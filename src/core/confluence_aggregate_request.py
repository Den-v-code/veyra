"""Exact requirement, policy, and catalog snapshots for P1-C2."""

from __future__ import annotations

import logging

from .confluence_aggregate_digest import (
    catalog_canonical_bytes, sequence_digest, tagged_digest,
)
from .confluence_aggregate_history import replay_history, snapshot_history
from .confluence_aggregate_types import (
    ConfluenceAggregatePolicy, FiniteConfluenceCatalogSource,
    GlobalPathPairRequirement, LocalCriticalForkRequirement, RequirementKind,
)
from .confluence_plan import (
    _snapshot_alignment, snapshot_direct_echo_transport, snapshot_fork_join_plan,
)
from .confluence_preflight import ConfluenceValidationError
from .confluence_types import AlignmentPoint, DirectEchoTransport, FiniteDiagramSource, ForkJoinPlan
from .confluence_validation import (
    _hex_digest, _identifier, snapshot_confluence_doctrine,
    snapshot_finite_diagram_source,
)
from .positive_ontology_types import ObserverDoctrine

logger = logging.getLogger(__name__)
CATALOG_VERSION = "p1-c2-v1"
CATALOG_SCOPE = "declared-finite-catalog-not-generated-path-universe"
POLICY_VERSION = "p1-c2-policy-v1"
MAX_CANONICAL_BYTES = 2 * 1024 * 1024


