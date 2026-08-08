"""Exact non-positive KPT1 term and universe-level syntax for reviewed P3-ΩA."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from types import MappingProxyType
from typing import NoReturn

logger = logging.getLogger(__name__)


class KPT1ValidationError(ValueError):
    """Raised when a host value is not an exact KPT1 syntax value."""


class KernelLevelTagV1(IntEnum):
    """Frozen KPT1 universe-level tags."""

    ZERO = 0
    SUCC = 1
    MAX = 2


class KernelTermTagV1(IntEnum):
    """Frozen KPT1 term tags in reviewed P3-ΩA order."""

    VAR = 0
    SORT = 1
    PI = 2
    LAM = 3
    APP = 4
    SIGMA = 5
    PAIR = 6
    FST = 7
    SND = 8
    LET = 9
    CONST = 10
    CTOR = 11
    REC = 12
    EQ = 13
    REFL = 14
    J = 15


_KPT1_FIELD_KINDS = MappingProxyType({
    KernelTermTagV1.VAR: ("nat",),
    KernelTermTagV1.SORT: ("level",),
    KernelTermTagV1.PI: ("term", "term"),
    KernelTermTagV1.LAM: ("term", "term"),
    KernelTermTagV1.APP: ("term", "term"),
    KernelTermTagV1.SIGMA: ("term", "term"),
    KernelTermTagV1.PAIR: ("term", "term"),
    KernelTermTagV1.FST: ("term",),
    KernelTermTagV1.SND: ("term",),
    KernelTermTagV1.LET: ("term", "term", "term"),
    KernelTermTagV1.CONST: ("digest",),
    KernelTermTagV1.CTOR: ("digest", "nat", "terms"),
    KernelTermTagV1.REC: ("digest", "term", "terms", "term"),
    KernelTermTagV1.EQ: ("term", "term", "term"),
    KernelTermTagV1.REFL: ("term",),
    KernelTermTagV1.J: ("term", "term", "term", "term", "term", "term"),
})
_KPT1_ARITIES = MappingProxyType(
    {tag: len(fields) for tag, fields in _KPT1_FIELD_KINDS.items()},
)
KPT1_FIELD_KINDS = _KPT1_FIELD_KINDS
KPT1_ARITIES = _KPT1_ARITIES
_TERM_BY_ORDINAL = tuple(KernelTermTagV1(index) for index in range(16))
_LEVEL_BY_ORDINAL = tuple(KernelLevelTagV1(index) for index in range(3))
_TERM_ORDINALS = MappingProxyType({tag: index for index, tag in enumerate(_TERM_BY_ORDINAL)})
_LEVEL_ORDINALS = MappingProxyType({tag: index for index, tag in enumerate(_LEVEL_BY_ORDINAL)})
_LEVEL_ARITIES = MappingProxyType({tag: index for index, tag in enumerate(_LEVEL_BY_ORDINAL)})


def _reject(reason: str) -> NoReturn:
    logger.error("KPT1 syntax rejected reason=%s", reason)
    raise KPT1ValidationError(reason)


def validate_kpt1_enum_integrity_v1() -> None:
    """Reject live IntEnum ordinal drift before any syntax or wire operation."""
    logger.debug("validate_kpt1_enum_integrity_v1 entry")
    if any(tag.value != ordinal for tag, ordinal in _TERM_ORDINALS.items()) or any(
        tag.value != ordinal for tag, ordinal in _LEVEL_ORDINALS.items()
    ):
        _reject("enum-ordinal-integrity")
    logger.debug("validate_kpt1_enum_integrity_v1 exit")


def kpt1_term_ordinal_v1(tag: KernelTermTagV1) -> int:
    """Return the frozen term ordinal, never a live enum value."""
    logger.debug("kpt1_term_ordinal_v1 entry")
    validate_kpt1_enum_integrity_v1()
    if type(tag) is not KernelTermTagV1:
        _reject("term-tag-type")
    result = _TERM_ORDINALS[tag]
    logger.debug("kpt1_term_ordinal_v1 exit ordinal=%d", result)
    return result


def kpt1_level_ordinal_v1(tag: KernelLevelTagV1) -> int:
    """Return the frozen level ordinal, never a live enum value."""
    logger.debug("kpt1_level_ordinal_v1 entry")
    validate_kpt1_enum_integrity_v1()
    if type(tag) is not KernelLevelTagV1:
        _reject("level-tag-type")
    result = _LEVEL_ORDINALS[tag]
    logger.debug("kpt1_level_ordinal_v1 exit ordinal=%d", result)
    return result


def kpt1_level_arity_v1(tag: KernelLevelTagV1) -> int:
    """Return frozen ZERO/SUCC/MAX arity."""
    logger.debug("kpt1_level_arity_v1 entry")
    validate_kpt1_enum_integrity_v1()
    if type(tag) is not KernelLevelTagV1:
        _reject("level-tag-type")
    result = _LEVEL_ARITIES[tag]
    logger.debug("kpt1_level_arity_v1 exit arity=%d", result)
    return result


def kpt1_term_tag_from_ordinal_v1(ordinal: int) -> KernelTermTagV1:
    """Decode one frozen term ordinal after global enum integrity pressure."""
    logger.debug("kpt1_term_tag_from_ordinal_v1 entry")
    validate_kpt1_enum_integrity_v1()
    if type(ordinal) is not int or not 0 <= ordinal < len(_TERM_BY_ORDINAL):
        _reject("term-tag-ordinal")
    result = _TERM_BY_ORDINAL[ordinal]
    logger.debug("kpt1_term_tag_from_ordinal_v1 exit")
    return result


def kpt1_level_tag_from_ordinal_v1(ordinal: int) -> KernelLevelTagV1:
    """Decode one frozen level ordinal after global enum integrity pressure."""
    logger.debug("kpt1_level_tag_from_ordinal_v1 entry")
    validate_kpt1_enum_integrity_v1()
    if type(ordinal) is not int or not 0 <= ordinal < len(_LEVEL_BY_ORDINAL):
        _reject("level-tag-ordinal")
    result = _LEVEL_BY_ORDINAL[ordinal]
    logger.debug("kpt1_level_tag_from_ordinal_v1 exit")
    return result


@dataclass(frozen=True, slots=True)
class KernelUniverseLevelV1:
    """Literal dependent sum ``ZERO | SUCC(level) | MAX(left,right)``."""

    tag: KernelLevelTagV1
    fields: tuple[KernelUniverseLevelV1, ...] = ()

    def __post_init__(self) -> None:
        logger.debug("KernelUniverseLevelV1.__post_init__ entry")
        if type(self.tag) is not KernelLevelTagV1 or type(self.fields) is not tuple:
            _reject("level-host-shape")
        expected = kpt1_level_arity_v1(self.tag)
        if len(self.fields) != expected:
            _reject("level-arity")
        if any(type(item) is not KernelUniverseLevelV1 for item in self.fields):
            _reject("level-child-type")
        logger.debug("KernelUniverseLevelV1.__post_init__ exit arity=%d", expected)


@dataclass(frozen=True, slots=True)
class KernelProofTermV1:
    """Literal tag-indexed dependent sum of the sixteen reviewed KPT1 nodes."""

    tag: KernelTermTagV1
    fields: tuple[object, ...]

    def __post_init__(self) -> None:
        logger.debug("KernelProofTermV1.__post_init__ entry")
        if type(self.tag) is not KernelTermTagV1 or type(self.fields) is not tuple:
            _reject("term-host-shape")
        validate_kpt1_enum_integrity_v1()
        kinds = _KPT1_FIELD_KINDS[self.tag]
        if len(self.fields) != len(kinds):
            _reject("term-arity")
        for position, (kind, value) in enumerate(zip(kinds, self.fields, strict=True)):
            if kind == "nat" and (type(value) is not int or value < 0):
                _reject(f"field-{position}-nat")
            if kind == "digest" and (type(value) is not bytes or len(value) != 32):
                _reject(f"field-{position}-digest")
            if kind == "level" and type(value) is not KernelUniverseLevelV1:
                _reject(f"field-{position}-level")
            if kind == "term" and type(value) is not KernelProofTermV1:
                _reject(f"field-{position}-term")
            if kind == "terms" and (
                type(value) is not tuple
                or any(type(item) is not KernelProofTermV1 for item in value)
            ):
                _reject(f"field-{position}-terms")
        logger.debug("KernelProofTermV1.__post_init__ exit arity=%d", len(kinds))


def zero_level_v1() -> KernelUniverseLevelV1:
    """Return the sole canonical ZERO universe level."""
    logger.debug("zero_level_v1 entry")
    result = KernelUniverseLevelV1(KernelLevelTagV1.ZERO)
    logger.debug("zero_level_v1 exit")
    return result


def succ_level_v1(level: KernelUniverseLevelV1) -> KernelUniverseLevelV1:
    """Return the exact SUCC level constructor."""
    logger.debug("succ_level_v1 entry")
    result = KernelUniverseLevelV1(KernelLevelTagV1.SUCC, (level,))
    logger.debug("succ_level_v1 exit")
    return result


def max_level_v1(
    left: KernelUniverseLevelV1, right: KernelUniverseLevelV1,
) -> KernelUniverseLevelV1:
    """Return the exact MAX level constructor."""
    logger.debug("max_level_v1 entry")
    result = KernelUniverseLevelV1(KernelLevelTagV1.MAX, (left, right))
    logger.debug("max_level_v1 exit")
    return result


def kernel_term_v1(tag: KernelTermTagV1, *fields: object) -> KernelProofTermV1:
    """Construct one exact tag-indexed KPT1 node without semantic capability."""
    logger.debug("kernel_term_v1 entry fields=%d", len(fields))
    result = KernelProofTermV1(tag, tuple(fields))
    logger.debug("kernel_term_v1 exit tag=%s", result.tag.name)
    return result
