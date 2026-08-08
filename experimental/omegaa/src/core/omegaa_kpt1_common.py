"""Shared exact errors and hostile-safe resource policy for private KPT1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from typing import NoReturn, Protocol, cast

logger = logging.getLogger(__name__)
KPT1_PREFIX = b"KPT1"
KPT1_MAX_SAFE_DEPTH = 128
MAX_INPUT, MAX_OUTPUT, MAX_DEPTH, MAX_NODES, MAX_LIST, MAX_NAT = range(6)


class KPT1DecodeCodeV1(IntEnum):
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


class KPT1DecodeError(ValueError):
    """First-offset canonical decoding failure."""

    def __init__(self, code: KPT1DecodeCodeV1, offset: int) -> None:
        logger.error("KPT1 decode rejected code=%s offset=%d", code.name, offset)
        self.code = code
        self.offset = offset
        super().__init__(f"{code.name}@{offset}")


class KPT1ResourceLimit(ValueError):
    """Hostile-input resource ceiling failure, separate from wire semantics."""

    def __init__(self, limit: str, offset: int) -> None:
        logger.error("KPT1 resource rejected limit=%s offset=%d", limit, offset)
        self.limit = limit
        self.offset = offset
        super().__init__(f"{limit}@{offset}")


@dataclass(frozen=True, slots=True)
class KPT1LimitsV1:
    max_input_bytes: int = 1_048_576
    max_output_bytes: int = 1_048_576
    max_depth: int = KPT1_MAX_SAFE_DEPTH
    max_nodes: int = 10_000
    max_list_items: int = 4096
    max_nat_bytes: int = 64

    def __post_init__(self) -> None:
        logger.debug("KPT1LimitsV1 validation entry")
        values = (
            self.max_input_bytes, self.max_output_bytes, self.max_depth,
            self.max_nodes, self.max_list_items, self.max_nat_bytes,
        )
        if any(type(value) is not int or value <= 0 for value in values):
            logger.error("KPT1LimitsV1 validation error positive")
            raise ValueError("KPT1 limits must be exact positive integers")
        if self.max_depth > KPT1_MAX_SAFE_DEPTH:
            logger.error("KPT1LimitsV1 validation error depth")
            raise ValueError("KPT1 max_depth exceeds safe recursion depth")
        logger.debug("KPT1LimitsV1 validation exit")


DEFAULT_KPT1_LIMITS_V1 = KPT1LimitsV1()
_LIMIT_NAMES = (
    "max_input_bytes", "max_output_bytes", "max_depth",
    "max_nodes", "max_list_items", "max_nat_bytes",
)
_LIMIT_SLOTS = tuple(vars(KPT1LimitsV1)[name] for name in _LIMIT_NAMES)


class _SlotDescriptor(Protocol):
    def __get__(self, instance: object, owner: type[object]) -> object: ...


def _resource(limit: str, offset: int = 0) -> NoReturn:
    logger.debug("_resource entry limit=%s offset=%d", limit, offset)
    raise KPT1ResourceLimit(limit, offset)


def _decode_error(code: KPT1DecodeCodeV1, offset: int) -> NoReturn:
    logger.debug("_decode_error entry code=%s offset=%d", code.name, offset)
    raise KPT1DecodeError(code, offset)


def _host_error(reason: str) -> NoReturn:
    logger.error("KPT1 host value rejected reason=%s", reason)
    raise ValueError(reason)


def _slot(descriptor: object, value: object, label: str) -> object:
    logger.debug("_slot entry label=%s", label)
    try:
        result = cast(_SlotDescriptor, descriptor).__get__(value, type(value))
    except Exception as exc:
        logger.error("_slot error label=%s exception=%s", label, type(exc).__name__)
        raise ValueError(f"invalid-{label}") from None
    logger.debug("_slot exit label=%s", label)
    return result


def _snapshot_limits(value: KPT1LimitsV1) -> tuple[int, ...]:
    logger.debug("_snapshot_limits entry")
    if type(value) is not KPT1LimitsV1 or any(
        vars(KPT1LimitsV1).get(name) is not descriptor
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
    if result[MAX_DEPTH] > KPT1_MAX_SAFE_DEPTH:
        _host_error("limits-unsafe-depth")
    logger.debug("_snapshot_limits exit")
    return result
