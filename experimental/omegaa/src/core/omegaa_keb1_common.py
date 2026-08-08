"""KEB1 errors, exact resource policy and hostile-safe primitives."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from types import MemberDescriptorType
from typing import NoReturn, Protocol, cast

logger = logging.getLogger(__name__)
_LOGGER = logger
KEB1_PREFIX = b"KEB1"
U64_LIMIT = 18446744073709551616
_U64_LIMIT_FROZEN = 18446744073709551616
MAX_U64 = U64_LIMIT - 1
(
    MAX_INPUT, MAX_OUTPUT, MAX_COMPOSITE_DEPTH, MAX_COMPOSITE_NODES,
    MAX_NESTED_KPT, MAX_KPT_LIST, MAX_KPT_NAT, MAX_EXPECTED_WIRE,
) = range(8)


class KEB1DecodeCodeV1(IntEnum):
    BAD_VERSION = 0
    BAD_DOMAIN = 1
    BAD_TAG = 2
    BAD_ARITY = 3
    BAD_ORDER = 4
    BAD_LENGTH = 5
    NONCANONICAL_NAT = 6
    NONCANONICAL_INT = 7
    DIGEST_MISMATCH = 8
    DEPENDENCY = 9
    TRAILING = 10


class KEB1ResourceKindV1(IntEnum):
    INPUT_BYTES = 0
    OUTPUT_BYTES = 1
    COMPOSITE_DEPTH = 2
    COMPOSITE_NODES = 3
    NESTED_KPT_BYTES = 4
    KPT_LIST_ITEMS = 5
    KPT_NAT_BYTES = 6
    EXPECTED_WIRE_BYTES = 7


class KEB1DecodeError(ValueError):
    def __init__(self, code: KEB1DecodeCodeV1, absolute_offset: int) -> None:
        _LOGGER.debug("KEB1DecodeError.__init__ entry")
        if type(code) is not KEB1DecodeCodeV1 or type(absolute_offset) is not int or not 0 <= absolute_offset <= MAX_U64:
            raise TypeError("invalid KEB1 decode error")
        self.code = code
        self.absolute_offset = absolute_offset
        self.offset = absolute_offset
        super().__init__(f"{code.name}@{absolute_offset}")
        _LOGGER.error("KEB1 decode rejected code=%s offset=%d", code.name, absolute_offset)


class KEB1ResourceLimit(ValueError):
    def __init__(self, kind: KEB1ResourceKindV1, allowed: int, required: int, absolute_offset: int) -> None:
        _LOGGER.debug("KEB1ResourceLimit.__init__ entry")
        if type(kind) is not KEB1ResourceKindV1 or any(type(v) is not int or not 0 <= v <= MAX_U64 for v in (allowed, required, absolute_offset)):
            raise TypeError("invalid KEB1 resource result")
        self.kind, self.allowed, self.required = kind, allowed, required
        self.absolute_offset = self.offset = absolute_offset
        super().__init__(f"{kind.name}:{allowed}<{required}@{absolute_offset}")
        _LOGGER.error("KEB1 resource refused kind=%s allowed=%d required=%d offset=%d", kind.name, allowed, required, absolute_offset)


class KEB1IntegrityError(ValueError):
    def __init__(self, reason: str) -> None:
        _LOGGER.debug("KEB1IntegrityError.__init__ entry")
        if type(reason) is not str:
            raise TypeError("invalid KEB1 integrity reason")
        self.reason = reason
        super().__init__(reason)
        _LOGGER.error("KEB1 integrity rejected reason=%s", reason)


@dataclass(frozen=True, slots=True)
class KEB1LimitsV1:
    max_input_bytes: int = 1_048_576
    max_output_bytes: int = 1_048_576
    max_composite_depth: int = 129
    max_composite_nodes: int = 10_001
    max_nested_kpt_bytes: int = 1_048_576
    max_kpt_list_items: int = 4096
    max_kpt_nat_bytes: int = 64
    max_expected_wire_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        _LOGGER.debug("KEB1LimitsV1.__post_init__ entry")
        values = tuple(getattr(self, name) for name in _LIMIT_NAMES)
        if any(type(v) is not int or not 0 < v <= MAX_U64 for v in values):
            _LOGGER.error("KEB1LimitsV1.__post_init__ error host-shape")
            raise ValueError("KEB1 limits must be exact positive U64 integers")
        if self.max_composite_depth > 129:
            raise ValueError("KEB1 composite depth exceeds safe KPT envelope")
        _LOGGER.debug("KEB1LimitsV1.__post_init__ exit")


_LIMIT_NAMES = (
    "max_input_bytes", "max_output_bytes", "max_composite_depth", "max_composite_nodes",
    "max_nested_kpt_bytes", "max_kpt_list_items", "max_kpt_nat_bytes", "max_expected_wire_bytes",
)
DEFAULT_KEB1_LIMITS_V1 = KEB1LimitsV1()
_DEFAULT_LIMITS_FROZEN = DEFAULT_KEB1_LIMITS_V1
_DEFAULT_LIMIT_VALUES = (1_048_576, 1_048_576, 129, 10_001, 1_048_576, 4096, 64, 1_048_576)
_LIMIT_CLASS = KEB1LimitsV1
_LIMIT_SLOTS = tuple(vars(_LIMIT_CLASS)[name] for name in _LIMIT_NAMES)
_LIMIT_INIT = vars(_LIMIT_CLASS)["__init__"]
_LIMIT_POST = vars(_LIMIT_CLASS)["__post_init__"]
_LIMIT_INIT_CODE, _LIMIT_POST_CODE = _LIMIT_INIT.__code__, _LIMIT_POST.__code__
_DECODE_CLASS, _RESOURCE_CLASS = KEB1DecodeCodeV1, KEB1ResourceKindV1
_DECODE_VALUES = tuple(_DECODE_CLASS(i) for i in range(11))
_RESOURCE_VALUES = tuple(_RESOURCE_CLASS(i) for i in range(8))
_DECODE_ERROR_CLASS = KEB1DecodeError
_RESOURCE_ERROR_CLASS = KEB1ResourceLimit
_INTEGRITY_ERROR_CLASS = KEB1IntegrityError
_DECODE_ERROR_INIT = vars(_DECODE_ERROR_CLASS)["__init__"]
_RESOURCE_ERROR_INIT = vars(_RESOURCE_ERROR_CLASS)["__init__"]
_INTEGRITY_ERROR_INIT = vars(_INTEGRITY_ERROR_CLASS)["__init__"]
_ERROR_INIT_CODES = (_DECODE_ERROR_INIT.__code__, _RESOURCE_ERROR_INIT.__code__, _INTEGRITY_ERROR_INIT.__code__)
_ERROR_CLASS_KEYS = tuple(frozenset(vars(cls)) for cls in (_DECODE_ERROR_CLASS, _RESOURCE_ERROR_CLASS, _INTEGRITY_ERROR_CLASS))


class _SlotDescriptor(Protocol):
    def __get__(self, instance: object, owner: type[object]) -> object: ...


def _integrity_error(reason: str) -> NoReturn:
    _LOGGER.debug("_integrity_error entry reason=%s", reason)
    error = ValueError.__new__(_INTEGRITY_ERROR_CLASS)
    object.__setattr__(error, "reason", reason)
    ValueError.__init__(error, reason)
    _LOGGER.error("KEB1 integrity rejected reason=%s", reason)
    raise error


_INTEGRITY_FROZEN = _integrity_error
_INTEGRITY_CODE = _INTEGRITY_FROZEN.__code__


def validate_keb1_common_integrity_v1() -> None:
    _LOGGER.debug("validate_keb1_common_integrity_v1 entry")
    namespace = vars(_LIMIT_CLASS)
    drift = (
        globals().get("logger") is not _LOGGER or globals().get("KEB1LimitsV1") is not _LIMIT_CLASS
        or globals().get("U64_LIMIT") != _U64_LIMIT_FROZEN or _U64_LIMIT_FROZEN != 18446744073709551616
        or globals().get("DEFAULT_KEB1_LIMITS_V1") is not _DEFAULT_LIMITS_FROZEN
        or globals().get("KEB1DecodeCodeV1") is not _DECODE_CLASS or globals().get("KEB1ResourceKindV1") is not _RESOURCE_CLASS
        or globals().get("KEB1DecodeError") is not _DECODE_ERROR_CLASS
        or globals().get("KEB1ResourceLimit") is not _RESOURCE_ERROR_CLASS
        or globals().get("KEB1IntegrityError") is not _INTEGRITY_ERROR_CLASS
        or vars(_DECODE_ERROR_CLASS).get("__init__") is not _DECODE_ERROR_INIT
        or vars(_RESOURCE_ERROR_CLASS).get("__init__") is not _RESOURCE_ERROR_INIT
        or vars(_INTEGRITY_ERROR_CLASS).get("__init__") is not _INTEGRITY_ERROR_INIT
        or tuple(init.__code__ for init in (_DECODE_ERROR_INIT, _RESOURCE_ERROR_INIT, _INTEGRITY_ERROR_INIT)) != _ERROR_INIT_CODES
        or tuple(frozenset(vars(cls)) for cls in (_DECODE_ERROR_CLASS, _RESOURCE_ERROR_CLASS, _INTEGRITY_ERROR_CLASS)) != _ERROR_CLASS_KEYS
        or len(_DECODE_VALUES) != 11 or len(_RESOURCE_VALUES) != 8
        or any(type(v) is not _DECODE_CLASS or object.__getattribute__(v, "_value_") != i for i, v in enumerate(_DECODE_VALUES))
        or any(type(v) is not _RESOURCE_CLASS or object.__getattribute__(v, "_value_") != i for i, v in enumerate(_RESOURCE_VALUES))
        or namespace.get("__init__") is not _LIMIT_INIT or namespace.get("__post_init__") is not _LIMIT_POST
        or _LIMIT_INIT.__code__ is not _LIMIT_INIT_CODE or _LIMIT_POST.__code__ is not _LIMIT_POST_CODE
        or any(namespace.get(n) is not s or type(s) is not MemberDescriptorType for n, s in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True))
        or tuple(slot.__get__(_DEFAULT_LIMITS_FROZEN, _LIMIT_CLASS) for slot in _LIMIT_SLOTS) != _DEFAULT_LIMIT_VALUES
    )
    if drift:
        _INTEGRITY_FROZEN("keb1-common-integrity")
    _LOGGER.debug("validate_keb1_common_integrity_v1 exit")


_VALIDATE_COMMON_FROZEN = validate_keb1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON_FROZEN.__code__


def _slot(descriptor: object, value: object, label: str) -> object:
    _LOGGER.debug("_slot entry label=%s", label)
    try:
        result = cast(_SlotDescriptor, descriptor).__get__(value, type(value))
    except Exception:
        _INTEGRITY_FROZEN(f"invalid-{label}")
    _LOGGER.debug("_slot exit label=%s", label)
    return result


_SLOT_FROZEN = _slot
_SLOT_CODE = _SLOT_FROZEN.__code__


def _snapshot_limits(value: KEB1LimitsV1) -> tuple[int, ...]:
    _LOGGER.debug("_snapshot_limits entry")
    if (
        globals().get("validate_keb1_common_integrity_v1") is not _VALIDATE_COMMON_FROZEN
        or _VALIDATE_COMMON_FROZEN.__code__ is not _VALIDATE_COMMON_CODE
        or globals().get("_slot") is not _SLOT_FROZEN
        or _SLOT_FROZEN.__code__ is not _SLOT_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_FROZEN
        or _INTEGRITY_FROZEN.__code__ is not _INTEGRITY_CODE
    ):
        _INTEGRITY_FROZEN("keb1-common-helper-integrity")
    _VALIDATE_COMMON_FROZEN()
    if type(value) is not _LIMIT_CLASS:
        _INTEGRITY_FROZEN("limits-host-shape")
    untyped = tuple(_SLOT_FROZEN(s, value, n) for n, s in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True))
    if any(type(v) is not int for v in untyped):
        _INTEGRITY_FROZEN("limits-host-shape")
    raw = cast(tuple[int, ...], untyped)
    if any(not 0 < v <= MAX_U64 for v in raw) or raw[MAX_COMPOSITE_DEPTH] > 129:
        _INTEGRITY_FROZEN("limits-host-shape")
    _LOGGER.debug("_snapshot_limits exit")
    return raw


def _decode_error(code: KEB1DecodeCodeV1, offset: int) -> NoReturn:
    _LOGGER.debug("_decode_error entry code=%s offset=%d", code.name, offset)
    _VALIDATE_COMMON_FROZEN()
    raise _DECODE_ERROR_CLASS(code, offset)


def _resource(kind: KEB1ResourceKindV1, allowed: int, required: int, offset: int) -> NoReturn:
    _LOGGER.debug("_resource entry kind=%s", kind.name)
    _VALIDATE_COMMON_FROZEN()
    raise _RESOURCE_ERROR_CLASS(kind, allowed, required, offset)


def FirstUnsignedDifferenceV1(left: bytes, right: bytes) -> int | None:
    """Return the first unsigned-byte difference, or ``None`` iff equal."""
    _LOGGER.debug("FirstUnsignedDifferenceV1 entry left=%d right=%d", len(left) if type(left) is bytes else -1, len(right) if type(right) is bytes else -1)
    _VALIDATE_COMMON_FROZEN()
    if type(left) is not bytes or type(right) is not bytes:
        _INTEGRITY_FROZEN("first-difference-host-shape")
    stop = min(len(left), len(right))
    for index in range(stop):
        if left[index] != right[index]:
            _LOGGER.debug("FirstUnsignedDifferenceV1 exit index=%d", index)
            return index
    if len(left) != len(right):
        _LOGGER.debug("FirstUnsignedDifferenceV1 exit prefix_index=%d", stop)
        return stop
    _LOGGER.debug("FirstUnsignedDifferenceV1 exit equal=true")
    return None


def _u64(value: int) -> bytes:
    _LOGGER.debug("_u64 entry")
    if type(value) is not int or not 0 <= value <= MAX_U64:
        _INTEGRITY_FROZEN("u64-range")
    result = value.to_bytes(8, "big")
    _LOGGER.debug("_u64 exit")
    return result


_U64_FROZEN = _u64
_U64_CODE = _U64_FROZEN.__code__


def _frame(payload: bytes) -> bytes:
    _LOGGER.debug("_frame entry")
    if type(payload) is not bytes:
        _INTEGRITY_FROZEN("frame-host-shape")
    if globals().get("_u64") is not _U64_FROZEN or _U64_FROZEN.__code__ is not _U64_CODE:
        _INTEGRITY_FROZEN("keb1-u64-helper-integrity")
    result = _U64_FROZEN(len(payload)) + payload
    _LOGGER.debug("_frame exit bytes=%d", len(result))
    return result
