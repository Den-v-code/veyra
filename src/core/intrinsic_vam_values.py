"""Exact bounded value conversions for the R12.3 intrinsic VAM lanes."""

from __future__ import annotations

import logging
from typing import NoReturn

from vam.src.intrinsic_ir import (
    MAX_RECURRENCE_TACTS,
    intrinsic_ir_data,
    validate_intrinsic_ir,
)
from vam.src.intrinsic_ir_types import (
    IntrinsicAnchorIR,
    IntrinsicBlockedIR,
    IntrinsicDomainBlockedIR,
    IntrinsicEchoIR,
    IntrinsicMarkIR,
    IntrinsicMarkValueIR,
    IntrinsicMismatchIR,
    IntrinsicObstructionCodeIR,
    IntrinsicObstructionIR,
    IntrinsicPairValueIR,
    IntrinsicPathStepIR,
    IntrinsicReadyIR,
    IntrinsicRecurrenceIR,
    IntrinsicRecurrenceValueIR,
    IntrinsicTactIR,
)

from .intrinsic_mode_transport import IntrinsicMode, encode_recurrence, verify_intrinsic_mode
from .observer_core_support import outcome_data, response_data
from .observer_core_types import (
    Blocked,
    DomainBlocked,
    Echo,
    Mark,
    MarkValue,
    Mismatch,
    ObstructionCode,
    ObserverObstruction,
    PairValue,
    PathStep,
    Ready,
    RecurrenceValue,
)
from .proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


class IntrinsicVamLoweringError(ValueError):
    """A stable fail-closed R12.3 conversion rejection."""


def reject_lowering(reason: str) -> NoReturn:
    """Log and raise one R12.3 conversion rejection."""
    logger.error("intrinsic VAM lowering rejected reason=%s", reason)
    raise IntrinsicVamLoweringError(reason)


def recurrence_to_intrinsic_ir(value: object) -> IntrinsicRecurrenceIR:
    """Lower one bounded exact R7 recurrence into the R12.2 image."""
    logger.debug("recurrence_to_intrinsic_ir entry type=%s", type(value).__name__)
    cursor, tacts, seen = value, [], set()
    while type(cursor) is Pulse:
        identity = id(cursor)
        if identity in seen:
            reject_lowering("circular-recurrence")
        seen.add(identity)
        if len(tacts) >= MAX_RECURRENCE_TACTS:
            reject_lowering("recurrence-lowering-resource-limit")
        tacts.append(IntrinsicTactIR())
        cursor = cursor.tail
    if type(cursor) is not Silence:
        reject_lowering("noncanonical-recurrence")
    result = IntrinsicRecurrenceIR(tuple(tacts), IntrinsicAnchorIR() if not tacts else None)
    validate_intrinsic_ir(result)
    logger.debug("recurrence_to_intrinsic_ir exit tacts=%d", len(tacts))
    return result


def intrinsic_ir_to_recurrence(value: object) -> Silence | Pulse:
    """Raise one exact recurrence IR into a closed R7 value."""
    logger.debug("intrinsic_ir_to_recurrence entry type=%s", type(value).__name__)
    validate_intrinsic_ir(value)
    if type(value) is not IntrinsicRecurrenceIR:
        reject_lowering("intrinsic-ir-not-recurrence")
    result: Silence | Pulse = Silence()
    for _ in reversed(value.tacts):
        result = Pulse(result)
    logger.debug("intrinsic_ir_to_recurrence exit tacts=%d", len(value.tacts))
    return result


def intrinsic_mode_to_intrinsic_ir(value: object) -> IntrinsicRecurrenceIR:
    """Lower only a verified exact R9 wrapper."""
    logger.debug("intrinsic_mode_to_intrinsic_ir entry type=%s", type(value).__name__)
    if type(value) is not IntrinsicMode or not verify_intrinsic_mode(value):
        reject_lowering("invalid-intrinsic-mode")
    result = recurrence_to_intrinsic_ir(value.recurrence)
    logger.debug("intrinsic_mode_to_intrinsic_ir exit digest=%s", value.digest)
    return result


def intrinsic_ir_to_intrinsic_mode(value: object) -> IntrinsicMode:
    """Raise exact recurrence IR through the reviewed R9 encoder."""
    logger.debug("intrinsic_ir_to_intrinsic_mode entry type=%s", type(value).__name__)
    result = encode_recurrence(intrinsic_ir_to_recurrence(value))
    logger.debug("intrinsic_ir_to_intrinsic_mode exit digest=%s", result.digest)
    return result


def _obstruction_to_ir(value: ObserverObstruction) -> IntrinsicObstructionIR:
    """Convert one already validated R11 obstruction."""
    logger.debug("_obstruction_to_ir entry")
    result = IntrinsicObstructionIR(
        IntrinsicObstructionCodeIR(value.code.value),
        tuple(IntrinsicPathStepIR(step.value) for step in value.path),
    )
    intrinsic_ir_data(result)
    logger.debug("_obstruction_to_ir exit steps=%d", len(result.path))
    return result


