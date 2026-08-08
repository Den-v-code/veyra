"""Exact zero/nonzero history construction and replay for P1-C2."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .confluence_aggregate_digest import tagged_digest
from .confluence_aggregate_types import DeclaredHistory, HistoryRef, IdentityHistory
from .confluence_path import replay_diagram_path
from .confluence_preflight import ConfluenceValidationError
from .confluence_types import FiniteDiagramSource
from .confluence_validation import (
    _hex_digest, _identifier, snapshot_confluence_doctrine,
    snapshot_finite_diagram_source,
)
from .positive_ontology_doctrine import stage_commitment
from .positive_ontology_types import ObserverDoctrine, OntologyStage

logger = logging.getLogger(__name__)
HISTORY_VERSION = "p1-c2-history-v1"


@dataclass(frozen=True)
class ReplayedHistory:
    history_id: str
    history_digest: str
    edge_ids: tuple[str, ...]
    stages: tuple[OntologyStage, ...]
    stage_commitments: tuple[str, ...]


def _reject(reason: str) -> None:
    logger.error("aggregate history rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


def identity_history(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    history_id: str, stage_id: str,
) -> IdentityHistory:
    """Construct the only zero-edge history from one exact diagram stage."""
    logger.debug("identity_history entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    history_id = _identifier(history_id, "history-id")
    stage_id = _identifier(stage_id, "identity-stage-id")
    stages = {item.stage_id: item for item in diagram.stages}
    if stage_id not in stages:
        _reject("unknown-identity-stage")
    commitment = stage_commitment(stages[stage_id])
    digest = tagged_digest(
        "veyra.p1c2.identity-history.v1", ("version", HISTORY_VERSION),
        ("history-id", history_id), ("diagram", diagram.source_digest),
        ("stage-id", stage_id), ("stage", commitment),
    )
    result = IdentityHistory(HISTORY_VERSION, history_id, stage_id, commitment, digest)
    logger.debug("identity_history exit")
    return result


def declared_history(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    history_id: str, path_id: str,
) -> DeclaredHistory:
    """Construct one exact nonempty history from a declared C1 path."""
    logger.debug("declared_history entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    history_id = _identifier(history_id, "history-id")
    path_id = _identifier(path_id, "history-path-id")
    paths = {item.path_id: item for item in diagram.paths}
    commitments = dict(zip(
        (item.path_id for item in diagram.paths), diagram.path_commitments, strict=True,
    ))
    if path_id not in paths:
        _reject("unknown-history-path")
    path = paths[path_id]
    digest = tagged_digest(
        "veyra.p1c2.declared-history.v1", ("version", HISTORY_VERSION),
        ("history-id", history_id), ("diagram", diagram.source_digest),
        ("path-id", path_id), ("path", commitments[path_id]),
        ("start", path.start_stage_id), ("end", path.end_stage_id),
    )
    result = DeclaredHistory(
        HISTORY_VERSION, history_id, path_id, commitments[path_id],
        path.start_stage_id, path.end_stage_id, digest,
    )
    logger.debug("declared_history exit")
    return result


def snapshot_history(
    value: HistoryRef, doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
) -> HistoryRef:
    """Rebuild an exact closed history variant and reject relabeling."""
    logger.debug("snapshot_history entry")
    if type(value) is IdentityHistory:
        try:
            result = identity_history(doctrine, diagram, value.history_id, value.stage_id)
            supplied = (value.version, value.stage_commitment, value.history_digest)
        except AttributeError:
            _reject("identity-history-missing-fields")
        if (
            any(type(item) is not str for item in supplied)
            or supplied != (result.version, result.stage_commitment, result.history_digest)
        ):
            _reject("identity-history-drift")
    elif type(value) is DeclaredHistory:
        try:
            result = declared_history(doctrine, diagram, value.history_id, value.path_id)
            supplied = (
                value.version, value.path_commitment, value.start_stage_id,
                value.end_stage_id, value.history_digest,
            )
        except AttributeError:
            _reject("declared-history-missing-fields")
        if (
            any(type(item) is not str for item in supplied)
            or supplied != (
                result.version, result.path_commitment, result.start_stage_id,
                result.end_stage_id, result.history_digest,
            )
        ):
            _reject("declared-history-drift")
    else:
        _reject("history-ref-must-be-exact-closed-variant")
    logger.debug("snapshot_history exit kind=%s", type(result).__name__)
    return result


def replay_history(
    value: HistoryRef, doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
) -> ReplayedHistory:
    """Freshly replay an identity or a nonempty declared path."""
    logger.debug("replay_history entry")
    value = snapshot_history(value, doctrine, diagram)
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    if type(value) is IdentityHistory:
        stage = next(item for item in diagram.stages if item.stage_id == value.stage_id)
        result = ReplayedHistory(
            value.history_id, value.history_digest, (), (stage,),
            (value.stage_commitment,),
        )
    else:
        replay = replay_diagram_path(doctrine, diagram, value.path_id)
        result = ReplayedHistory(
            value.history_id, value.history_digest, replay.edge_ids,
            replay.stages, replay.stage_commitments,
        )
    logger.debug("replay_history exit edges=%d stages=%d", len(result.edge_ids), len(result.stages))
    return result


def history_digest_field(value: object, field: str) -> str:
    """Expose strict digest validation for result validators."""
    logger.debug("history_digest_field entry field=%s", field)
    result = _hex_digest(value, field)
    logger.debug("history_digest_field exit field=%s", field)
    return result
