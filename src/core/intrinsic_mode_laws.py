"""Executable structural laws for the reviewed intrinsic recurrence/mode image."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from .intrinsic_arithmetic import (
    stitch as native_stitch, successor as native_successor, weave as native_weave,
    zero as native_zero,
)
from .intrinsic_mode_transport import (
    BOUNDARY, IntrinsicMode, _from_pulses, _walk_recurrence, decode_mode,
    encode_recurrence, recurrence_digest, recurrence_equal,
)
from .native_runtime import Mode
from .proof_core_types import CoreTerm, Pulse, Silence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TransportLaw:
    """One executable parity row; arbitrary validity comes from the Lean bridge."""

    law_id: str
    expected_digest: str
    native_digest: str
    holds: bool
    boundary: str = BOUNDARY


def recurrence_stitch(left: object, right: object) -> CoreTerm:
    """Structurally stitch two closed recurrence values without numeric conversion."""
    logger.debug("recurrence_stitch entry")
    result = _from_pulses(_walk_recurrence(left) + _walk_recurrence(right))
    logger.debug("recurrence_stitch exit digest=%s", recurrence_digest(result))
    return result


def recurrence_weave(left: object, right: object) -> CoreTerm:
    """Structurally repeat left once for every pulse structurally carried by right."""
    logger.debug("recurrence_weave entry")
    left_pulses, result_pulses = _walk_recurrence(left), []
    for _ in _walk_recurrence(right):
        result_pulses.extend(left_pulses)
    result = _from_pulses(tuple(result_pulses))
    logger.debug("recurrence_weave exit digest=%s", recurrence_digest(result))
    return result


def _law(law_id: str, expected: IntrinsicMode, actual: object) -> TransportLaw:
    logger.debug("_law entry law=%s", law_id)
    decoded = decode_mode(actual) if type(actual) is Mode else actual
    holds = (
        type(decoded) is IntrinsicMode and decoded.native == expected.native
        and recurrence_equal(decoded.recurrence, expected.recurrence)
    )
    native_digest = decoded.digest if type(decoded) is IntrinsicMode else ""
    result = TransportLaw(law_id, expected.digest, native_digest, holds)
    if not holds:
        logger.error("_law blocked law=%s actual=%r", law_id, actual)
    logger.debug("_law exit law=%s holds=%s", law_id, holds)
    return result


def zero_transport() -> TransportLaw:
    """Compare proof silence with the existing strict-native anchored zero."""
    logger.debug("zero_transport entry")
    result = _law("R9-LAW-ZERO", encode_recurrence(Silence()), native_zero())
    logger.debug("zero_transport exit holds=%s", result.holds)
    return result


def successor_transport(value: object) -> TransportLaw:
    """Compare proof pulse construction with strict-native structural successor."""
    logger.debug("successor_transport entry")
    encoded = encode_recurrence(value)
    result = _law(
        "R9-LAW-SUCCESSOR", encode_recurrence(Pulse(value)),
        native_successor(encoded.native),
    )
    logger.debug("successor_transport exit holds=%s", result.holds)
    return result


def stitch_transport(left: object, right: object) -> TransportLaw:
    """Compare proof-value stitch with the existing strict-native operation."""
    logger.debug("stitch_transport entry")
    first, second = encode_recurrence(left), encode_recurrence(right)
    expected = encode_recurrence(recurrence_stitch(left, right))
    result = _law("THM-R9-005", expected, native_stitch(first.native, second.native))
    logger.debug("stitch_transport exit holds=%s", result.holds)
    return result


def weave_transport(left: object, right: object) -> TransportLaw:
    """Compare proof-value weave extensionally with strict-native structural weave."""
    logger.debug("weave_transport entry")
    first, second = encode_recurrence(left), encode_recurrence(right)
    expected = encode_recurrence(recurrence_weave(left, right))
    result = _law("THM-R9-006", expected, native_weave(first.native, second.native))
    logger.debug("weave_transport exit holds=%s", result.holds)
    return result


def resonance_transport(value: object) -> TransportLaw:
    """Instantiate the R7 unit-witness resonance on one strict intrinsic image value."""
    logger.debug("resonance_transport entry")
    recurrence, unit = encode_recurrence(value), encode_recurrence(Pulse(Silence()))
    result = _law("THM-R9-008", recurrence, native_weave(recurrence.native, unit.native))
    logger.debug("resonance_transport exit holds=%s", result.holds)
    return result


def transport_law_rows() -> tuple[TransportLaw, ...]:
    """Return bounded executable parity rows; Lean supplies arbitrary proofs."""
    logger.debug("transport_law_rows entry")
    zero_value = Silence()
    one_value = Pulse(zero_value)
    two_value = Pulse(one_value)
    result = (
        zero_transport(), successor_transport(zero_value), successor_transport(two_value),
        stitch_transport(zero_value, two_value), stitch_transport(two_value, one_value),
        weave_transport(two_value, zero_value), weave_transport(two_value, one_value),
        weave_transport(two_value, two_value), resonance_transport(two_value),
    )
    logger.debug("transport_law_rows exit")
    return result
