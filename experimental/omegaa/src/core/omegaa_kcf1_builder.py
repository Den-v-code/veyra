"""Captured hook-free reconstruction for preflighted KCF1 frames."""

from __future__ import annotations

import logging
from types import MemberDescriptorType
from typing import Protocol, cast

from . import omegaa_kcf1_types as _syntax

logger = logging.getLogger(__name__)
_FRAME_CLASS = _syntax.KernelContinuationFrameV1
_TAG_CLASS = _syntax.KernelContinuationTagV1
_FRAME_INIT = vars(_FRAME_CLASS)["__init__"]
_FRAME_POST_INIT = vars(_FRAME_CLASS)["__post_init__"]
_FRAME_INIT_CODE = _FRAME_INIT.__code__
_FRAME_POST_INIT_CODE = _FRAME_POST_INIT.__code__
_TAG_SLOT = vars(_FRAME_CLASS)["tag"]
_FIELDS_SLOT = vars(_FRAME_CLASS)["fields"]
_VALIDATE_ENUM = _syntax.validate_kcf1_enum_integrity_v1
_REJECT = _syntax._reject
_FIELD_KINDS = _syntax._FIELD_KINDS
_ARITIES = _syntax._ARITIES
_TAG_ORDINALS = _syntax._TAG_ORDINALS
_SYNTAX_LOGGER = _syntax.logger
_OBJECT_NEW = object.__new__


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def validate_kcf1_builder_integrity_v1(
    frame_alias: object = _FRAME_CLASS, tag_alias: object = _TAG_CLASS,
) -> None:
    """Refuse class, table, slot and generated-hook drift before allocation."""
    logger.debug("validate_kcf1_builder_integrity_v1 entry")
    module = vars(_syntax)
    namespace = vars(_FRAME_CLASS)
    expected = (
        ("KernelContinuationFrameV1", _FRAME_CLASS),
        ("KernelContinuationTagV1", _TAG_CLASS),
        ("validate_kcf1_enum_integrity_v1", _VALIDATE_ENUM),
        ("_reject", _REJECT), ("_FIELD_KINDS", _FIELD_KINDS),
        ("_ARITIES", _ARITIES), ("_TAG_ORDINALS", _TAG_ORDINALS),
        ("logger", _SYNTAX_LOGGER),
    )
    drift = (
        frame_alias is not _FRAME_CLASS or tag_alias is not _TAG_CLASS
        or any(module.get(name) is not value for name, value in expected)
        or namespace.get("__init__") is not _FRAME_INIT
        or namespace.get("__post_init__") is not _FRAME_POST_INIT
        or _FRAME_INIT.__code__ is not _FRAME_INIT_CODE
        or _FRAME_POST_INIT.__code__ is not _FRAME_POST_INIT_CODE
        or namespace.get("tag") is not _TAG_SLOT
        or namespace.get("fields") is not _FIELDS_SLOT
        or type(_TAG_SLOT) is not MemberDescriptorType
        or type(_FIELDS_SLOT) is not MemberDescriptorType
        or object.__new__ is not _OBJECT_NEW
    )
    if drift:
        logger.error("validate_kcf1_builder_integrity_v1 error drift")
        raise ValueError("kcf1-parser-constructor-integrity")
    logger.debug("validate_kcf1_builder_integrity_v1 exit")


def build_frame_v1(
    tag: _syntax.KernelContinuationTagV1,
    fields: tuple[object, ...],
    frame_alias: object,
    tag_alias: object,
) -> _syntax.KernelContinuationFrameV1:
    """Allocate one validated frame without invoking Python class hooks."""
    logger.debug("build_frame_v1 entry")
    validate_kcf1_builder_integrity_v1(frame_alias, tag_alias)
    result = _OBJECT_NEW(_FRAME_CLASS)
    cast(_SlotSetter, _TAG_SLOT).__set__(result, tag)
    cast(_SlotSetter, _FIELDS_SLOT).__set__(result, fields)
    logger.debug("build_frame_v1 exit")
    return result
