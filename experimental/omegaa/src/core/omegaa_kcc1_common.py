"""Distinct KCC1 decode, resource and integrity envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from types import MemberDescriptorType
from typing import NoReturn, Protocol, cast

logger = logging.getLogger(__name__)
_LOGGER = logger
KCC1_PREFIX = b"KCC1"
MAX_INPUT, MAX_OUTPUT = range(2)


class KCC1DecodeCodeV1(IntEnum):
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


class KCC1ResourceKindV1(IntEnum):
    INPUT_BYTES = 0
    OUTPUT_BYTES = 1


class KCC1DecodeError(ValueError):
    """First-offset canonical KCC1 wire failure."""

    def __init__(self, code: KCC1DecodeCodeV1, absolute_offset: int) -> None:
        _LOGGER.debug("KCC1DecodeError.__init__ entry")
        if (
            type(code) is not KCC1DecodeCodeV1
            or type(absolute_offset) is not int
            or absolute_offset < 0
        ):
            _LOGGER.error("KCC1DecodeError.__init__ error host-shape")
            raise TypeError("invalid KCC1 decode error")
        self.code = code
        self.absolute_offset = absolute_offset
        self.offset = absolute_offset
        super().__init__(f"{code.name}@{absolute_offset}")
        _LOGGER.error("KCC1 decode rejected code=%s offset=%d", code.name, absolute_offset)
        _LOGGER.debug("KCC1DecodeError.__init__ exit")


class KCC1ResourceLimit(ValueError):
    """Local bounded-attempt refusal, never a semantic rejection."""

    def __init__(
        self,
        kind: KCC1ResourceKindV1,
        allowed: int,
        required: int,
        absolute_offset: int,
    ) -> None:
        _LOGGER.debug("KCC1ResourceLimit.__init__ entry")
        if (
            type(kind) is not KCC1ResourceKindV1
            or any(type(value) is not int or value < 0 for value in (allowed, required, absolute_offset))
        ):
            _LOGGER.error("KCC1ResourceLimit.__init__ error host-shape")
            raise TypeError("invalid KCC1 resource result")
        self.kind = kind
        self.allowed = allowed
        self.required = required
        self.absolute_offset = absolute_offset
        self.offset = absolute_offset
        super().__init__(f"{kind.name}:{allowed}<{required}@{absolute_offset}")
        _LOGGER.error(
            "KCC1 resource refused kind=%s allowed=%d required=%d offset=%d",
            kind.name, allowed, required, absolute_offset,
        )
        _LOGGER.debug("KCC1ResourceLimit.__init__ exit")


class KCC1IntegrityError(ValueError):
    """Sanitized host/integrity failure channel."""

    def __init__(self, reason: str) -> None:
        _LOGGER.debug("KCC1IntegrityError.__init__ entry")
        if type(reason) is not str:
            _LOGGER.error("KCC1IntegrityError.__init__ error reason-type")
            raise TypeError("invalid KCC1 integrity reason")
        self.reason = reason
        super().__init__(reason)
        _LOGGER.error("KCC1 integrity rejected reason=%s", reason)
        _LOGGER.debug("KCC1IntegrityError.__init__ exit")


@dataclass(frozen=True, slots=True)
class KCC1LimitsV1:
    max_input_bytes: int = 1_048_576
    max_output_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        _LOGGER.debug("KCC1LimitsV1.__post_init__ entry")
        if any(
            type(value) is not int or value <= 0
            for value in (self.max_input_bytes, self.max_output_bytes)
        ):
            _LOGGER.error("KCC1LimitsV1.__post_init__ error positive-exact-int")
            raise ValueError("KCC1 limits must be exact positive integers")
        _LOGGER.debug("KCC1LimitsV1.__post_init__ exit")


DEFAULT_KCC1_LIMITS_V1 = KCC1LimitsV1()
_LIMITS_CLASS = KCC1LimitsV1
_DEFAULT_LIMITS_FROZEN = DEFAULT_KCC1_LIMITS_V1
_DEFAULT_LIMIT_VALUES = (1_048_576, 1_048_576)
_DECODE_ENUM_CLASS = KCC1DecodeCodeV1
_RESOURCE_ENUM_CLASS = KCC1ResourceKindV1
_DECODE_CODES_FROZEN = tuple(KCC1DecodeCodeV1(index) for index in range(11))
_RESOURCE_KINDS_FROZEN = tuple(KCC1ResourceKindV1(index) for index in range(2))
_LIMIT_NAMES = ("max_input_bytes", "max_output_bytes")
_LIMIT_SLOTS = tuple(vars(KCC1LimitsV1)[name] for name in _LIMIT_NAMES)
_LIMIT_INIT = vars(KCC1LimitsV1)["__init__"]
_LIMIT_POST = vars(KCC1LimitsV1)["__post_init__"]
_LIMIT_INIT_CODE = _LIMIT_INIT.__code__
_LIMIT_POST_CODE = _LIMIT_POST.__code__
_DECODE_ERROR_CLASS = KCC1DecodeError
_DECODE_ERROR_INIT = vars(_DECODE_ERROR_CLASS)["__init__"]
_DECODE_ERROR_INIT_CODE = _DECODE_ERROR_INIT.__code__
_RESOURCE_ERROR_CLASS = KCC1ResourceLimit
_RESOURCE_ERROR_INIT = vars(_RESOURCE_ERROR_CLASS)["__init__"]
_RESOURCE_ERROR_INIT_CODE = _RESOURCE_ERROR_INIT.__code__
_INTEGRITY_ERROR_CLASS = KCC1IntegrityError
_INTEGRITY_ERROR_INIT = vars(_INTEGRITY_ERROR_CLASS)["__init__"]
_INTEGRITY_ERROR_INIT_CODE = _INTEGRITY_ERROR_INIT.__code__


class _SlotDescriptor(Protocol):
    def __get__(self, instance: object, owner: type[object]) -> object: ...


def _integrity_error(reason: str) -> NoReturn:
    _LOGGER.debug("_integrity_error entry reason=%s", reason)
    _LOGGER.error("KCC1 integrity rejected reason=%s", reason)
    error = ValueError.__new__(_INTEGRITY_ERROR_CLASS)
    object.__setattr__(error, "reason", reason)
    ValueError.__init__(error, reason)
    raise error


def validate_kcc1_common_integrity_v1() -> None:
    """Reject enum, limits-class, slot or generated-hook drift."""
    _LOGGER.debug("validate_kcc1_common_integrity_v1 entry")
    namespace = vars(_LIMITS_CLASS)
    default_values = tuple(
        slot.__get__(_DEFAULT_LIMITS_FROZEN, _LIMITS_CLASS)
        for slot in _LIMIT_SLOTS
    )
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("KCC1LimitsV1") is not _LIMITS_CLASS
        or globals().get("DEFAULT_KCC1_LIMITS_V1") is not _DEFAULT_LIMITS_FROZEN
        or globals().get("KCC1DecodeCodeV1") is not _DECODE_ENUM_CLASS
        or globals().get("KCC1ResourceKindV1") is not _RESOURCE_ENUM_CLASS
        or globals().get("KCC1DecodeError") is not _DECODE_ERROR_CLASS
        or globals().get("KCC1ResourceLimit") is not _RESOURCE_ERROR_CLASS
        or globals().get("KCC1IntegrityError") is not _INTEGRITY_ERROR_CLASS
        or _DECODE_ERROR_CLASS.__dict__.get("__init__") is not _DECODE_ERROR_INIT
        or _DECODE_ERROR_INIT.__code__ is not _DECODE_ERROR_INIT_CODE
        or _RESOURCE_ERROR_CLASS.__dict__.get("__init__") is not _RESOURCE_ERROR_INIT
        or _RESOURCE_ERROR_INIT.__code__ is not _RESOURCE_ERROR_INIT_CODE
        or _INTEGRITY_ERROR_CLASS.__dict__.get("__init__") is not _INTEGRITY_ERROR_INIT
        or _INTEGRITY_ERROR_INIT.__code__ is not _INTEGRITY_ERROR_INIT_CODE
        or len(_DECODE_CODES_FROZEN) != 11
        or len(_RESOURCE_KINDS_FROZEN) != 2
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
        _integrity_error("kcc1-common-integrity")
    _LOGGER.debug("validate_kcc1_common_integrity_v1 exit")


def _decode_error(code: KCC1DecodeCodeV1, absolute_offset: int) -> NoReturn:
    _LOGGER.debug("_decode_error entry code=%s offset=%d", code.name, absolute_offset)
    validate_kcc1_common_integrity_v1()
    raise _DECODE_ERROR_CLASS(code, absolute_offset)


def _resource(
    kind: KCC1ResourceKindV1,
    allowed: int,
    required: int,
    absolute_offset: int,
) -> NoReturn:
    _LOGGER.debug(
        "_resource entry kind=%s allowed=%d required=%d offset=%d",
        kind.name, allowed, required, absolute_offset,
    )
    validate_kcc1_common_integrity_v1()
    raise _RESOURCE_ERROR_CLASS(kind, allowed, required, absolute_offset)


def _slot(descriptor: object, value: object, label: str) -> object:
    _LOGGER.debug("_slot entry label=%s", label)
    try:
        result = cast(_SlotDescriptor, descriptor).__get__(value, type(value))
    except Exception as exc:
        _LOGGER.error("_slot error label=%s exception=%s", label, type(exc).__name__)
        _integrity_error(f"invalid-{label}")
    _LOGGER.debug("_slot exit label=%s", label)
    return result


def _snapshot_limits(value: KCC1LimitsV1) -> tuple[int, int]:
    _LOGGER.debug("_snapshot_limits entry")
    validate_kcc1_common_integrity_v1()
    if type(value) is not _LIMITS_CLASS:
        _integrity_error("limits-host-shape")
    raw = tuple(
        _slot(descriptor, value, name)
        for name, descriptor in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True)
    )
    if any(type(item) is not int or item <= 0 for item in raw):
        _integrity_error("limits-host-shape")
    result = cast(tuple[int, int], raw)
    _LOGGER.debug("_snapshot_limits exit")
    return result
