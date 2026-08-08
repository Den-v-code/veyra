"""Exact non-executing KCA1 checker-program syntax for reviewed P3-ΩA."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from types import MappingProxyType
from typing import NoReturn
import unicodedata

from .omegaa_kca1_common import KCA1DecodeCodeV1

logger = logging.getLogger(__name__)


class KCA1ValidationError(ValueError):
    """Raised when a host value is not exact private KCA1 syntax."""


class KernelCheckerTagV1(IntEnum):
    """Frozen eight-tag KCA1 checker-program grammar."""

    PROGRAM = 0
    PARSE_CANON = 1
    INFER_MATCH = 2
    CHECK = 3
    NORMALIZE_STEP = 4
    ENTRY = 5
    RETURN = 6
    FAIL = 7


class ParseModeV1(IntEnum):
    CANON_FRAME_LTR_EXACT_END = 0


class ChildOrderV1(IntEnum):
    PROPER_CHILDREN_LTR = 0


class DeltaOrderV1(IntEnum):
    STRICT_LOWER_FINITE_RANK = 0


class FamilyOrderV1(IntEnum):
    STRICT_POSITIVE_STRUCTURAL_REC = 0


class QuoteModeV1(IntEnum):
    ETA_LONG_DEBRUIJN_LEVEL = 0


class EqualityModeV1(IntEnum):
    UNSIGNED_EXACT_BYTES = 0


class RedexOrderV1(IntEnum):
    LEFTMOST_OUTERMOST_BETA_ZETA_FST_SND_IOTA_DELTA_ETA = 0


class ParseOrderV1(IntEnum):
    EXPECTED_THEN_TERM = 0


class ContextModeV1(IntEnum):
    CLOSED = 0


class TypeCheckModeV1(IntEnum):
    INFERRED_TYPE_ID_EQUALS_EXPECTED_TYPE_ID = 0


class FunctionObligationModeV1(IntEnum):
    EXACT_TOTALITY_AND_EXTENSIONALITY_APPS = 0


class TerminalModeV1(IntEnum):
    ACCEPT_OR_FIRST_FAIL = 0


_MODE_TYPES = MappingProxyType({
    "parse_mode": ParseModeV1, "child_order": ChildOrderV1,
    "delta_order": DeltaOrderV1, "family_order": FamilyOrderV1,
    "quote_mode": QuoteModeV1, "equality_mode": EqualityModeV1,
    "redex_order": RedexOrderV1, "parse_order": ParseOrderV1,
    "context_mode": ContextModeV1, "type_check_mode": TypeCheckModeV1,
    "function_obligation_mode": FunctionObligationModeV1,
    "terminal_mode": TerminalModeV1,
})
_FIELD_KINDS = MappingProxyType({
    KernelCheckerTagV1.PROGRAM: ("ast", "ast", "ast", "ast", "ast"),
    KernelCheckerTagV1.PARSE_CANON: ("literal", "parse_mode"),
    KernelCheckerTagV1.INFER_MATCH: (
        "literal", "child_order", "delta_order", "family_order",
    ),
    KernelCheckerTagV1.CHECK: (
        "ast", "ast", "quote_mode", "equality_mode",
    ),
    KernelCheckerTagV1.NORMALIZE_STEP: (
        "literal", "literal", "redex_order",
    ),
    KernelCheckerTagV1.ENTRY: (
        "parse_order", "context_mode", "type_check_mode",
        "function_obligation_mode", "terminal_mode",
    ),
    KernelCheckerTagV1.RETURN: ("u8", "bytes"),
    KernelCheckerTagV1.FAIL: ("decode_code", "nat"),
})
_ARITIES = MappingProxyType({tag: len(row) for tag, row in _FIELD_KINDS.items()})
KCA1_FIELD_KINDS = _FIELD_KINDS
KCA1_ARITIES = _ARITIES
_TAGS = tuple(KernelCheckerTagV1(index) for index in range(8))
_TAG_ORDINALS = MappingProxyType({tag: index for index, tag in enumerate(_TAGS)})
_MODE_ROWS = tuple(
    (mode_type, tuple(mode_type)[0]) for mode_type in _MODE_TYPES.values()
)


def _reject(reason: str) -> NoReturn:
    logger.error("KCA1 syntax rejected reason=%s", reason)
    raise KCA1ValidationError(reason)


def validate_kca1_enum_integrity_v1() -> None:
    """Reject live checker-tag or one-member mode ordinal drift."""
    logger.debug("validate_kca1_enum_integrity_v1 entry")
    if any(tag.value != ordinal for tag, ordinal in _TAG_ORDINALS.items()):
        _reject("tag-enum-ordinal-integrity")
    if any(len(mode_type) != 1 or member.value != 0 for mode_type, member in _MODE_ROWS):
        _reject("mode-enum-ordinal-integrity")
    logger.debug("validate_kca1_enum_integrity_v1 exit")


def kca1_tag_ordinal_v1(tag: KernelCheckerTagV1) -> int:
    """Return the frozen checker tag ordinal, never a live enum value."""
    logger.debug("kca1_tag_ordinal_v1 entry")
    validate_kca1_enum_integrity_v1()
    if type(tag) is not KernelCheckerTagV1:
        _reject("tag-type")
    result = _TAG_ORDINALS[tag]
    logger.debug("kca1_tag_ordinal_v1 exit ordinal=%d", result)
    return result


def kca1_tag_from_ordinal_v1(ordinal: int) -> KernelCheckerTagV1:
    """Decode one frozen checker tag ordinal."""
    logger.debug("kca1_tag_from_ordinal_v1 entry")
    validate_kca1_enum_integrity_v1()
    if type(ordinal) is not int or not 0 <= ordinal < len(_TAGS):
        _reject("tag-ordinal")
    result = _TAGS[ordinal]
    logger.debug("kca1_tag_from_ordinal_v1 exit")
    return result


def kca1_mode_type_v1(kind: str) -> type[IntEnum]:
    """Return the private frozen one-member mode class for a grammar field."""
    logger.debug("kca1_mode_type_v1 entry kind=%s", kind)
    if type(kind) is not str or kind not in _MODE_TYPES:
        _reject("mode-kind")
    result = _MODE_TYPES[kind]
    logger.debug("kca1_mode_type_v1 exit")
    return result


def _literal_ok(value: object) -> bool:
    logger.debug("_literal_ok entry")
    if type(value) is not bytes:
        logger.debug("_literal_ok exit result=false")
        return False
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        logger.debug("_literal_ok exit result=false")
        return False
    result = unicodedata.normalize("NFC", text) == text
    logger.debug("_literal_ok exit result=%s", result)
    return result


@dataclass(frozen=True, slots=True)
class KernelCheckerASTV1:
    """Literal dependent sum of exactly the eight reviewed KCA1 tags."""

    tag: KernelCheckerTagV1
    fields: tuple[object, ...]

    def __post_init__(self) -> None:
        logger.debug("KernelCheckerASTV1.__post_init__ entry")
        validate_kca1_enum_integrity_v1()
        if type(self.tag) is not KernelCheckerTagV1 or type(self.fields) is not tuple:
            _reject("ast-host-shape")
        kinds = _FIELD_KINDS[self.tag]
        if len(self.fields) != len(kinds):
            _reject("ast-arity")
        for position, (kind, value) in enumerate(zip(kinds, self.fields, strict=True)):
            valid = (
                (kind == "ast" and type(value) is KernelCheckerASTV1)
                or (kind == "literal" and _literal_ok(value))
                or (kind == "bytes" and type(value) is bytes)
                or (kind == "u8" and type(value) is int and 0 <= value <= 255)
                or (kind == "nat" and type(value) is int and value >= 0)
                or (kind == "decode_code" and type(value) is KCA1DecodeCodeV1)
                or (kind in _MODE_TYPES and type(value) is _MODE_TYPES[kind])
            )
            if not valid:
                _reject(f"field-{position}-{kind}")
        logger.debug("KernelCheckerASTV1.__post_init__ exit arity=%d", len(kinds))


def kernel_checker_ast_v1(
    tag: KernelCheckerTagV1, *fields: object,
) -> KernelCheckerASTV1:
    """Construct syntax only; this grants no checker or proof capability."""
    logger.debug("kernel_checker_ast_v1 entry fields=%d", len(fields))
    result = KernelCheckerASTV1(tag, tuple(fields))
    logger.debug("kernel_checker_ast_v1 exit tag=%s", result.tag.name)
    return result
