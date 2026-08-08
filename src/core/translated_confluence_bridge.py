"""Exact P0-to-P1-A observer and stage bridge for P1-C3."""

from __future__ import annotations

from hashlib import sha256
import logging

from .confluence_types import FiniteDiagramSource
from .confluence_validation import (
    ConfluenceValidationError, snapshot_confluence_doctrine,
    snapshot_finite_diagram_source,
)
from .observer_morphism_types import ObserverSourceBinding
from .observer_morphism_validation import (
    ObserverMorphismValidationError, snapshot_source_binding,
    snapshot_morphism_doctrine,
)
from .observer_relation_request import snapshot_stage_source
from .observer_relation_types import RelationEvaluationSource
from .observer_relation_validation import ObserverRelationValidationError
from .positive_ontology_doctrine import stage_commitment
from .positive_ontology_types import ObserverDoctrine
from .translated_confluence_digest import digest, frame, kind_bytes, recurrence_bytes, sequence
from .translated_confluence_bridge_validation import compare_bridge, shallow_bridge
from .translated_confluence_types import (
    ObserverProgramBridgeRow, P0P1AResponseBridgeSource, StageInputBridgeRow,
)
from .translated_confluence_validation import TranslatedConfluenceValidationError, reject

logger = logging.getLogger(__name__)
BRIDGE_VERSION = "p1-c3-bridge-v1"
BRIDGE_SCOPE = "exact-byte-kind-and-recurrence-source-bridge"


def _snapshot_sources(
    raw_p0_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_p1a_doctrine: ObserverDoctrine, raw_p1a_source: ObserverSourceBinding,
    raw_a2_stage_source: RelationEvaluationSource,
) -> tuple[ObserverDoctrine, FiniteDiagramSource, ObserverDoctrine, ObserverSourceBinding, RelationEvaluationSource]:
    """Capture every lower source while normalizing only validation failures."""
    logger.debug("c3 bridge snapshot_sources entry")
    try:
        p0 = snapshot_confluence_doctrine(raw_p0_doctrine)
        diagram = snapshot_finite_diagram_source(raw_diagram, p0)
        p1a = snapshot_morphism_doctrine(raw_p1a_doctrine)
        binding = snapshot_source_binding(raw_p1a_source, p1a)
        stages = snapshot_stage_source(raw_a2_stage_source, p1a, binding)
    except (ConfluenceValidationError, ObserverMorphismValidationError,
            ObserverRelationValidationError) as exc:
        logger.error("c3 bridge lower source rejected")
        raise TranslatedConfluenceValidationError("invalid-c3-bridge-source") from exc
    logger.debug("c3 bridge snapshot_sources exit")
    return p0, diagram, p1a, binding, stages


def _p0_membership(doctrine: ObserverDoctrine) -> str:
    """Commit the exact ordered P0 observer family used by the diagram."""
    logger.debug("c3 p0_membership entry")
    result = digest("p1-c3-p0-membership-v1", (
        ("doctrine", doctrine.fingerprint.encode()),
        ("ids", sequence("observer", tuple(row.observer_id for row in doctrine.observers))),
        ("programs", len(doctrine.observers).to_bytes(8, "big") + b"".join(
            frame("program", row.canonical) for row in doctrine.observers
        )),
    ))
    logger.debug("c3 p0_membership exit")
    return result


def _observer_rows(
    p0: ObserverDoctrine, p1a: ObserverDoctrine, binding: ObserverSourceBinding,
) -> tuple[ObserverProgramBridgeRow, ...]:
    """Infer only unique byte-identical and kind-identical observer mappings."""
    logger.debug("c3 observer_rows entry")
    members = {row.observer_id: row for row in p1a.observers if row.observer_id in binding.observer_ids}
    p0_membership = _p0_membership(p0)
    rows: list[ObserverProgramBridgeRow] = []
    used: set[str] = set()
    for left in p0.observers:
        matches = tuple(
            right for right in members.values()
            if right.canonical == left.canonical and right.response_kind == left.response_kind
        )
        if len(matches) > 1:
            reject("ambiguous-observer-program-bridge")
        if not matches:
            continue
        right = matches[0]
        if right.observer_id in used:
            reject("duplicate-p1a-observer-program-bridge")
        used.add(right.observer_id)
        kind_digest = sha256(kind_bytes(left.response_kind)).hexdigest()
        row_digest = digest("p1-c3-observer-bridge-row-v1", (
            ("p0-id", left.observer_id.encode()), ("p1a-id", right.observer_id.encode()),
            ("program", left.canonical), ("kind", kind_digest.encode()),
            ("p0-membership", p0_membership.encode()),
            ("p1a-membership", binding.membership_digest.encode()),
        ))
        rows.append(ObserverProgramBridgeRow(
            left.observer_id, right.observer_id, bytes(left.canonical), kind_digest,
            p0_membership, binding.membership_digest, row_digest,
        ))
    if not rows:
        reject("empty-observer-program-bridge")
    result = tuple(rows)
    logger.debug("c3 observer_rows exit rows=%d", len(result))
    return result