def _ir_to_obstruction(value: IntrinsicObstructionIR) -> ObserverObstruction:
    """Raise one validated intrinsic obstruction into R11."""
    logger.debug("_ir_to_obstruction entry")
    result = ObserverObstruction(
        ObstructionCode(value.code.value),
        tuple(PathStep(step.value) for step in value.path),
    )
    outcome_data(Blocked((result,)))
    logger.debug("_ir_to_obstruction exit steps=%d", len(result.path))
    return result


def _response_to_ir(value: object) -> object:
    """Recursively lower one already bounded R11 response."""
    logger.debug("_response_to_ir entry type=%s", type(value).__name__)
    if type(value) is RecurrenceValue:
        result = IntrinsicRecurrenceValueIR(recurrence_to_intrinsic_ir(value.recurrence))
    elif type(value) is MarkValue:
        result = IntrinsicMarkValueIR(IntrinsicMarkIR(value.mark.value))
    elif type(value) is PairValue:
        result = IntrinsicPairValueIR(_response_to_ir(value.left), _response_to_ir(value.right))
    else:
        reject_lowering("invalid-r11-response")
    intrinsic_ir_data(result)
    logger.debug("_response_to_ir exit type=%s", type(result).__name__)
    return result


def _ir_to_response(value: object) -> object:
    """Recursively raise one validated intrinsic response into R11."""
    logger.debug("_ir_to_response entry type=%s", type(value).__name__)
    if type(value) is IntrinsicRecurrenceValueIR:
        result = RecurrenceValue(intrinsic_ir_to_recurrence(value.recurrence))
    elif type(value) is IntrinsicMarkValueIR:
        result = MarkValue(Mark(value.mark.value))
    elif type(value) is IntrinsicPairValueIR:
        result = PairValue(_ir_to_response(value.left), _ir_to_response(value.right))
    else:
        reject_lowering("invalid-intrinsic-response")
    response_data(result)
    logger.debug("_ir_to_response exit type=%s", type(result).__name__)
    return result


def _r11_outcome_to_intrinsic_ir(value: object) -> object:
    """Internally convert one replay-produced exact R11 outcome."""
    logger.debug("_r11_outcome_to_intrinsic_ir entry type=%s", type(value).__name__)
    outcome_data(value)
    if type(value) is Ready:
        result = IntrinsicReadyIR(_response_to_ir(value.value))
    elif type(value) is Blocked:
        result = IntrinsicBlockedIR(tuple(_obstruction_to_ir(item) for item in value.obstructions))
    elif type(value) is Echo:
        result = IntrinsicEchoIR(_response_to_ir(value.value))
    elif type(value) is Mismatch:
        result = IntrinsicMismatchIR(_response_to_ir(value.left), _response_to_ir(value.right))
    elif type(value) is DomainBlocked:
        result = IntrinsicDomainBlockedIR(
            tuple(_obstruction_to_ir(item) for item in value.left_obstructions),
            tuple(_obstruction_to_ir(item) for item in value.right_obstructions),
        )
    else:
        reject_lowering("invalid-r11-outcome")
    intrinsic_ir_data(result)
    logger.debug("_r11_outcome_to_intrinsic_ir exit type=%s", type(result).__name__)
    return result


def _intrinsic_ir_to_r11(value: object) -> object:
    """Internally raise IR only after an outer replay receipt check."""
    logger.debug("_intrinsic_ir_to_r11 entry type=%s", type(value).__name__)
    validate_intrinsic_ir(value)
    if type(value) in {IntrinsicRecurrenceValueIR, IntrinsicMarkValueIR, IntrinsicPairValueIR}:
        result = _ir_to_response(value)
    elif type(value) is IntrinsicObstructionIR:
        result = _ir_to_obstruction(value)
    elif type(value) is IntrinsicReadyIR:
        result = Ready(_ir_to_response(value.value))
    elif type(value) is IntrinsicBlockedIR:
        result = Blocked(tuple(_ir_to_obstruction(item) for item in value.obstructions))
    elif type(value) is IntrinsicEchoIR:
        result = Echo(_ir_to_response(value.value))
    elif type(value) is IntrinsicMismatchIR:
        result = Mismatch(_ir_to_response(value.left), _ir_to_response(value.right))
    elif type(value) is IntrinsicDomainBlockedIR:
        result = DomainBlocked(
            tuple(_ir_to_obstruction(item) for item in value.left),
            tuple(_ir_to_obstruction(item) for item in value.right),
        )
    elif type(value) is IntrinsicMarkIR:
        result = Mark(value.value)
    else:
        reject_lowering("unsupported-intrinsic-raise")
    if type(result) not in {ObserverObstruction, Mark}:
        outcome_data(result) if type(result) in {Ready, Blocked, Echo, Mismatch, DomainBlocked} else response_data(result)
    logger.debug("_intrinsic_ir_to_r11 exit type=%s", type(result).__name__)
    return result
