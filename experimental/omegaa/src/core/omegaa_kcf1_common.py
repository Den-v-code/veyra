"""Distinct KCF1 wire errors, resources and hostile-safe limits."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from types import MappingProxyType
from typing import NoReturn, Protocol, cast

logger = logging.getLogger(__name__)
KCF1_PREFIX = b"KCF1"
KCF1_MAX_SAFE_DEPTH = 128
(
    MAX_INPUT, MAX_OUTPUT, MAX_DEPTH, MAX_NODES, MAX_NESTED,
    MAX_KPT_LIST, MAX_KPT_NAT,
) = range(7)


class KCF1DecodeCodeV1(IntEnum):
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


class KCF1ResourceKindV1(IntEnum):
    INPUT_BYTES = 0
    OUTPUT_BYTES = 1
    COMPOSITE_DEPTH = 2
    COMPOSITE_NODES = 3
    NESTED_KPT_BYTES = 4
    KPT_LIST_ITEMS = 5
    KPT_NAT_BYTES = 6


_DECODE_CODES = tuple(KCF1DecodeCodeV1(index) for index in range(11))
_RESOURCE_KINDS = tuple(KCF1ResourceKindV1(index) for index in range(7))
_DECODE_CODES_FROZEN = _DECODE_CODES
_RESOURCE_KINDS_FROZEN = _RESOURCE_KINDS
_KPT_RESOURCE_MAP_FROZEN = MappingProxyType({
    "max_input_bytes": KCF1ResourceKindV1.NESTED_KPT_BYTES,
    "max_output_bytes": KCF1ResourceKindV1.OUTPUT_BYTES,
    "max_depth": KCF1ResourceKindV1.COMPOSITE_DEPTH,
    "max_nodes": KCF1ResourceKindV1.COMPOSITE_NODES,
    "max_list_items": KCF1ResourceKindV1.KPT_LIST_ITEMS,
    "max_nat_bytes": KCF1ResourceKindV1.KPT_NAT_BYTES,
})
_KPT_RESOURCE_MAP = _KPT_RESOURCE_MAP_FROZEN


def validate_kcf1_error_enum_integrity_v1() -> None:
    """Reject ordinal drift in both KCF1 envelope enums."""
    logger.debug("validate_kcf1_error_enum_integrity_v1 entry")
    if (
        globals().get("_DECODE_CODES") is not _DECODE_CODES_FROZEN
        or globals().get("_RESOURCE_KINDS") is not _RESOURCE_KINDS_FROZEN
        or len(_DECODE_CODES_FROZEN) != 11 or len(_RESOURCE_KINDS_FROZEN) != 7
        or any(
            type(code) is not KCF1DecodeCodeV1
            or code is not KCF1DecodeCodeV1(index)
            or object.__getattribute__(code, "_value_") != index
            for index, code in enumerate(_DECODE_CODES_FROZEN)
        )
        or any(
            type(kind) is not KCF1ResourceKindV1
            or kind is not KCF1ResourceKindV1(index)
            or object.__getattribute__(kind, "_value_") != index
            for index, kind in enumerate(_RESOURCE_KINDS_FROZEN)
        )
    ):
        _host_error("kcf1-error-enum-integrity")
    logger.debug("validate_kcf1_error_enum_integrity_v1 exit")


def decode_code_ordinal_v1(code: KCF1DecodeCodeV1) -> int:
    """Return a frozen KCF1 decode ordinal."""
    logger.debug("decode_code_ordinal_v1 entry")
    validate_kcf1_error_enum_integrity_v1()
    if type(code) is not KCF1DecodeCodeV1:
        _host_error("decode-code-type")
    result = _DECODE_CODES.index(code)
    logger.debug("decode_code_ordinal_v1 exit ordinal=%d", result)
    return result


class KCF1DecodeError(ValueError):
    """Lowest-offset canonical KCF1 wire failure."""

    def __init__(self, code: KCF1DecodeCodeV1, offset: int) -> None:
        logger.error("KCF1 decode rejected code=%s offset=%d", code.name, offset)
        self.code = code
        self.offset = offset
        super().__init__(f"{code.name}@{offset}")


class KCF1ResourceLimit(ValueError):
    """Bounded-attempt refusal, never a mathematical rejection."""

    def __init__(self, kind: KCF1ResourceKindV1, offset: int) -> None:
        logger.error("KCF1 resource refused kind=%s offset=%d", kind.name, offset)
        self.kind = kind
        self.offset = offset
        super().__init__(f"{kind.name}@{offset}")


@dataclass(frozen=True, slots=True)
class KCF1LimitsV1:
    max_input_bytes: int = 1_048_576
    max_output_bytes: int = 1_048_576
    max_depth: int = KCF1_MAX_SAFE_DEPTH
    max_nodes: int = 10_000
    max_nested_kpt_bytes: int = 1_048_576
    max_kpt_list_items: int = 4096
    max_kpt_nat_bytes: int = 64

    def __post_init__(self) -> None:
        logger.debug("KCF1LimitsV1.__post_init__ entry")
        values = (
            self.max_input_bytes, self.max_output_bytes, self.max_depth,
            self.max_nodes, self.max_nested_kpt_bytes,
            self.max_kpt_list_items, self.max_kpt_nat_bytes,
        )
        if any(type(value) is not int or value <= 0 for value in values):
            logger.error("KCF1LimitsV1.__post_init__ error positive")
            raise ValueError("KCF1 limits must be exact positive integers")
        if self.max_depth > KCF1_MAX_SAFE_DEPTH:
            logger.error("KCF1LimitsV1.__post_init__ error unsafe-depth")
            raise ValueError("KCF1 max_depth exceeds safe recursion depth")
        logger.debug("KCF1LimitsV1.__post_init__ exit")


DEFAULT_KCF1_LIMITS_V1 = KCF1LimitsV1()
_LIMIT_NAMES = (
    "max_input_bytes", "max_output_bytes", "max_depth", "max_nodes",
    "max_nested_kpt_bytes", "max_kpt_list_items", "max_kpt_nat_bytes",
)
_LIMIT_SLOTS = tuple(vars(KCF1LimitsV1)[name] for name in _LIMIT_NAMES)


class _SlotDescriptor(Protocol):
    def __get__(self, instance: object, owner: type[object]) -> object: ...


def _decode_error(code: KCF1DecodeCodeV1, offset: int) -> NoReturn:
    logger.debug("_decode_error entry code=%s offset=%d", code.name, offset)
    raise KCF1DecodeError(code, offset)


def _resource(kind: KCF1ResourceKindV1, offset: int = 0) -> NoReturn:
    logger.debug("_resource entry kind=%s offset=%d", kind.name, offset)
    raise KCF1ResourceLimit(kind, offset)


def _host_error(reason: str) -> NoReturn:
    logger.error("KCF1 host/integrity rejected reason=%s", reason)
    raise ValueError(reason)


def _map_kpt_resource_v1(exc: object, base: int, expected: type[object]) -> NoReturn:
    """Translate one exact KPT resource envelope without mutable map authority."""
    logger.debug("_map_kpt_resource_v1 entry base=%d", base)
    if type(exc) is not expected:
        _host_error("nested-kpt-resource-type")
    name = object.__getattribute__(exc, "limit")
    offset = object.__getattribute__(exc, "offset")
    if (
        globals().get("_KPT_RESOURCE_MAP") is not _KPT_RESOURCE_MAP_FROZEN
        or type(name) is not str or name not in _KPT_RESOURCE_MAP_FROZEN
        or type(offset) is not int or offset < 0
    ):
        _host_error("nested-kpt-resource-integrity")
    _resource(_KPT_RESOURCE_MAP_FROZEN[name], base + offset)


def _u64(value: int) -> bytes:
    logger.debug("_u64 entry value=%d", value)
    result = value.to_bytes(8, "big")
    logger.debug("_u64 exit bytes=%d", len(result))
    return result


def _frame(payload: bytes) -> bytes:
    logger.debug("_frame entry bytes=%d", len(payload))
    result = _u64(len(payload)) + payload
    logger.debug("_frame exit bytes=%d", len(result))
    return result


def _slot(descriptor: object, value: object, label: str) -> object:
    logger.debug("_slot entry label=%s", label)
    try:
        result = cast(_SlotDescriptor, descriptor).__get__(value, type(value))
    except Exception as exc:
        logger.error("_slot error label=%s exception=%s", label, type(exc).__name__)
        raise ValueError(f"invalid-{label}") from None
    logger.debug("_slot exit label=%s", label)
    return result


def _snapshot_limits(value: KCF1LimitsV1) -> tuple[int, ...]:
    logger.debug("_snapshot_limits entry")
    if type(value) is not KCF1LimitsV1 or any(
        vars(KCF1LimitsV1).get(name) is not descriptor
        for name, descriptor in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True)
    ):
        _host_error("limits-host-shape")
    raw = tuple(
        _slot(descriptor, value, name)
        for name, descriptor in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True)
    )
    if any(type(item) is not int or item <= 0 for item in raw):
        _host_error("limits-host-shape")
    result = cast(tuple[int, ...], raw)
    if result[MAX_DEPTH] > KCF1_MAX_SAFE_DEPTH:
        _host_error("limits-unsafe-depth")
    logger.debug("_snapshot_limits exit")
    return result
