"""Preflight-first declared finite confluence aggregation for P1-C2."""

from __future__ import annotations

from dataclasses import replace
import logging

from .confluence_aggregate_catalog_validation import snapshot_finite_confluence_catalog
from .confluence_aggregate_digest import (
    c1_judgment_digest, row_digest, sequence_digest, tagged_digest,
)
from .confluence_aggregate_global import global_history_2cell
from .confluence_aggregate_history import replay_history
from .confluence_aggregate_preflight import aggregate_preflight
from .confluence_aggregate_types import (
    AggregateCoverageStatus, C2_NONCLAIMS, ConfluenceRequirementRow,
    FiniteConfluenceAggregate, FiniteConfluenceCatalogSource,
    FiniteConfluenceResult, GlobalDeclaredFiniteStatus, LocalFiniteStatus,
    RequirementKind,
)
from .confluence_runtime import fork_confluence_judgment
from .confluence_types import ConfluenceStatus, FiniteDiagramSource
from .confluence_validation import (
    snapshot_confluence_doctrine, snapshot_finite_diagram_source,
)
from .positive_ontology_types import ObserverDoctrine

logger = logging.getLogger(__name__)


def finite_confluence_aggregate(
    raw_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_catalog: FiniteConfluenceCatalogSource,
) -> FiniteConfluenceResult:
    """Replay every exact key only after atomic whole-catalog preflight."""
    logger.debug("finite_confluence_aggregate entry")
    doctrine = snapshot_confluence_doctrine(raw_doctrine)
    diagram = snapshot_finite_diagram_source(raw_diagram, doctrine)
    catalog = snapshot_finite_confluence_catalog(raw_catalog, doctrine, diagram)
    charged, _, run_digest, refusal = aggregate_preflight(doctrine, diagram, catalog)
    if refusal is not None:
        logger.debug("finite_confluence_aggregate exit resource-limit")
        return refusal
    local_rows = tuple(_local_row(doctrine, diagram, item) for item in catalog.local_requirements)
    global_rows = tuple(_global_row(doctrine, diagram, item) for item in catalog.global_requirements)
    rows = (*local_rows, *global_rows)
    actual_keys = tuple(item.key for item in rows)
    expected = (*catalog.expected_local_keys, *catalog.expected_global_keys)
    if actual_keys != expected:
        logger.error("finite_confluence_aggregate internal coverage drift")
        raise RuntimeError("internal confluence aggregate coverage drift")
    local_status = _local_status(local_rows)
    global_status = _global_status(global_rows)
    first = next((item.first_obstruction for item in rows if item.first_obstruction is not None), None)
    provisional = FiniteConfluenceAggregate(
        doctrine.fingerprint, diagram.source_digest, catalog.catalog_digest,
        catalog.policy.policy_digest, run_digest, catalog.expected_local_keys,
        catalog.expected_global_keys, rows, local_status, global_status,
        AggregateCoverageStatus.COMPLETE, first, charged, C2_NONCLAIMS, "",
    )
    result = replace(provisional, aggregate_digest=_aggregate_digest(provisional))
    logger.debug(
        "finite_confluence_aggregate exit local=%s global=%s rows=%d",
        local_status.value, global_status.value, len(rows),
    )
    return result


def _local_row(doctrine, diagram, requirement) -> ConfluenceRequirementRow:
    logger.debug("aggregate local row entry id=%s", requirement.requirement_id)
    judgment = fork_confluence_judgment(
        doctrine, diagram, requirement.plan, requirement.transport,
    )
    paths = {item.path_id: item for item in diagram.paths}
    plan = requirement.plan
    edge_occurrences = sum(
        len(paths[path_id].edge_ids) for path_id in (
            plan.left_branch_path_id, plan.right_branch_path_id,
            plan.left_join_path_id, plan.right_join_path_id,
        ) if path_id is not None
    )
    charged = edge_occurrences + len(plan.alignment) * len(requirement.transport.observer_ids)
    provisional = ConfluenceRequirementRow(
        (RequirementKind.LOCAL, requirement.requirement_id, requirement.requirement_digest),
        plan.plan_digest, None, None, requirement.transport.transport_digest,
        c1_judgment_digest(judgment), None, judgment.first_obstruction,
        charged, judgment.status, "",
    )
    result = replace(provisional, row_digest=row_digest(provisional))
    logger.debug("aggregate local row exit status=%s", result.status.value)
    return result


def _global_row(doctrine, diagram, requirement) -> ConfluenceRequirementRow:
    logger.debug("aggregate global row entry id=%s", requirement.requirement_id)
    left = replay_history(requirement.left, doctrine, diagram)
    right = replay_history(requirement.right, doctrine, diagram)
    cell = global_history_2cell(doctrine, diagram, requirement)
    provisional = ConfluenceRequirementRow(
        (RequirementKind.GLOBAL, requirement.requirement_id, requirement.requirement_digest),
        None, left.history_digest, right.history_digest,
        requirement.transport.transport_digest, None, cell.artifact_digest,
        cell.first_obstruction, cell.charged_checks, cell.status, "",
    )
    result = replace(provisional, row_digest=row_digest(provisional))
    logger.debug("aggregate global row exit status=%s", result.status.value)
    return result


def _local_status(rows: tuple[ConfluenceRequirementRow, ...]) -> LocalFiniteStatus:
    logger.debug("aggregate local status entry rows=%d", len(rows))
    statuses = tuple(item.status for item in rows)
    result = LocalFiniteStatus.REFUTED if ConfluenceStatus.REFUTED in statuses else (
        LocalFiniteStatus.OPEN if ConfluenceStatus.OPEN in statuses
        else LocalFiniteStatus.CONFLUENT
    )
    logger.debug("aggregate local status exit status=%s", result.value)
    return result


def _global_status(rows: tuple[ConfluenceRequirementRow, ...]) -> GlobalDeclaredFiniteStatus:
    logger.debug("aggregate global status entry rows=%d", len(rows))
    statuses = tuple(item.status for item in rows)
    result = GlobalDeclaredFiniteStatus.REFUTED if ConfluenceStatus.REFUTED in statuses else (
        GlobalDeclaredFiniteStatus.OPEN if ConfluenceStatus.OPEN in statuses
        else GlobalDeclaredFiniteStatus.CONFLUENT
    )
    logger.debug("aggregate global status exit status=%s", result.value)
    return result


def _aggregate_digest(value: FiniteConfluenceAggregate) -> str:
    logger.debug("aggregate digest entry")
    rows = sequence_digest(
        "veyra.p1c2.aggregate-rows.v1", tuple(("row", item.row_digest) for item in value.rows),
    )
    result = tagged_digest(
        "veyra.p1c2.aggregate.v1", ("doctrine", value.doctrine_fingerprint),
        ("diagram", value.diagram_digest), ("catalog", value.catalog_digest),
        ("policy", value.policy_digest), ("run", value.run_digest),
        ("rows", rows), ("local", value.local_status.value),
        ("global", value.global_status.value), ("coverage", value.coverage.value),
        ("charge", value.total_charge),
    )
    logger.debug("aggregate digest exit")
    return result
