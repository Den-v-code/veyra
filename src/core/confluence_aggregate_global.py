"""Fresh arbitrary same-endpoint history comparison for P1-C2."""

from __future__ import annotations

from dataclasses import replace
import logging

from .confluence_aggregate_digest import cell_artifact_digest
from .confluence_aggregate_history import ReplayedHistory, replay_history
from .confluence_aggregate_types import GlobalHistory2CellArtifact, GlobalPathPairRequirement
from .confluence_digest import cell_trace_digest, response_row_digest, trace_digest
from .confluence_runtime import _outcome_name, _payload, _status
from .confluence_types import (
    ConfluenceObstruction, ConfluenceStatus, FiniteDiagramSource,
    TransportResponseRow,
)
from .observer_core_codec import decode_observer
from .observer_core_semantics import echo
from .positive_ontology_types import ObserverDoctrine, OntologyStage

logger = logging.getLogger(__name__)


def global_history_2cell(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    requirement: GlobalPathPairRequirement,
) -> GlobalHistory2CellArtifact:
    """Derive a full direct-echo 2-cell without C1 fork-shape coercion."""
    logger.debug("global_history_2cell entry")
    left = replay_history(requirement.left, doctrine, diagram)
    right = replay_history(requirement.right, doctrine, diagram)
    mismatches, openings = _persistence_obstructions(diagram, left, "left-history")
    right_bad, right_open = _persistence_obstructions(diagram, right, "right-history")
    mismatches.extend(right_bad)
    openings.extend(right_open)
    rows = tuple(
        _response_row(
            requirement.requirement_digest, point_index,
            point.left_index, point.right_index,
            left.stages[point.left_index], right.stages[point.right_index], observer_id,
        )
        for point_index, point in enumerate(requirement.alignment)
        for observer_id in requirement.transport.observer_ids
    )
    for row in rows:
        if row.status is ConfluenceStatus.REFUTED:
            mismatches.append(_row_obstruction(row))
        elif row.status is ConfluenceStatus.OPEN:
            openings.append(_row_obstruction(row))
    status = ConfluenceStatus.REFUTED if mismatches else (
        ConfluenceStatus.OPEN if openings else ConfluenceStatus.ESTABLISHED
    )
    first = mismatches[0] if mismatches else (openings[0] if openings else None)
    charged = (
        len(left.edge_ids) + len(right.edge_ids)
        + len(requirement.alignment) * len(requirement.transport.observer_ids)
    )
    left_trace = trace_digest("global-left", left.history_digest, rows)
    right_trace = trace_digest("global-right", right.history_digest, rows)
    combined = cell_trace_digest(left_trace, right_trace, requirement.requirement_digest)
    provisional = GlobalHistory2CellArtifact(
        doctrine.fingerprint, diagram.source_digest, requirement.requirement_digest,
        left.history_digest, right.history_digest, left.stage_commitments,
        right.stage_commitments, requirement.alignment,
        requirement.transport.observer_ids, requirement.transport.mode,
        requirement.transport.transport_digest, rows, left_trace, right_trace,
        combined, first, charged, status, "",
    )
    result = replace(provisional, artifact_digest=cell_artifact_digest(provisional))
    logger.debug("global_history_2cell exit status=%s rows=%d", status.value, len(rows))
    return result


def _persistence_obstructions(
    diagram: FiniteDiagramSource, history: ReplayedHistory, lane: str,
) -> tuple[list[ConfluenceObstruction], list[ConfluenceObstruction]]:
    logger.debug("global persistence entry lane=%s edges=%d", lane, len(history.edge_ids))
    edges = {item.edge_id: item for item in diagram.edges}
    stages = {item.stage_id: item for item in diagram.stages}
    mismatches: list[ConfluenceObstruction] = []
    openings: list[ConfluenceObstruction] = []
    for occurrence, edge_id in enumerate(history.edge_ids, start=1):
        edge = edges[edge_id]
        if not edge.preserved_observer_ids:
            openings.append(ConfluenceObstruction(lane, occurrence, "none", "not-queried"))
            continue
        upper = {item.observer_id: item for item in stages[edge.upper_stage_id].observers}
        for observer_id in edge.preserved_observer_ids:
            outcome = echo(
                decode_observer(upper[observer_id].canonical),
                stages[edge.lower_stage_id].representative,
                stages[edge.upper_stage_id].representative,
            )
            status = _status(outcome)
            obstruction = ConfluenceObstruction(
                lane, occurrence, observer_id, _outcome_name(outcome),
            )
            if status is ConfluenceStatus.REFUTED:
                mismatches.append(obstruction)
            elif status is ConfluenceStatus.OPEN:
                openings.append(obstruction)
    logger.debug("global persistence exit lane=%s bad=%d open=%d", lane, len(mismatches), len(openings))
    return mismatches, openings


def _response_row(
    requirement_digest: str, point_index: int, left_index: int, right_index: int,
    left: OntologyStage, right: OntologyStage, observer_id: str,
) -> TransportResponseRow:
    logger.debug("global response row entry point=%d", point_index)
    left_map = {item.observer_id: item for item in left.observers}
    right_map = {item.observer_id: item for item in right.observers}
    if observer_id not in left_map or observer_id not in right_map:
        status = ConfluenceStatus.OPEN
        outcome_name, payload = "observer-unavailable", b'{"tag":"observer-unavailable"}'
    else:
        outcome = echo(
            decode_observer(left_map[observer_id].canonical),
            left.representative, right.representative,
        )
        status, outcome_name, payload = _status(outcome), _outcome_name(outcome), _payload(outcome)
    fields = (
        ("requirement", requirement_digest.encode()),
        ("point", point_index.to_bytes(8, "big")),
        ("left-index", left_index.to_bytes(8, "big")),
        ("right-index", right_index.to_bytes(8, "big")),
        ("left-stage", left.stage_id.encode()), ("right-stage", right.stage_id.encode()),
        ("observer", observer_id.encode()), ("status", status.value.encode()),
        ("outcome", outcome_name.encode()), ("payload", payload),
    )
    result = TransportResponseRow(
        point_index, left_index, right_index, left.stage_id, right.stage_id,
        observer_id, status, outcome_name, payload, response_row_digest(fields),
    )
    logger.debug("global response row exit status=%s", status.value)
    return result


def _row_obstruction(row: TransportResponseRow) -> ConfluenceObstruction:
    logger.debug("global row obstruction entry point=%d", row.point_index)
    result = ConfluenceObstruction(
        "transport-alignment", row.point_index, row.observer_id, row.outcome,
    )
    logger.debug("global row obstruction exit")
    return result
