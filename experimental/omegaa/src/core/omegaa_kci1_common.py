"""Closed KCI1 enums, limits, U64 arithmetic, and integrity channel."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from types import MemberDescriptorType
from typing import NoReturn, Protocol, cast

logger = logging.getLogger(__name__)
_LOGGER = logger
KCI1_PREFIX = b"KCI1"
U64_LIMIT = 18_446_744_073_709_551_616
_U64_LIMIT_FROZEN = 18_446_744_073_709_551_616
MAX_INPUT, MAX_OUTPUT, MAX_EXPECTED, MAX_TERM = range(4)


class KCI1DecodeCodeV1(IntEnum):
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


class KCI1ResourceKindV1(IntEnum):
    INPUT_BYTES = 0
    OUTPUT_BYTES = 1
    EXPECTED_BYTES = 2
    TERM_BYTES = 3


class KCI1IntegrityError(ValueError):
    """Sanitized host or captured-object integrity failure."""

    def __init__(self, reason: str) -> None:
        _LOGGER.debug("KCI1IntegrityError.__init__ entry")
        if type(reason) is not str:
            _LOGGER.error("KCI1IntegrityError.__init__ error reason-type")
            raise TypeError("invalid KCI1 integrity reason")
        self.reason = reason
        super().__init__(reason)
        _LOGGER.error("KCI1 integrity rejected reason=%s", reason)
        _LOGGER.debug("KCI1IntegrityError.__init__ exit")


@dataclass(frozen=True, slots=True)
class KCI1LimitsV1:
    max_input_bytes: int = 1_048_576
    max_output_bytes: int = 1_048_576
    max_expected_bytes: int = 524_288
    max_term_bytes: int = 524_288

    def __post_init__(self) -> None:
        _LOGGER.debug("KCI1LimitsV1.__post_init__ entry")
        values = (
            self.max_input_bytes,
            self.max_output_bytes,
            self.max_expected_bytes,
            self.max_term_bytes,
        )
        if any(
            type(value) is not int or not 0 < value < 18_446_744_073_709_551_616
            for value in values
        ):
            _LOGGER.error("KCI1LimitsV1.__post_init__ error positive-u64")
            raise ValueError("KCI1 limits must be exact positive U64 values")
        _LOGGER.debug("KCI1LimitsV1.__post_init__ exit")


DEFAULT_KCI1_LIMITS_V1 = KCI1LimitsV1()
_LIMITS_CLASS = KCI1LimitsV1
_DEFAULT_LIMITS_FROZEN = DEFAULT_KCI1_LIMITS_V1
_DEFAULT_LIMIT_VALUES = (1_048_576, 1_048_576, 524_288, 524_288)
_DECODE_ENUM_CLASS = KCI1DecodeCodeV1
_RESOURCE_ENUM_CLASS = KCI1ResourceKindV1
_DECODE_CODES_FROZEN = tuple(KCI1DecodeCodeV1(index) for index in range(11))
_RESOURCE_KINDS_FROZEN = tuple(KCI1ResourceKindV1(index) for index in range(4))
_LIMIT_NAMES = (
    "max_input_bytes",
    "max_output_bytes",
    "max_expected_bytes",
    "max_term_bytes",
)
_LIMIT_SLOTS = tuple(vars(_LIMITS_CLASS)[name] for name in _LIMIT_NAMES)
_LIMIT_INIT = vars(_LIMITS_CLASS)["__init__"]
_LIMIT_POST = vars(_LIMITS_CLASS)["__post_init__"]
_LIMIT_INIT_CODE = _LIMIT_INIT.__code__
_LIMIT_POST_CODE = _LIMIT_POST.__code__
_INTEGRITY_ERROR_CLASS = KCI1IntegrityError
_INTEGRITY_ERROR_INIT = vars(_INTEGRITY_ERROR_CLASS)["__init__"]
_INTEGRITY_ERROR_INIT_CODE = _INTEGRITY_ERROR_INIT.__code__


class _SlotDescriptor(Protocol):
    def __get__(self, instance: object, owner: type[object]) -> object: ...


def _integrity_error(reason: str) -> NoReturn:
    _LOGGER.debug("_integrity_error entry reason=%s", reason)
    _LOGGER.error("KCI1 integrity rejected reason=%s", reason)
    error = ValueError.__new__(_INTEGRITY_ERROR_CLASS)
    object.__setattr__(error, "reason", reason)
    ValueError.__init__(error, reason)
    raise error


def validate_kci1_common_integrity_v1() -> None:
    """Refuse enum, limit, slot, generated-hook, alias, or default drift."""
    _LOGGER.debug("validate_kci1_common_integrity_v1 entry")
    namespace = vars(_LIMITS_CLASS)
    try:
        default_values = tuple(
            slot.__get__(_DEFAULT_LIMITS_FROZEN, _LIMITS_CLASS) for slot in _LIMIT_SLOTS
        )
    except Exception as exc:
        _LOGGER.error(
            "validate_kci1_common_integrity_v1 error slot exception=%s",
            type(exc).__name__,
        )
        _integrity_error("kci1-common-integrity")
    drift = (
        globals().get("logger") is not _LOGGER
        or type(globals().get("U64_LIMIT")) is not int
        or globals().get("U64_LIMIT") != 18_446_744_073_709_551_616
        or type(_U64_LIMIT_FROZEN) is not int
        or _U64_LIMIT_FROZEN != 18_446_744_073_709_551_616
        or globals().get("KCI1LimitsV1") is not _LIMITS_CLASS
        or globals().get("DEFAULT_KCI1_LIMITS_V1") is not _DEFAULT_LIMITS_FROZEN
        or globals().get("KCI1DecodeCodeV1") is not _DECODE_ENUM_CLASS
        or globals().get("KCI1ResourceKindV1") is not _RESOURCE_ENUM_CLASS
        or globals().get("KCI1IntegrityError") is not _INTEGRITY_ERROR_CLASS
        or _INTEGRITY_ERROR_CLASS.__dict__.get("__init__") is not _INTEGRITY_ERROR_INIT
        or _INTEGRITY_ERROR_INIT.__code__ is not _INTEGRITY_ERROR_INIT_CODE
        or len(_DECODE_CODES_FROZEN) != 11
        or len(_RESOURCE_KINDS_FROZEN) != 4
        or any(
            type(code) is not _DECODE_ENUM_CLASS
            or code is not _DECODE_ENUM_CLASS(index)
            or type(object.__getattribute__(code, "_value_")) is not int
            or object.__getattribute__(code, "_value_") != index
            for index, code in enumerate(_DECODE_CODES_FROZEN)
        )
        or any(
            type(kind) is not _RESOURCE_ENUM_CLASS
            or kind is not _RESOURCE_ENUM_CLASS(index)
            or type(object.__getattribute__(kind, "_value_")) is not int
            or object.__getattribute__(kind, "_value_") != index
            for index, kind in enumerate(_RESOURCE_KINDS_FROZEN)
        )
        or namespace.get("__init__") is not _LIMIT_INIT
        or namespace.get("__post_init__") is not _LIMIT_POST
        or _LIMIT_INIT.__code__ is not _LIMIT_INIT_CODE
        or _LIMIT_POST.__code__ is not _LIMIT_POST_CODE
        or any(
            namespace.get(name) is not slot or type(slot) is not MemberDescriptorType
            for name, slot in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True)
        )
        or any(type(value) is not int for value in default_values)
        or default_values != _DEFAULT_LIMIT_VALUES
    )
    if drift:
        _LOGGER.error("validate_kci1_common_integrity_v1 error drift")
        _integrity_error("kci1-common-integrity")
    _LOGGER.debug("validate_kci1_common_integrity_v1 exit")


def _slot(descriptor: object, value: object, label: str) -> object:
    _LOGGER.debug("_slot entry label=%s", label)
    try:
        result = cast(_SlotDescriptor, descriptor).__get__(value, type(value))
    except Exception as exc:
        _LOGGER.error("_slot error label=%s exception=%s", label, type(exc).__name__)
        _integrity_error(f"invalid-{label}")
    _LOGGER.debug("_slot exit label=%s", label)
    return result


def _snapshot_limits(value: KCI1LimitsV1) -> tuple[int, int, int, int]:
    _LOGGER.debug("_snapshot_limits entry")
    validate_kci1_common_integrity_v1()
    if type(value) is not _LIMITS_CLASS:
        _LOGGER.error("_snapshot_limits error host-shape")
        _integrity_error("limits-host-shape")
    raw = tuple(
        _slot(descriptor, value, name)
        for name, descriptor in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True)
    )
    if any(
        type(item) is not int or not 0 < item < 18_446_744_073_709_551_616
        for item in raw
    ):
        _LOGGER.error("_snapshot_limits error value-shape")
        _integrity_error("limits-host-shape")
    result = cast(tuple[int, int, int, int], raw)
    _LOGGER.debug("_snapshot_limits exit")
    return result


def _checked_u64(value: int, label: str) -> int:
    _LOGGER.debug("_checked_u64 entry label=%s", label)
    if type(value) is not int or not 0 <= value < 18_446_744_073_709_551_616:
        _LOGGER.error("_checked_u64 error label=%s", label)
        _integrity_error(f"kci1-{label}-u64")
    _LOGGER.debug("_checked_u64 exit label=%s", label)
    return value


def _checked_add_u64(left: int, right: int, label: str) -> int:
    _LOGGER.debug("_checked_add_u64 entry label=%s", label)
    _checked_u64(left, f"{label}-left")
    _checked_u64(right, f"{label}-right")
    result = left + right
    if result >= 18_446_744_073_709_551_616:
        _LOGGER.error("_checked_add_u64 error overflow label=%s", label)
        _integrity_error(f"kci1-{label}-overflow")
    _LOGGER.debug("_checked_add_u64 exit label=%s", label)
    return result
