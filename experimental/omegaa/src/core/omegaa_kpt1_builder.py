"""Captured fail-closed reconstruction for already validated KPT1 syntax."""

from __future__ import annotations

import logging
from typing import Protocol, cast

from . import omegaa_kpt1_types as _syntax

logger = logging.getLogger(__name__)
_TERM_CLASS = _syntax.KernelProofTermV1
_LEVEL_CLASS = _syntax.KernelUniverseLevelV1
_TERM_TAG_CLASS = _syntax.KernelTermTagV1
_LEVEL_TAG_CLASS = _syntax.KernelLevelTagV1
_TERM_INIT = vars(_TERM_CLASS)["__init__"]
_TERM_POST_INIT = vars(_TERM_CLASS)["__post_init__"]
_TERM_INIT_CODE = _TERM_INIT.__code__
_TERM_POST_INIT_CODE = _TERM_POST_INIT.__code__
_TERM_TAG_SLOT = vars(_TERM_CLASS)["tag"]
_TERM_FIELDS_SLOT = vars(_TERM_CLASS)["fields"]
_LEVEL_INIT = vars(_LEVEL_CLASS)["__init__"]
_LEVEL_POST_INIT = vars(_LEVEL_CLASS)["__post_init__"]
_LEVEL_INIT_CODE = _LEVEL_INIT.__code__
_LEVEL_POST_INIT_CODE = _LEVEL_POST_INIT.__code__
_LEVEL_TAG_SLOT = vars(_LEVEL_CLASS)["tag"]
_LEVEL_FIELDS_SLOT = vars(_LEVEL_CLASS)["fields"]
_VALIDATE_ENUM = _syntax.validate_kpt1_enum_integrity_v1
_LEVEL_ARITY = _syntax.kpt1_level_arity_v1
_REJECT = _syntax._reject
_FIELD_KINDS = _syntax._KPT1_FIELD_KINDS
_TERM_ORDINALS = _syntax._TERM_ORDINALS
_LEVEL_ORDINALS = _syntax._LEVEL_ORDINALS
_LEVEL_ARITIES = _syntax._LEVEL_ARITIES
_SYNTAX_LOGGER = _syntax.logger
_OBJECT_NEW = object.__new__


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def _validate_builder_integrity(term_alias: object, level_alias: object) -> None:
    logger.debug("_validate_builder_integrity entry")
    module = vars(_syntax)
    term_namespace = vars(_TERM_CLASS)
    level_namespace = vars(_LEVEL_CLASS)
    module_expected = (
        ("KernelProofTermV1", _TERM_CLASS),
        ("KernelUniverseLevelV1", _LEVEL_CLASS),
        ("KernelTermTagV1", _TERM_TAG_CLASS),
        ("KernelLevelTagV1", _LEVEL_TAG_CLASS),
        ("validate_kpt1_enum_integrity_v1", _VALIDATE_ENUM),
        ("kpt1_level_arity_v1", _LEVEL_ARITY),
        ("_reject", _REJECT),
        ("_KPT1_FIELD_KINDS", _FIELD_KINDS),
        ("_TERM_ORDINALS", _TERM_ORDINALS),
        ("_LEVEL_ORDINALS", _LEVEL_ORDINALS),
        ("_LEVEL_ARITIES", _LEVEL_ARITIES),
        ("logger", _SYNTAX_LOGGER),
    )
    drift = (
        term_alias is not _TERM_CLASS
        or level_alias is not _LEVEL_CLASS
        or any(module.get(name) is not expected for name, expected in module_expected)
        or term_namespace.get("__init__") is not _TERM_INIT
        or term_namespace.get("__post_init__") is not _TERM_POST_INIT
        or _TERM_INIT.__code__ is not _TERM_INIT_CODE
        or _TERM_POST_INIT.__code__ is not _TERM_POST_INIT_CODE
        or term_namespace.get("tag") is not _TERM_TAG_SLOT
        or term_namespace.get("fields") is not _TERM_FIELDS_SLOT
        or level_namespace.get("__init__") is not _LEVEL_INIT
        or level_namespace.get("__post_init__") is not _LEVEL_POST_INIT
        or _LEVEL_INIT.__code__ is not _LEVEL_INIT_CODE
        or _LEVEL_POST_INIT.__code__ is not _LEVEL_POST_INIT_CODE
        or level_namespace.get("tag") is not _LEVEL_TAG_SLOT
        or level_namespace.get("fields") is not _LEVEL_FIELDS_SLOT
    )
    if drift:
        logger.error("_validate_builder_integrity error drift")
        raise ValueError("kpt1-parser-constructor-integrity")
    logger.debug("_validate_builder_integrity exit")


def build_level_v1(
    tag: _syntax.KernelLevelTagV1,
    fields: tuple[_syntax.KernelUniverseLevelV1, ...],
    term_alias: object,
    level_alias: object,
) -> _syntax.KernelUniverseLevelV1:
    """Allocate one preflighted level without executing any Python class hook."""
    logger.debug("build_level_v1 entry")
    _validate_builder_integrity(term_alias, level_alias)
    result = _OBJECT_NEW(_LEVEL_CLASS)
    cast(_SlotSetter, _LEVEL_TAG_SLOT).__set__(result, tag)
    cast(_SlotSetter, _LEVEL_FIELDS_SLOT).__set__(result, fields)
    logger.debug("build_level_v1 exit")
    return result


def build_term_v1(
    tag: _syntax.KernelTermTagV1,
    fields: tuple[object, ...],
    term_alias: object,
    level_alias: object,
) -> _syntax.KernelProofTermV1:
    """Allocate one preflighted term without executing any Python class hook."""
    logger.debug("build_term_v1 entry")
    _validate_builder_integrity(term_alias, level_alias)
    result = _OBJECT_NEW(_TERM_CLASS)
    cast(_SlotSetter, _TERM_TAG_SLOT).__set__(result, tag)
    cast(_SlotSetter, _TERM_FIELDS_SLOT).__set__(result, fields)
    logger.debug("build_term_v1 exit")
    return result
