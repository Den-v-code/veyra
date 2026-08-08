"""Tagged commitments and canonical catalog bytes for P1-C2."""

from __future__ import annotations

import json
import logging

from .confluence_digest import _digest
from .confluence_types import ForkConfluenceJudgment, TransportResponseRow
from .confluence_aggregate_types import (
    ConfluenceAggregatePolicy, ConfluenceRequirementRow, DeclaredHistory,
    FiniteConfluenceCatalogSource, GlobalHistory2CellArtifact,
    GlobalPathPairRequirement, IdentityHistory, LocalCriticalForkRequirement,
)

logger = logging.getLogger(__name__)


def tagged_digest(domain: str, *fields: tuple[str, str | bytes | int]) -> str:
    """Hash exact tagged primitive fields."""
    logger.debug("tagged_digest entry domain=%s fields=%d", domain, len(fields))
    encoded = tuple(
        (tag, value if type(value) is bytes else (
            value.to_bytes(8, "big") if type(value) is int else value.encode()
        )) for tag, value in fields
    )
    result = _digest(domain, encoded)
    logger.debug("tagged_digest exit domain=%s", domain)
    return result


def sequence_digest(domain: str, fields: tuple[tuple[str, str], ...]) -> str:
    """Hash an ordered count-framed string sequence."""
    logger.debug("sequence_digest entry domain=%s count=%d", domain, len(fields))
    packed = [("count", len(fields).to_bytes(8, "big"))]
    packed.extend((f"{tag}-{i}", value.encode()) for i, (tag, value) in enumerate(fields))
    result = _digest(domain, tuple(packed))
    logger.debug("sequence_digest exit domain=%s", domain)
    return result


def c1_judgment_digest(value: ForkConfluenceJudgment) -> str:
    """Commit the freshly derived C1 judgment without accepting it as input."""
    logger.debug("c1_judgment_digest entry")
    cell = "none" if value.transport_cell is None else value.transport_cell.trace_digest
    obstruction = "none" if value.first_obstruction is None else tagged_digest(
        "veyra.p1c2.obstruction.v1",
        ("lane", value.first_obstruction.lane),
        ("occurrence", value.first_obstruction.occurrence),
        ("observer", value.first_obstruction.observer_id),
        ("outcome", value.first_obstruction.outcome),
    )
    result = tagged_digest(
        "veyra.p1c2.c1-judgment.v1", ("plan-id", value.plan_id),
        ("plan", value.plan_digest), ("status", value.status.value),
        ("cell", cell), ("obstruction", obstruction),
        ("charged", value.charged_checks),
    )
    logger.debug("c1_judgment_digest exit")
    return result


def response_commitment(rows: tuple[TransportResponseRow, ...]) -> str:
    """Commit every ordered response-row digest."""
    logger.debug("response_commitment entry rows=%d", len(rows))
    result = sequence_digest(
        "veyra.p1c2.responses.v1", tuple(("row", item.row_digest) for item in rows),
    )
    logger.debug("response_commitment exit")
    return result


def cell_artifact_digest(value: GlobalHistory2CellArtifact) -> str:
    """Commit one derived global-history 2-cell."""
    logger.debug("cell_artifact_digest entry")
    obstruction = "none" if value.first_obstruction is None else tagged_digest(
        "veyra.p1c2.obstruction.v1",
        ("lane", value.first_obstruction.lane),
        ("occurrence", value.first_obstruction.occurrence),
        ("observer", value.first_obstruction.observer_id),
        ("outcome", value.first_obstruction.outcome),
    )
    result = tagged_digest(
        "veyra.p1c2.global-cell.v1", ("doctrine", value.doctrine_fingerprint),
        ("diagram", value.diagram_digest), ("requirement", value.requirement_digest),
        ("left-history", value.left_history_digest),
        ("right-history", value.right_history_digest),
        ("transport", value.transport_digest), ("trace", value.trace_digest),
        ("responses", response_commitment(value.response_rows)),
        ("obstruction", obstruction), ("charged", value.charged_checks),
        ("status", value.status.value), ("scope", value.scope),
    )
    logger.debug("cell_artifact_digest exit")
    return result