def _reject(reason: str) -> None:
    logger.error("aggregate request rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


def confluence_aggregate_policy(
    max_checks: int = 4096, max_bytes: int = MAX_CANONICAL_BYTES,
) -> ConfluenceAggregatePolicy:
    """Construct the bounded operational policy independently of catalog identity."""
    logger.debug("confluence_aggregate_policy entry")
    if (
        type(max_checks) is not int or not 1 <= max_checks <= 4096
        or type(max_bytes) is not int or not 1 <= max_bytes <= MAX_CANONICAL_BYTES
    ):
        _reject("invalid-confluence-aggregate-policy")
    digest = tagged_digest(
        "veyra.p1c2.policy.v1", ("version", POLICY_VERSION),
        ("max-checks", max_checks), ("max-bytes", max_bytes),
    )
    result = ConfluenceAggregatePolicy(POLICY_VERSION, max_checks, max_bytes, digest)
    logger.debug("confluence_aggregate_policy exit")
    return result


def snapshot_policy(value: ConfluenceAggregatePolicy) -> ConfluenceAggregatePolicy:
    """Rebuild one exact policy and reject Boolean/int or digest drift."""
    logger.debug("snapshot_policy entry")
    if type(value) is not ConfluenceAggregatePolicy:
        _reject("confluence-aggregate-policy-must-be-exact")
    try:
        result = confluence_aggregate_policy(value.max_checks, value.max_bytes)
        supplied = (value.version, value.policy_digest)
    except AttributeError:
        _reject("confluence-aggregate-policy-missing-fields")
    if any(type(item) is not str for item in supplied) or supplied != (
        result.version, result.policy_digest,
    ):
        _reject("confluence-aggregate-policy-drift")
    logger.debug("snapshot_policy exit")
    return result


def local_critical_fork_requirement(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource, requirement_id: str,
    plan: ForkJoinPlan, transport: DirectEchoTransport,
) -> LocalCriticalForkRequirement:
    """Bind one genuinely one-edge C1 critical fork from raw inputs."""
    logger.debug("local_critical_fork_requirement entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    transport = snapshot_direct_echo_transport(transport, doctrine)
    plan = snapshot_fork_join_plan(plan, diagram, transport, doctrine)
    requirement_id = _identifier(requirement_id, "confluence-requirement-id")
    paths = {item.path_id: item for item in diagram.paths}
    left, right = paths[plan.left_branch_path_id], paths[plan.right_branch_path_id]
    if len(left.edge_ids) != 1 or len(right.edge_ids) != 1:
        _reject("local-critical-branch-must-have-one-edge")
    if left.edge_ids[0] == right.edge_ids[0]:
        _reject("local-critical-edges-must-differ")
    if plan.left_join_path_id is None or plan.right_join_path_id is None:
        _reject("local-critical-fork-requires-nonempty-joins")
    digest = tagged_digest(
        "veyra.p1c2.local-requirement.v1", ("id", requirement_id),
        ("diagram", diagram.source_digest), ("plan", plan.plan_digest),
        ("transport", transport.transport_digest),
    )
    result = LocalCriticalForkRequirement(requirement_id, plan, transport, digest)
    logger.debug("local_critical_fork_requirement exit")
    return result


def global_path_pair_requirement(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource, requirement_id: str,
    left: object, right: object, alignment: tuple[AlignmentPoint, ...],
    transport: DirectEchoTransport,
) -> GlobalPathPairRequirement:
    """Bind two distinct arbitrary same-endpoint declared histories."""
    logger.debug("global_path_pair_requirement entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    requirement_id = _identifier(requirement_id, "confluence-requirement-id")
    left = snapshot_history(left, doctrine, diagram)  # type: ignore[arg-type]
    right = snapshot_history(right, doctrine, diagram)  # type: ignore[arg-type]
    transport = snapshot_direct_echo_transport(transport, doctrine)
    left_replay = replay_history(left, doctrine, diagram)
    right_replay = replay_history(right, doctrine, diagram)
    if left.history_id == right.history_id:
        _reject("global-histories-require-distinct-ids")
    if type(left) is type(right):
        same = (
            left.stage_id == right.stage_id if hasattr(left, "stage_id")
            else left.path_id == right.path_id
        )
        if same:
            _reject("global-histories-identical-under-distinct-ids")
    if (
        left_replay.stage_commitments[0] != right_replay.stage_commitments[0]
        or left_replay.stage_commitments[-1] != right_replay.stage_commitments[-1]
    ):
        _reject("global-history-endpoint-mismatch")
    alignment = _global_alignment(
        alignment, len(left_replay.stages), len(right_replay.stages),
    )
    digest = tagged_digest(
        "veyra.p1c2.global-requirement.v1", ("id", requirement_id),
        ("diagram", diagram.source_digest), ("left", left.history_digest),
        ("right", right.history_digest),
        ("alignment", _alignment_digest(alignment)),
        ("transport", transport.transport_digest),
    )
    result = GlobalPathPairRequirement(
        requirement_id, left, right, alignment, transport, digest,
    )
    logger.debug("global_path_pair_requirement exit")
    return result


def _global_alignment(
    value: tuple[AlignmentPoint, ...], left_stages: int, right_stages: int,
) -> tuple[AlignmentPoint, ...]:
    logger.debug("global alignment entry")
    rows = _snapshot_alignment(value)
    if (
        not rows or rows[0] != AlignmentPoint(0, 0)
        or rows[-1] != AlignmentPoint(left_stages - 1, right_stages - 1)
    ):
        _reject("global-alignment-endpoint-drift")
    for previous, current in zip(rows, rows[1:]):
        delta = (
            current.left_index - previous.left_index,
            current.right_index - previous.right_index,
        )
        if delta not in {(1, 0), (0, 1), (1, 1)}:
            _reject("global-alignment-not-full-monotone")
    logger.debug("global alignment exit points=%d", len(rows))
    return rows


def _alignment_digest(value: tuple[AlignmentPoint, ...]) -> str:
    logger.debug("aggregate alignment digest entry points=%d", len(value))
    try:
        fields = tuple(("point", f"{x.left_index}:{x.right_index}") for x in value)
        result = sequence_digest("veyra.p1c2.alignment.v1", fields)
    except Exception:
        logger.error("aggregate alignment digest error")
        raise
    logger.debug("aggregate alignment digest exit")
    return result


def finite_confluence_catalog(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    local: tuple[LocalCriticalForkRequirement, ...],
    global_: tuple[GlobalPathPairRequirement, ...],
    policy: ConfluenceAggregatePolicy,
) -> FiniteConfluenceCatalogSource:
    """Build the complete immutable ordered C2 requirement catalog."""
    logger.debug("finite_confluence_catalog entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    policy = snapshot_policy(policy)
    if type(local) is not tuple or not 1 <= len(local) <= 64:
        _reject("invalid-local-requirement-catalog")
    if type(global_) is not tuple or not 1 <= len(global_) <= 128:
        _reject("invalid-global-requirement-catalog")
    locals_ = tuple(_snapshot_local(x, doctrine, diagram) for x in local)
    globals_ = tuple(_snapshot_global(x, doctrine, diagram) for x in global_)
    ids = tuple(x.requirement_id for x in (*locals_, *globals_))
    if len(set(ids)) != len(ids):
        _reject("duplicate-cross-catalog-requirement-id")
    local_keys = tuple(
        (RequirementKind.LOCAL, x.requirement_id, x.requirement_digest) for x in locals_
    )
    global_keys = tuple(
        (RequirementKind.GLOBAL, x.requirement_id, x.requirement_digest) for x in globals_
    )
    digest = _catalog_digest(
        doctrine.fingerprint, diagram.source_digest, local_keys, global_keys, policy,
    )
    result = FiniteConfluenceCatalogSource(
        doctrine.fingerprint, diagram.source_digest, locals_, globals_,
        local_keys, global_keys, policy, digest,
    )
    if len(catalog_canonical_bytes(result)) > MAX_CANONICAL_BYTES:
        _reject("confluence-catalog-hard-byte-limit")
    logger.debug("finite_confluence_catalog exit local=%d global=%d", len(locals_), len(globals_))
    return result


def _snapshot_local(value, doctrine, diagram) -> LocalCriticalForkRequirement:
    logger.debug("aggregate snapshot local entry")
    try:
        if type(value) is not LocalCriticalForkRequirement:
            _reject("local-requirement-must-be-exact")
        result = local_critical_fork_requirement(
            doctrine, diagram, value.requirement_id, value.plan, value.transport,
        )
        if _hex_digest(value.requirement_digest, "local-requirement-digest") != result.requirement_digest:
            _reject("local-requirement-drift")
    except Exception:
        logger.error("aggregate snapshot local error")
        raise
    logger.debug("aggregate snapshot local exit")
    return result


def _snapshot_global(value, doctrine, diagram) -> GlobalPathPairRequirement:
    logger.debug("aggregate snapshot global entry")
    try:
        if type(value) is not GlobalPathPairRequirement:
            _reject("global-requirement-must-be-exact")
        result = global_path_pair_requirement(
            doctrine, diagram, value.requirement_id, value.left, value.right,
            value.alignment, value.transport,
        )
        if _hex_digest(value.requirement_digest, "global-requirement-digest") != result.requirement_digest:
            _reject("global-requirement-drift")
    except Exception:
        logger.error("aggregate snapshot global error")
        raise
    logger.debug("aggregate snapshot global exit")
    return result


def _catalog_digest(doctrine, diagram, local_keys, global_keys, policy) -> str:
    logger.debug("aggregate catalog digest entry")
    try:
        key_rows = tuple(
            ("key", f"{kind.value}\0{identifier}\0{digest}")
            for kind, identifier, digest in (*local_keys, *global_keys)
        )
        keys = sequence_digest("veyra.p1c2.catalog-keys.v1", key_rows)
        result = tagged_digest(
            "veyra.p1c2.catalog.v1", ("version", CATALOG_VERSION),
            ("scope", CATALOG_SCOPE), ("doctrine", doctrine),
            ("diagram", diagram), ("keys", keys), ("policy", policy.policy_digest),
        )
    except Exception:
        logger.error("aggregate catalog digest error")
        raise
    logger.debug("aggregate catalog digest exit")
    return result
