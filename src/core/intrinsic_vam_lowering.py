"""Replay-bound R12.3 transport between reviewed carriers and intrinsic VAM IR."""

from __future__ import annotations

import logging
from typing import NoReturn

from .intrinsic_mode_transport import IntrinsicMode, recurrence_digest, verify_intrinsic_mode
from .intrinsic_vam_lowering_types import (
    IntrinsicLoweringLane,
    TransportedIntrinsicIR,
)
from .intrinsic_vam_receipts import (
    _make_intrinsic_transport,
    _require_intrinsic_replay,
    digest_transport_data,
)
from .intrinsic_vam_values import (
    IntrinsicVamLoweringError,
    _intrinsic_ir_to_r11,
    _r11_outcome_to_intrinsic_ir,
    intrinsic_ir_to_intrinsic_mode,
    intrinsic_ir_to_recurrence,
    intrinsic_mode_to_intrinsic_ir,
    recurrence_to_intrinsic_ir,
)
from .observer_core_codec import canonical_observer_bytes
from .observer_core_semantics import echo, infer_observer_kind, observe
from .observer_core_support import outcome_data
from .proof_core_types import CoreTerm, Pulse, Silence
from .shadow_effect_branding import (
    brand_observation,
    digest_bytes,
    response_kind_data,
    verify_branded_observation,
)
from .shadow_effect_types import BrandedObservation, CarrierId
from .observer_core_types import EchoOutcome

logger = logging.getLogger(__name__)


def _reject(reason: str) -> NoReturn:
    """Log and raise one stable R12.3 transport rejection."""
    logger.error("intrinsic VAM transport rejected reason=%s", reason)
    raise IntrinsicVamLoweringError(reason)


def _source(value: object) -> tuple[CoreTerm, CarrierId, str]:
    """Recover exact recurrence, provenance, and canonical source digest."""
    logger.debug("_source entry type=%s", type(value).__name__)
    if type(value) in {Silence, Pulse}:
        recurrence_to_intrinsic_ir(value)
        result = (value, CarrierId.R7_RECURRENCE, recurrence_digest(value))
    elif type(value) is IntrinsicMode and verify_intrinsic_mode(value):
        result = (value.recurrence, CarrierId.R9_INTRINSIC_MODE, value.digest)
    else:
        _reject("invalid-replay-source")
    logger.debug("_source exit provenance=%s", result[1].value)
    return result


def lower_r7_recurrence(value: object) -> TransportedIntrinsicIR:
    """Lower one exact bounded R7 recurrence with finite witness evidence."""
    logger.debug("lower_r7_recurrence entry type=%s", type(value).__name__)
    if type(value) not in {Silence, Pulse}:
        _reject("invalid-r7-lowering-source")
    ir = recurrence_to_intrinsic_ir(value)
    digest = recurrence_digest(value)
    result = _make_intrinsic_transport(IntrinsicLoweringLane.R7_RECURRENCE, CarrierId.R7_RECURRENCE, (digest,), "", "", digest, ir)
    logger.debug("lower_r7_recurrence exit")
    return result


def raise_r7_recurrence(expected_source: object, value: object) -> Silence | Pulse:
    """Raise only after replaying the caller-supplied expected R7 source."""
    logger.debug("raise_r7_recurrence entry")
    actual = _require_intrinsic_replay(lower_r7_recurrence(expected_source), value)
    result = intrinsic_ir_to_recurrence(actual.value)
    logger.debug("raise_r7_recurrence exit")
    return result


def lower_r9_intrinsic_mode(value: object) -> TransportedIntrinsicIR:
    """Lower one verified exact R9 intrinsic-mode wrapper."""
    logger.debug("lower_r9_intrinsic_mode entry type=%s", type(value).__name__)
    if type(value) is not IntrinsicMode or not verify_intrinsic_mode(value):
        _reject("invalid-r9-lowering-source")
    ir = intrinsic_mode_to_intrinsic_ir(value)
    result = _make_intrinsic_transport(IntrinsicLoweringLane.R9_INTRINSIC_MODE, CarrierId.R9_INTRINSIC_MODE, (value.digest,), "", "", value.digest, ir)
    logger.debug("lower_r9_intrinsic_mode exit")
    return result


def raise_r9_intrinsic_mode(expected_source: object, value: object) -> IntrinsicMode:
    """Raise only after replaying the expected verified R9 wrapper."""
    logger.debug("raise_r9_intrinsic_mode entry")
    actual = _require_intrinsic_replay(lower_r9_intrinsic_mode(expected_source), value)
    result = intrinsic_ir_to_intrinsic_mode(actual.value)
    logger.debug("raise_r9_intrinsic_mode exit digest=%s", result.digest)
    return result


def lower_r11_observation(observer: object, source: object) -> TransportedIntrinsicIR:
    """Evaluate, brand, and lower one exact R11 observation."""
    logger.debug("lower_r11_observation entry observer=%s", type(observer).__name__)
    recurrence, provenance, source_digest = _source(source)
    branded = brand_observation(observer, observe(observer, recurrence), provenance)
    ir = _r11_outcome_to_intrinsic_ir(branded.observation)
    result = _make_intrinsic_transport(
        IntrinsicLoweringLane.R11_BRANDED_OBSERVATION,
        provenance,
        (source_digest,),
        branded.brand.observer_digest,
        branded.brand.response_kind_digest,
        branded.payload_digest,
        ir,
    )
    logger.debug("lower_r11_observation exit")
    return result


def raise_r11_observation(observer: object, expected_source: object, value: object) -> BrandedObservation:
    """Replay source and observer before returning a newly verified R11 brand."""
    logger.debug("raise_r11_observation entry")
    expected = lower_r11_observation(observer, expected_source)
    actual = _require_intrinsic_replay(expected, value)
    observation = _intrinsic_ir_to_r11(actual.value)
    _, provenance, _ = _source(expected_source)
    result = brand_observation(observer, observation, provenance)
    verify_branded_observation(observer, result, provenance)
    logger.debug("raise_r11_observation exit")
    return result


def lower_r11_echo(observer: object, left: object, right: object) -> TransportedIntrinsicIR:
    """Evaluate and lower one ordered exact R11 echo outcome."""
    logger.debug("lower_r11_echo entry observer=%s", type(observer).__name__)
    left_term, left_provenance, left_digest = _source(left)
    right_term, right_provenance, right_digest = _source(right)
    if left_provenance is not right_provenance:
        _reject("mixed-echo-provenance")
    observer_digest = digest_bytes(canonical_observer_bytes(observer))
    kind_digest = digest_transport_data(response_kind_data(infer_observer_kind(observer)))
    outcome = echo(observer, left_term, right_term)
    payload_digest = digest_transport_data(outcome_data(outcome))
    result = _make_intrinsic_transport(
        IntrinsicLoweringLane.R11_ECHO_OUTCOME,
        left_provenance,
        (left_digest, right_digest),
        observer_digest,
        kind_digest,
        payload_digest,
        _r11_outcome_to_intrinsic_ir(outcome),
    )
    logger.debug("lower_r11_echo exit")
    return result


def raise_r11_echo(observer: object, left: object, right: object, value: object) -> EchoOutcome:
    """Replay ordered sources and observer before returning an R11 outcome."""
    logger.debug("raise_r11_echo entry")
    actual = _require_intrinsic_replay(lower_r11_echo(observer, left, right), value)
    result = _intrinsic_ir_to_r11(actual.value)
    logger.debug("raise_r11_echo exit type=%s", type(result).__name__)
    return result