def _stage_rows(
    diagram: FiniteDiagramSource, source: RelationEvaluationSource,
) -> tuple[StageInputBridgeRow, ...]:
    """Infer exact same-ID, same-recurrence diagram-to-A2 stage bindings."""
    logger.debug("c3 stage_rows entry")
    relation = {row.stage_id: row for row in source.stages}
    rows: list[StageInputBridgeRow] = []
    for stage in diagram.stages:
        right = relation.get(stage.stage_id)
        if right is None:
            continue
        left_bytes, right_bytes = recurrence_bytes(stage.representative), recurrence_bytes(right.recurrence)
        if left_bytes != right_bytes:
            reject("same-stage-id-different-recurrence")
        recurrence_digest = sha256(left_bytes).hexdigest()
        left_commitment = stage_commitment(stage)
        row_digest = digest("p1-c3-stage-bridge-row-v1", (
            ("p0-id", stage.stage_id.encode()), ("p0-commitment", left_commitment.encode()),
            ("recurrence", recurrence_digest.encode()), ("a2-id", right.stage_id.encode()),
            ("a2-commitment", right.commitment.encode()),
        ))
        rows.append(StageInputBridgeRow(
            stage.stage_id, left_commitment, stage.representative,
            recurrence_digest, right.stage_id, right.commitment, row_digest,
        ))
    if not 1 <= len(rows) <= 32:
        reject("stage-program-bridge-count")
    result = tuple(rows)
    logger.debug("c3 stage_rows exit rows=%d", len(result))
    return result


def p0_p1a_response_bridge(
    raw_p0_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_p1a_doctrine: ObserverDoctrine, raw_p1a_source: ObserverSourceBinding,
    raw_a2_stage_source: RelationEvaluationSource,
) -> P0P1AResponseBridgeSource:
    """Build a response-free exact bridge solely from raw lower sources."""
    logger.debug("p0_p1a_response_bridge entry")
    p0, diagram, p1a, binding, source = _snapshot_sources(
        raw_p0_doctrine, raw_diagram, raw_p1a_doctrine,
        raw_p1a_source, raw_a2_stage_source,
    )
    observers, stages = _observer_rows(p0, p1a, binding), _stage_rows(diagram, source)
    bridge_digest = digest("p1-c3-response-bridge-v1", (
        ("version", BRIDGE_VERSION.encode()), ("scope", BRIDGE_SCOPE.encode()),
        ("p0", p0.fingerprint.encode()), ("diagram", diagram.source_digest.encode()),
        ("p1a", p1a.fingerprint.encode()), ("binding", binding.membership_digest.encode()),
        ("a2-source", source.source_digest.encode()),
        ("observer-rows", sequence("row", tuple(row.row_digest for row in observers))),
        ("stage-rows", sequence("row", tuple(row.row_digest for row in stages))),
        ("a2-order", sequence("commitment", source.ordered_commitments)),
    ))
    result = P0P1AResponseBridgeSource(
        p0.fingerprint, diagram.source_digest, p1a.fingerprint,
        binding.membership_digest, source.source_digest, observers, stages,
        source.ordered_commitments, bridge_digest,
    )
    logger.debug("p0_p1a_response_bridge exit observers=%d stages=%d", len(observers), len(stages))
    return result


def snapshot_response_bridge(
    raw_p0_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_p1a_doctrine: ObserverDoctrine, raw_p1a_source: ObserverSourceBinding,
    raw_a2_stage_source: RelationEvaluationSource, value: P0P1AResponseBridgeSource,
) -> P0P1AResponseBridgeSource:
    """Freshly reconstruct and exact-compare a supplied bridge artifact."""
    logger.debug("snapshot_response_bridge entry")
    supplied = shallow_bridge(value)
    expected = p0_p1a_response_bridge(
        raw_p0_doctrine, raw_diagram, raw_p1a_doctrine,
        raw_p1a_source, raw_a2_stage_source,
    )
    compare_bridge(supplied, expected)
    logger.debug("snapshot_response_bridge exit")
    return expected
