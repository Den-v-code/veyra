"""Exact private KCF1 continuation-frame syntax; no transition semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from types import MappingProxyType
from typing import NoReturn

from .omegaa_kpt1_types import KernelProofTermV1

logger = logging.getLogger(__name__)


class KCF1ValidationError(ValueError):
    """Raised when a host value is not exact KCF1 syntax."""


class KernelContinuationTagV1(IntEnum):
    """Frozen eight-tag KCF1 grammar."""

    PARSE_TERM = 0
    INFER_EXPECTED_SORT = 1
    INFER_TERM = 2
    NORMALIZE_EXPECTED = 3
    NORMALIZE_INFERRED = 4
    COMPARE_TYPES = 5
    NORMALIZE_VALUE = 6
    RETURN_TYPED = 7


_FIELD_KINDS = MappingProxyType({
    KernelContinuationTagV1.PARSE_TERM: ("term_bytes", "term"),
    KernelContinuationTagV1.INFER_EXPECTED_SORT: ("term", "term"),
    KernelContinuationTagV1.INFER_TERM: ("term", "term"),
    KernelContinuationTagV1.NORMALIZE_EXPECTED: ("term", "term", "term"),
    KernelContinuationTagV1.NORMALIZE_INFERRED: ("term", "term", "term"),
    KernelContinuationTagV1.COMPARE_TYPES: ("term", "term", "term"),
    KernelContinuationTagV1.NORMALIZE_VALUE: ("kernel_type_id",),
    KernelContinuationTagV1.RETURN_TYPED: ("kernel_type_id",),
})
_ARITIES = MappingProxyType({tag: len(kinds) for tag, kinds in _FIELD_KINDS.items()})
KCF1_FIELD_KINDS = _FIELD_KINDS
KCF1_ARITIES = _ARITIES
_TAGS = tuple(KernelContinuationTagV1(index) for index in range(8))
_TAG_ORDINALS = MappingProxyType({tag: index for index, tag in enumerate(_TAGS)})


def _reject(reason: str) -> NoReturn:
    logger.error("KCF1 syntax rejected reason=%s", reason)
    raise KCF1ValidationError(reason)


def validate_kcf1_enum_integrity_v1() -> None:
    """Reject live continuation-tag ordinal drift."""
    logger.debug("validate_kcf1_enum_integrity_v1 entry")
    if any(tag.value != ordinal for tag, ordinal in _TAG_ORDINALS.items()):
        _reject("tag-enum-ordinal-integrity")
    logger.debug("validate_kcf1_enum_integrity_v1 exit")


def kcf1_tag_ordinal_v1(tag: KernelContinuationTagV1) -> int:
    """Return one frozen tag ordinal without trusting its live value."""
    logger.debug("kcf1_tag_ordinal_v1 entry")
    validate_kcf1_enum_integrity_v1()
    if type(tag) is not KernelContinuationTagV1:
        _reject("tag-type")
    result = _TAG_ORDINALS[tag]
    logger.debug("kcf1_tag_ordinal_v1 exit ordinal=%d", result)
    return result


def kcf1_tag_from_ordinal_v1(ordinal: int) -> KernelContinuationTagV1:
    """Decode one frozen KCF1 tag ordinal."""
    logger.debug("kcf1_tag_from_ordinal_v1 entry")
    validate_kcf1_enum_integrity_v1()
    if type(ordinal) is not int or not 0 <= ordinal < len(_TAGS):
        _reject("tag-ordinal")
    result = _TAGS[ordinal]
    logger.debug("kcf1_tag_from_ordinal_v1 exit")
    return result


@dataclass(frozen=True, slots=True)
class KernelContinuationFrameV1:
    """One inert frame from the exact reviewed KCF1 dependent sum."""

    tag: KernelContinuationTagV1
    fields: tuple[object, ...]

    def __post_init__(self) -> None:
        logger.debug("KernelContinuationFrameV1.__post_init__ entry")
        validate_kcf1_enum_integrity_v1()
        if type(self.tag) is not KernelContinuationTagV1 or type(self.fields) is not tuple:
            _reject("frame-host-shape")
        kinds = _FIELD_KINDS[self.tag]
        if len(self.fields) != len(kinds):
            _reject("frame-arity")
        for position, (kind, value) in enumerate(zip(kinds, self.fields, strict=True)):
            valid = (
                (kind == "term" and type(value) is KernelProofTermV1)
                or (kind == "term_bytes" and type(value) is bytes)
                or (kind == "kernel_type_id" and type(value) is bytes and len(value) == 32)
            )
            if not valid:
                _reject(f"field-{position}-{kind}")
        logger.debug("KernelContinuationFrameV1.__post_init__ exit arity=%d", len(kinds))


def kernel_continuation_frame_v1(
    tag: KernelContinuationTagV1, *fields: object,
) -> KernelContinuationFrameV1:
    """Construct inert syntax only; this does not execute or check a term."""
    logger.debug("kernel_continuation_frame_v1 entry fields=%d", len(fields))
    result = KernelContinuationFrameV1(tag, tuple(fields))
    logger.debug("kernel_continuation_frame_v1 exit tag=%s", result.tag.name)
    return result
