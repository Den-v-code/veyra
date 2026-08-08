"""Atomic whole-catalog resource accounting for P1-C2."""

from __future__ import annotations

import logging

from .confluence_aggregate_digest import catalog_canonical_bytes, tagged_digest
from .confluence_aggregate_history import replay_history
from .confluence_aggregate_types import (
    AggregateFailedBound, AggregateResultStatus, C2_NONCLAIMS,
    ConfluenceAggregateResourceLimit, FiniteConfluenceCatalogSource,
)
from .confluence_preflight import ConfluenceValidationError
from .confluence_types import FiniteDiagramSource
from .positive_ontology_types import ObserverDoctrine

logger = logging.getLogger(__name__)
MAX_TOTAL_CHECKS = 16_384
MAX_CANONICAL_BYTES = 2 * 1024 * 1024


def _reject(reason: str) -> None:
    logger.error("aggregate preflight rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


def aggregate_run_digest(catalog: FiniteConfluenceCatalogSource) -> str:
    """Bind one deterministic replay run to exact source and policy identities."""
    logger.debug("aggregate_run_digest entry")
    result = tagged_digest(
        "veyra.p1c2.run.v1", ("doctrine", catalog.doctrine_fingerprint),
        ("diagram", catalog.diagram_digest), ("catalog", catalog.catalog_digest),
        ("policy", catalog.policy.policy_digest),
    )
    logger.debug("aggregate_run_digest exit")
    return result


def total_catalog_charge(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    catalog: FiniteConfluenceCatalogSource,
) -> int:
    """Charge each history edge once plus each aligned observer comparison."""
    logger.debug("total_catalog_charge entry")
    paths = {item.path_id: item for item in diagram.paths}
    edges = {item.edge_id: item for item in diagram.edges}
    total = 0
    for item in catalog.local_requirements:
        plan = item.plan
        selected = (
            plan.left_branch_path_id, plan.right_branch_path_id,
            plan.left_join_path_id, plan.right_join_path_id,
        )
        if any(path_id is None for path_id in selected):
            _reject("local-requirement-missing-joined-history")
        local_edges = tuple(
            edge_id for path_id in selected if path_id is not None
            for edge_id in paths[path_id].edge_ids
        )
        total += len(local_edges)
        total += len(plan.alignment) * len(item.transport.observer_ids)
        c1_charge = sum(
            max(1, len(edges[edge_id].preserved_observer_ids))
            for edge_id in local_edges
        ) + len(plan.alignment) * len(item.transport.observer_ids)
        if c1_charge > 4096:
            _reject("confluence-aggregate-local-c1-check-limit")
    for item in catalog.global_requirements:
        left = replay_history(item.left, doctrine, diagram)
        right = replay_history(item.right, doctrine, diagram)
        total += len(left.edge_ids) + len(right.edge_ids)
        total += len(item.alignment) * len(item.transport.observer_ids)
    if total > MAX_TOTAL_CHECKS:
        _reject("confluence-aggregate-hard-check-limit")
    logger.debug("total_catalog_charge exit checks=%d", total)
    return total


def aggregate_preflight(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    catalog: FiniteConfluenceCatalogSource,
) -> tuple[int, int, str, ConfluenceAggregateResourceLimit | None]:
    """Apply canonical-byte then total-check policy before any observation."""
    logger.debug("aggregate_preflight entry")
    encoded_bytes = len(catalog_canonical_bytes(catalog))
    if encoded_bytes > MAX_CANONICAL_BYTES:
        _reject("confluence-aggregate-hard-byte-limit")
    run = aggregate_run_digest(catalog)
    # Hard semantic validity is prior to every operational policy outcome.
    # Only a hard-valid request participates in the byte-then-check policy order.
    charged = total_catalog_charge(doctrine, diagram, catalog)
    if encoded_bytes > catalog.policy.max_bytes:
        refusal = _refusal(
            catalog, run, AggregateFailedBound.CANONICAL_BYTES,
            encoded_bytes, catalog.policy.max_bytes,
        )
        logger.debug("aggregate_preflight exit refused bound=canonical-bytes")
        return charged, encoded_bytes, run, refusal
    if charged <= catalog.policy.max_checks:
        logger.debug("aggregate_preflight exit accepted checks=%d bytes=%d", charged, encoded_bytes)
        return charged, encoded_bytes, run, None
    refusal = _refusal(
        catalog, run, AggregateFailedBound.TOTAL_CHECKS,
        charged, catalog.policy.max_checks,
    )
    logger.debug("aggregate_preflight exit refused bound=total-checks")
    return charged, encoded_bytes, run, refusal


def _refusal(
    catalog: FiniteConfluenceCatalogSource, run: str,
    failed: AggregateFailedBound, required: int, allowed: int,
) -> ConfluenceAggregateResourceLimit:
    """Construct a typed no-partial-evidence refusal after one failed bound."""
    logger.debug("aggregate refusal entry bound=%s", failed.value)
    refusal_digest = tagged_digest(
        "veyra.p1c2.resource-limit.v1", ("doctrine", catalog.doctrine_fingerprint),
        ("diagram", catalog.diagram_digest), ("catalog", catalog.catalog_digest),
        ("policy", catalog.policy.policy_digest), ("run", run),
        ("failed", failed.value), ("required", required), ("allowed", allowed),
    )
    refusal = ConfluenceAggregateResourceLimit(
        AggregateResultStatus.RESOURCE_LIMIT, catalog.doctrine_fingerprint,
        catalog.diagram_digest, catalog.catalog_digest, catalog.policy.policy_digest,
        run, failed, required, allowed, C2_NONCLAIMS, refusal_digest,
    )
    logger.debug("aggregate refusal exit bound=%s", failed.value)
    return refusal
