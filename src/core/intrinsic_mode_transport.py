"""Stack-safe reviewed transport between proof recurrences and strict native modes."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import logging

from .native_runtime import Breath, Mode, NativeObstruction, Nod, Rez, Tact, nod, rez, tact
from .proof_core_types import CoreTerm, Pulse, Silence

logger = logging.getLogger(__name__)
CARRIER_ID = "veyra.strict.intrinsic-mode-image.v1"
CODEC_SCHEMA = "veyra-recurrence-mode-codec-v1"
ORIGIN_NAME = "intrinsic-origin"
SUCCESSOR_MARK = "intrinsic-successor"
OBSERVER_NAME = "native-cycle"
BOUNDARY = (
    "exact fixed-anchor unary image only; arbitrary strict modes, labeled word "
    "modes, cyclic phase, approximate, weighted, and profile resonance excluded"
)


@dataclass(frozen=True)
class IntrinsicMode:
    """A strict native mode paired with its verified closed recurrence value."""

    recurrence: CoreTerm
    native: Mode
    digest: str

    def __post_init__(self) -> None:
        logger.debug("IntrinsicMode.__post_init__ entry")
        pulses = _walk_recurrence(self.recurrence)
        expected_native = _native_from_pulses(pulses)
        expected_digest = _digest_pulses(pulses)
        if type(self.native) is not Mode or self.native != expected_native or self.digest != expected_digest:
            _reject("forged-intrinsic-mode-wrapper")
        logger.debug("IntrinsicMode.__post_init__ exit")


def _reject(reason: str) -> None:
    logger.error("intrinsic_mode_transport rejected reason=%s", reason)
    raise ValueError(reason)


def _walk_recurrence(value: object) -> tuple[object, ...]:
    logger.debug("_walk_recurrence entry type=%s", type(value).__name__)
    cursor, pulses, seen = value, [], set()
    while type(cursor) is Pulse:
        identity = id(cursor)
        if identity in seen:
            _reject("cyclic-recurrence-value")
        seen.add(identity)
        pulses.append(cursor)
        cursor = cursor.tail
    if type(cursor) is not Silence:
        _reject("noncanonical-recurrence-value")
    logger.debug("_walk_recurrence exit")
    return tuple(pulses)


def _from_pulses(pulses: tuple[object, ...]) -> CoreTerm:
    logger.debug("_from_pulses entry")
    result: CoreTerm = Silence()
    for _ in reversed(pulses):
        result = Pulse(result)
    logger.debug("_from_pulses exit")
    return result


def _canonical_anchor() -> Nod:
    logger.debug("_canonical_anchor entry")
    result = nod(rez(ORIGIN_NAME), ORIGIN_NAME)
    logger.debug("_canonical_anchor exit")
    return result


def _canonical_tact() -> Tact:
    logger.debug("_canonical_tact entry")
    anchor = _canonical_anchor()
    result = tact(anchor, anchor, SUCCESSOR_MARK)
    logger.debug("_canonical_tact exit")
    return result


def _native_from_pulses(pulses: tuple[object, ...]) -> Mode:
    logger.debug("_native_from_pulses entry")
    items = tuple(_canonical_tact() for _ in pulses)
    source = Breath(items, None) if items else Breath((), _canonical_anchor())
    result = Mode(source, OBSERVER_NAME)
    logger.debug("_native_from_pulses exit")
    return result


def _digest_pulses(pulses: tuple[object, ...]) -> str:
    logger.debug("_digest_pulses entry")
    state = sha256(f"{CODEC_SCHEMA}\0{CARRIER_ID}\0".encode())
    for _ in pulses:
        state.update(b"pulse\0")
    state.update(b"silence\0")
    result = state.hexdigest()
    logger.debug("_digest_pulses exit digest=%s", result)
    return result


def recurrence_digest(value: object) -> str:
    """Return a domain-bound structural digest without a numeric shadow."""
    logger.debug("recurrence_digest entry type=%s", type(value).__name__)
    result = _digest_pulses(_walk_recurrence(value))
    logger.debug("recurrence_digest exit digest=%s", result)
    return result


def recurrence_equal(left: object, right: object) -> bool:
    """Compare canonical recurrence values iteratively and reject malformed values."""
    logger.debug("recurrence_equal entry")
    left_cursor, right_cursor = left, right
    left_seen: set[int] = set()
    right_seen: set[int] = set()
    while type(left_cursor) is Pulse and type(right_cursor) is Pulse:
        left_identity, right_identity = id(left_cursor), id(right_cursor)
        if left_identity in left_seen or right_identity in right_seen:
            _reject("cyclic-recurrence-value")
        left_seen.add(left_identity)
        right_seen.add(right_identity)
        left_cursor, right_cursor = left_cursor.tail, right_cursor.tail
    if type(left_cursor) is Pulse:
        _walk_recurrence(left_cursor)
    if type(right_cursor) is Pulse:
        _walk_recurrence(right_cursor)
    if type(left_cursor) not in (Pulse, Silence) or type(right_cursor) not in (Pulse, Silence):
        _reject("noncanonical-recurrence-value")
    result = type(left_cursor) is Silence and type(right_cursor) is Silence
    logger.debug("recurrence_equal exit result=%s", result)
    return result


def encode_recurrence(value: object) -> IntrinsicMode:
    """Totally encode one finite closed ``Silence|Pulse`` value into the strict image."""
    logger.debug("encode_recurrence entry type=%s", type(value).__name__)
    pulses = _walk_recurrence(value)
    result = IntrinsicMode(value, _native_from_pulses(pulses), _digest_pulses(pulses))
    logger.debug("encode_recurrence exit digest=%s", result.digest)
    return result


def _obstruction(reason: str, *residue: str) -> NativeObstruction:
    logger.error("intrinsic_mode_transport decode blocked reason=%s residue=%r", reason, residue)
    return NativeObstruction("intrinsic-mode-decode", reason, tuple(residue))


def _exact_anchor(value: object) -> bool:
    logger.debug("_exact_anchor entry type=%s", type(value).__name__)
    result = (
        type(value) is Nod and type(value.residue) is Rez
        and type(value.residue.name) is str and type(value.mark) is str
        and value == _canonical_anchor()
    )
    logger.debug("_exact_anchor exit result=%s", result)
    return result


def _exact_tact(value: object) -> bool:
    logger.debug("_exact_tact entry type=%s", type(value).__name__)
    result = (
        type(value) is Tact and _exact_anchor(value.start)
        and _exact_anchor(value.end) and type(value.mark) is str
        and value.mark == SUCCESSOR_MARK
    )
    logger.debug("_exact_tact exit result=%s", result)
    return result


def decode_mode(value: object) -> IntrinsicMode | NativeObstruction:
    """Partially decode only the exact fixed-anchor strict intrinsic image."""
    logger.debug("decode_mode entry type=%s", type(value).__name__)
    if type(value) is not Mode or type(value.breath) is not Breath:
        return _obstruction("foreign-mode-type", type(value).__name__)
    if type(value.observer) is not str or value.observer != OBSERVER_NAME:
        return _obstruction("observer-mismatch")
    items, anchor = value.breath.tacts, value.breath.anchor
    if type(items) is not tuple:
        return _obstruction("noncanonical-tact-container")
    if not items:
        if not _exact_anchor(anchor):
            return _obstruction("zero-anchor-mismatch")
    elif anchor is not None:
        return _obstruction("nonzero-anchor-present")
    if any(not _exact_tact(item) for item in items):
        return _obstruction("foreign-recurrence-tact")
    recurrence = _from_pulses(tuple(items))
    canonical = encode_recurrence(recurrence)
    if canonical.native != value:
        return _obstruction("noncanonical-mode-structure")
    result = IntrinsicMode(recurrence, value, canonical.digest)
    logger.debug("decode_mode exit digest=%s", result.digest)
    return result


def verify_intrinsic_mode(value: object) -> bool:
    """Verify wrapper fields by exact re-encoding; never trust direct construction."""
    logger.debug("verify_intrinsic_mode entry type=%s", type(value).__name__)
    if type(value) is not IntrinsicMode:
        logger.error("verify_intrinsic_mode invalid wrapper type")
        return False
    try:
        canonical = encode_recurrence(value.recurrence)
    except ValueError:
        logger.exception("verify_intrinsic_mode malformed recurrence")
        return False
    decoded = decode_mode(value.native)
    result = (
        type(decoded) is IntrinsicMode and canonical.native == value.native
        and canonical.digest == value.digest == decoded.digest
        and recurrence_equal(value.recurrence, decoded.recurrence)
    )
    logger.debug("verify_intrinsic_mode exit result=%s", result)
    return result
