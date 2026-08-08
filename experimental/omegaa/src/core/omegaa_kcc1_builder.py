"""Captured allocation-free reconstruction for the sole KCC1 singleton."""

from __future__ import annotations

import logging

from . import omegaa_kcc1_common as _common
from . import omegaa_kcc1_types as _syntax

logger = logging.getLogger(__name__)
_LOGGER = logger
_SYNTAX_MODULE = _syntax
_COMMON_MODULE = _common
_CONFIG_CLASS = _syntax.EmptyCheckerConfigV1
_SINGLETON = _syntax.EMPTY_CHECKER_CONFIG_V1
_CONFIG_NAMESPACE = vars(_CONFIG_CLASS)
_CONFIG_KEYS = frozenset(_CONFIG_NAMESPACE)
_CONFIG_SLOTS = _CONFIG_NAMESPACE["__slots__"]
_CONFIG_INIT = _CONFIG_NAMESPACE["__init__"]
_CONFIG_INIT_CODE = _CONFIG_INIT.__code__
_CONFIG_FINAL = _CONFIG_NAMESPACE.get("__final__")
_SYNTAX_LOGGER = _syntax.logger
_COMMON_VALIDATE = _common.validate_kcc1_common_integrity_v1
_COMMON_VALIDATE_CODE = _COMMON_VALIDATE.__code__
_INTEGRITY_ERROR = _common._integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__
_LIMITS_CLASS = _common.KCC1LimitsV1
_DEFAULT_LIMITS = _common.DEFAULT_KCC1_LIMITS_V1
_DECODE_CLASS = _common.KCC1DecodeCodeV1
_RESOURCE_CLASS = _common.KCC1ResourceKindV1


def validate_kcc1_builder_integrity_v1() -> None:
    """Refuse module, class, zero-slot, singleton, enum or limits drift."""
    _LOGGER.debug("validate_kcc1_builder_integrity_v1 entry")
    namespace = vars(_CONFIG_CLASS)
    syntax = vars(_SYNTAX_MODULE)
    common = vars(_COMMON_MODULE)
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("_syntax") is not _SYNTAX_MODULE
        or globals().get("_common") is not _COMMON_MODULE
        or syntax.get("EmptyCheckerConfigV1") is not _CONFIG_CLASS
        or syntax.get("EMPTY_CHECKER_CONFIG_V1") is not _SINGLETON
        or syntax.get("logger") is not _SYNTAX_LOGGER
        or type(_SINGLETON) is not _CONFIG_CLASS
        or frozenset(namespace) != _CONFIG_KEYS
        or namespace.get("__slots__") is not _CONFIG_SLOTS
        or _CONFIG_SLOTS != ()
        or namespace.get("__init__") is not _CONFIG_INIT
        or _CONFIG_INIT.__code__ is not _CONFIG_INIT_CODE
        or "__post_init__" in namespace
        or namespace.get("__final__") is not _CONFIG_FINAL
        or _CONFIG_FINAL is not True
        or common.get("validate_kcc1_common_integrity_v1") is not _COMMON_VALIDATE
        or _COMMON_VALIDATE.__code__ is not _COMMON_VALIDATE_CODE
        or common.get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or common.get("KCC1LimitsV1") is not _LIMITS_CLASS
        or common.get("DEFAULT_KCC1_LIMITS_V1") is not _DEFAULT_LIMITS
        or common.get("KCC1DecodeCodeV1") is not _DECODE_CLASS
        or common.get("KCC1ResourceKindV1") is not _RESOURCE_CLASS
    )
    if drift:
        _LOGGER.error("validate_kcc1_builder_integrity_v1 error drift")
        _INTEGRITY_ERROR("kcc1-builder-integrity")
    _COMMON_VALIDATE()
    _LOGGER.debug("validate_kcc1_builder_integrity_v1 exit")


_VALIDATE_LOCAL = validate_kcc1_builder_integrity_v1
_VALIDATE_LOCAL_CODE = _VALIDATE_LOCAL.__code__


def build_empty_checker_config_v1() -> _syntax.EmptyCheckerConfigV1:
    """Return the captured singleton without allocation or Python hooks."""
    _LOGGER.debug("build_empty_checker_config_v1 entry")
    if (
        globals().get("validate_kcc1_builder_integrity_v1") is not _VALIDATE_LOCAL
        or _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
    ):
        _INTEGRITY_ERROR("kcc1-builder-validator-integrity")
    _VALIDATE_LOCAL()
    _LOGGER.debug("build_empty_checker_config_v1 exit")
    return _SINGLETON
