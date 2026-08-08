"""Fresh runtime projections and structural helpers for P1-A morphisms."""

from __future__ import annotations

import logging

from .observer_core_codec import decode_observer
from .observer_core_semantics import observe
from .observer_core_support import response_data
from .observer_core_types import (
    Apply, Input, LeafKind, MarkValue, Pair, PairKind, PairValue,
    PrimitiveId, Ready, RecurrenceValue, ResponseKind, ResponseValue,
)
from .positive_ontology_response import _snapshot_response
from .positive_ontology_types import InternalObserver, ObserverDoctrine
from .positive_ontology_validation import PositiveOntologyValidationError
from .proof_core_types import Pulse, Silence
from .observer_morphism_types import (
    ObserverSourceBinding, ProjectionStep, ResponseTranslation,
)
from .observer_morphism_validation import (
    ObserverMorphismValidationError, response_kind_signature,
    snapshot_morphism_doctrine, snapshot_source_binding, snapshot_translation,
    translation_digest,
)

logger = logging.getLogger(__name__)


def translate_response(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    translation: ResponseTranslation,
    fine_value: ResponseValue,
) -> ResponseValue:
    """Apply an exact typed pair projection to one fresh response snapshot."""
    logger.debug("translate_response entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    translation = snapshot_translation(translation, doctrine, binding)
    value = _snapshot_response_value(fine_value)
    if response_kind_signature(_response_value_kind(value)) != response_kind_signature(translation.fine_kind):
        logger.error("translate_response fine kind mismatch")
        raise ObserverMorphismValidationError("translation-fine-response-kind-mismatch")
    cursor: ResponseValue = value
    for step in translation.projection:
        if type(cursor) is not PairValue:
            logger.error("translate_response projection shape mismatch")
            raise ObserverMorphismValidationError("translation-response-shape-mismatch")
        cursor = cursor.left if step is ProjectionStep.LEFT else cursor.right
    if response_kind_signature(_response_value_kind(cursor)) != response_kind_signature(translation.coarse_kind):
        logger.error("translate_response coarse kind mismatch")
        raise ObserverMorphismValidationError("translation-coarse-response-kind-mismatch")
    result = _snapshot_response_value(cursor)
    logger.debug("translate_response exit steps=%d", len(translation.projection))
    return result


def _snapshot_response_value(value: ResponseValue) -> ResponseValue:
    """Normalize lower-layer response failures into the P1-A boundary."""
    logger.debug("_snapshot_response_value entry")
    try:
        result = _snapshot_response(value)
    except PositiveOntologyValidationError as exc:
        logger.error("_snapshot_response_value rejected")
        raise ObserverMorphismValidationError("invalid-translation-response") from exc
    logger.debug("_snapshot_response_value exit")
    return result


def _build_translation(
    translation_id: str,
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    fine: InternalObserver,
    coarse: InternalObserver,
    projection: tuple[ProjectionStep, ...],
) -> ResponseTranslation:
    """Build one digest-bound translation after structural factorization."""
    logger.debug("build_translation entry")
    digest = translation_digest(
        translation_id, doctrine.fingerprint, binding.membership_digest,
        fine.observer_id, coarse.observer_id, projection,
        fine.response_kind, coarse.response_kind,
    )
    result = ResponseTranslation(
        translation_id, doctrine.fingerprint, binding.membership_digest,
        fine.observer_id, coarse.observer_id, projection,
        fine.response_kind, coarse.response_kind, digest,
    )
    logger.debug("build_translation exit")
    return result


def _check_comparison_witness(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    translation: ResponseTranslation,
    depth: int,
) -> bool:
    """Check one nonempty-domain sanity witness; not the factorization proof."""
    logger.debug("check_comparison_witness entry depth=%d", depth)
    members = {item.observer_id: item for item in doctrine.observers}
    recurrence = _recurrence_at_depth(depth)
    fine = observe(decode_observer(members[translation.fine_observer_id].canonical), recurrence)
    coarse = observe(decode_observer(members[translation.coarse_observer_id].canonical), recurrence)
    result = (
        type(fine) is Ready and type(coarse) is Ready
        and response_data(translate_response(doctrine, binding, translation, fine.value))
        == response_data(coarse.value)
    )
    logger.debug("check_comparison_witness exit result=%s", result)
    return result


def _comparison_is_nonempty(
    fine: InternalObserver, coarse: InternalObserver, depth: int
) -> bool:
    """Confirm the exact threshold intersection has a concrete recurrence."""
    logger.debug("_comparison_is_nonempty entry depth=%d", depth)
    recurrence = _recurrence_at_depth(depth)
    fine_run = observe(decode_observer(fine.canonical), recurrence)
    coarse_run = observe(decode_observer(coarse.canonical), recurrence)
    result = type(fine_run) is Ready and type(coarse_run) is Ready
    logger.debug("_comparison_is_nonempty exit result=%s", result)
    return result


def _observer_member(doctrine: ObserverDoctrine, observer_id: str) -> InternalObserver:
    """Return one exact already-snapshotted doctrine member."""
    logger.debug("observer_member entry")
    result = next((item for item in doctrine.observers if item.observer_id == observer_id), None)
    if result is None:
        logger.error("observer_member missing")
        raise ObserverMorphismValidationError("observer-nonmember")
    logger.debug("observer_member exit")
    return result


def _minimum_pulse_depth(observer: object) -> int:
    """Compute the exact R11 domain threshold on a fresh validated AST."""
    logger.debug("minimum_pulse_depth entry")
    stack: list[tuple[bool, object]] = [(False, observer)]
    values: list[int] = []
    while stack:
        closing, node = stack.pop()
        if not closing:
            stack.append((True, node))
            if type(node) is Apply:
                stack.append((False, node.child))
            elif type(node) is Pair:
                stack.extend(((False, node.right), (False, node.left)))
            continue
        if type(node) is Input:
            values.append(0)
        elif type(node) is Apply:
            child = values.pop()
            values.append(child + (1 if node.primitive is PrimitiveId.TAIL else 0))
        else:
            right, left = values.pop(), values.pop()
            values.append(max(left, right))
    if len(values) != 1:
        logger.error("minimum_pulse_depth shape rejected")
        raise ObserverMorphismValidationError("invalid-domain-profile-shape")
    result = values[0]
    logger.debug("minimum_pulse_depth exit minimum=%d", result)
    return result


def _response_value_kind(value: ResponseValue) -> ResponseKind:
    """Infer the exact kind of a fresh bounded response value."""
    logger.debug("response_value_kind entry")
    stack: list[tuple[bool, object]] = [(False, value)]
    kinds: list[ResponseKind] = []
    while stack:
        closing, node = stack.pop()
        if not closing:
            stack.append((True, node))
            if type(node) is PairValue:
                stack.extend(((False, node.right), (False, node.left)))
            continue
        if type(node) is RecurrenceValue:
            kinds.append(LeafKind.RECURRENCE)
        elif type(node) is MarkValue:
            kinds.append(LeafKind.MARK)
        elif type(node) is PairValue:
            right, left = kinds.pop(), kinds.pop()
            kinds.append(PairKind(left, right))
        else:
            logger.error("response_value_kind exact gate rejected")
            raise ObserverMorphismValidationError("invalid-response-value")
    if len(kinds) != 1:
        logger.error("response_value_kind shape rejected")
        raise ObserverMorphismValidationError("invalid-response-shape")
    result = kinds[0]
    logger.debug("response_value_kind exit")
    return result


def _recurrence_at_depth(depth: int):
    """Construct the canonical nonempty-domain witness at an exact depth."""
    logger.debug("recurrence_at_depth entry")
    if type(depth) is not int or not 0 <= depth <= 128:
        logger.error("recurrence_at_depth invalid depth")
        raise ObserverMorphismValidationError("invalid-comparison-witness-depth")
    result = Silence()
    for _ in range(depth):
        result = Pulse(result)
    logger.debug("recurrence_at_depth exit depth=%d", depth)
    return result