def row_digest(value: ConfluenceRequirementRow) -> str:
    """Commit one exact aggregate row."""
    logger.debug("aggregate row_digest entry")
    kind, requirement_id, requirement_digest = value.key
    obstruction = "none" if value.first_obstruction is None else tagged_digest(
        "veyra.p1c2.obstruction.v1",
        ("lane", value.first_obstruction.lane),
        ("occurrence", value.first_obstruction.occurrence),
        ("observer", value.first_obstruction.observer_id),
        ("outcome", value.first_obstruction.outcome),
    )
    fields = (
        ("kind", kind.value), ("id", requirement_id),
        ("requirement", requirement_digest), ("plan", value.plan_digest or "none"),
        ("left", value.left_history_digest or "none"),
        ("right", value.right_history_digest or "none"),
        ("transport", value.transport_digest),
        ("local", value.local_judgment_digest or "none"),
        ("global", value.global_history_cell_digest or "none"),
        ("obstruction", obstruction), ("charged", value.charged_checks),
        ("status", value.status.value),
    )
    result = tagged_digest("veyra.p1c2.requirement-row.v1", *fields)
    logger.debug("aggregate row_digest exit")
    return result


def catalog_canonical_bytes(value: FiniteConfluenceCatalogSource) -> bytes:
    """Encode every catalog payload in deterministic semantic order."""
    logger.debug("catalog_canonical_bytes entry")
    payload = {
        "version": value.version, "scope": value.scope,
        "doctrine": value.doctrine_fingerprint, "diagram": value.diagram_digest,
        "policy": _policy_json(value.policy),
        "local": [_local_json(item) for item in value.local_requirements],
        "global": [_global_json(item) for item in value.global_requirements],
    }
    result = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    logger.debug("catalog_canonical_bytes exit bytes=%d", len(result))
    return result


def _policy_json(value: ConfluenceAggregatePolicy) -> dict[str, object]:
    logger.debug("aggregate policy json entry")
    try:
        result = {"version": value.version, "max_checks": value.max_checks,
                  "max_bytes": value.max_bytes, "digest": value.policy_digest}
    except Exception:
        logger.error("aggregate policy json error")
        raise
    logger.debug("aggregate policy json exit")
    return result


def _local_json(value: LocalCriticalForkRequirement) -> dict[str, object]:
    logger.debug("aggregate local json entry")
    try:
        plan = value.plan
        result = {
            "id": value.requirement_id, "digest": value.requirement_digest,
            "plan": {
                "id": plan.plan_id, "digest": plan.plan_digest,
                "diagram": plan.diagram_digest, "fork": plan.fork_stage_commitment,
                "branches": [plan.left_branch_path_id, plan.right_branch_path_id],
                "joins": [plan.left_join_path_id, plan.right_join_path_id],
                "join": plan.join_stage_commitment,
                "alignment": [[x.left_index, x.right_index] for x in plan.alignment],
                "transport": plan.transport_digest, "version": plan.version,
                "scope": plan.scope,
            },
            "transport": _transport_json(value.transport),
        }
    except Exception:
        logger.error("aggregate local json error")
        raise
    logger.debug("aggregate local json exit")
    return result


def _history_json(value: IdentityHistory | DeclaredHistory) -> dict[str, object]:
    logger.debug("aggregate history json entry")
    try:
        if type(value) is IdentityHistory:
            result = {"kind": "identity", "version": value.version, "id": value.history_id,
                      "stage": value.stage_id, "stage_commitment": value.stage_commitment,
                      "digest": value.history_digest}
        else:
            result = {"kind": "declared", "version": value.version, "id": value.history_id,
                      "path": value.path_id, "path_commitment": value.path_commitment,
                      "start": value.start_stage_id, "end": value.end_stage_id,
                      "digest": value.history_digest}
    except Exception:
        logger.error("aggregate history json error")
        raise
    logger.debug("aggregate history json exit")
    return result


def _transport_json(value: object) -> dict[str, object]:
    logger.debug("aggregate transport json entry")
    try:
        result = {"observers": list(value.observer_ids), "mode": value.mode.value,
                  "scope": value.scope, "digest": value.transport_digest}
    except Exception:
        logger.error("aggregate transport json error")
        raise
    logger.debug("aggregate transport json exit")
    return result


def _global_json(value: GlobalPathPairRequirement) -> dict[str, object]:
    logger.debug("aggregate global json entry")
    try:
        result = {"id": value.requirement_id, "digest": value.requirement_digest,
                  "left": _history_json(value.left), "right": _history_json(value.right),
                  "alignment": [[x.left_index, x.right_index] for x in value.alignment],
                  "transport": _transport_json(value.transport)}
    except Exception:
        logger.error("aggregate global json error")
        raise
    logger.debug("aggregate global json exit")
    return result
