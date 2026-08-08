"""Bounded first-offset inverse parser for the inert KCC1 singleton."""

from __future__ import annotations

import logging

from . import omegaa_kcc1_types as _syntax
from .omegaa_kcc1_builder import (
    build_empty_checker_config_v1,
    validate_kcc1_builder_integrity_v1,
)
from .omegaa_kcc1_codec import codec_empty_checker_config_v1
from .omegaa_kcc1_common import (
    DEFAULT_KCC1_LIMITS_V1,
    KCC1_PREFIX,
    MAX_INPUT,
    MAX_OUTPUT,
    KCC1DecodeCodeV1,
    KCC1LimitsV1,
    KCC1ResourceKindV1,
    _decode_error,
    _integrity_error,
    _resource,
    _snapshot_limits,
    validate_kcc1_common_integrity_v1,
)
from .omegaa_kcc1_types import EMPTY_CHECKER_CONFIG_V1, EmptyCheckerConfigV1

logger = logging.getLogger(__name__)
_LOGGER = logger
_SYNTAX_MODULE = _syntax
_CONFIG_CLASS = EmptyCheckerConfigV1
_SINGLETON = EMPTY_CHECKER_CONFIG_V1
_BUILD = build_empty_checker_config_v1
_BUILD_CODE = _BUILD.__code__
_VALIDATE_BUILDER = validate_kcc1_builder_integrity_v1
_VALIDATE_BUILDER_CODE = _VALIDATE_BUILDER.__code__
_VALIDATE_COMMON = validate_kcc1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON.__code__
_INTEGRITY_ERROR = _integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__
_DECODE_CLASS = KCC1DecodeCodeV1
_RESOURCE_CLASS = KCC1ResourceKindV1
_MAX_INPUT = MAX_INPUT
_MAX_OUTPUT = MAX_OUTPUT
_DECODE_ERROR = _decode_error
_DECODE_ERROR_CODE = _DECODE_ERROR.__code__
_RESOURCE = _resource
_RESOURCE_CODE = _RESOURCE.__code__
_SNAPSHOT_LIMITS = _snapshot_limits
_SNAPSHOT_LIMITS_CODE = _SNAPSHOT_LIMITS.__code__
_CODEC = codec_empty_checker_config_v1
_CODEC_CODE = _CODEC.__code__
_PREFIX_FROZEN = KCC1_PREFIX


def _validate_parser_integrity_v1() -> None:
    _LOGGER.debug("_validate_parser_integrity_v1 entry")
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("_syntax") is not _SYNTAX_MODULE
        or vars(_SYNTAX_MODULE).get("EmptyCheckerConfigV1") is not _CONFIG_CLASS
        or vars(_SYNTAX_MODULE).get("EMPTY_CHECKER_CONFIG_V1") is not _SINGLETON
        or globals().get("EmptyCheckerConfigV1") is not _CONFIG_CLASS
        or globals().get("EMPTY_CHECKER_CONFIG_V1") is not _SINGLETON
        or globals().get("build_empty_checker_config_v1") is not _BUILD
        or _BUILD.__code__ is not _BUILD_CODE
        or globals().get("validate_kcc1_builder_integrity_v1") is not _VALIDATE_BUILDER
        or _VALIDATE_BUILDER.__code__ is not _VALIDATE_BUILDER_CODE
        or globals().get("validate_kcc1_common_integrity_v1") is not _VALIDATE_COMMON
        or _VALIDATE_COMMON.__code__ is not _VALIDATE_COMMON_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or globals().get("KCC1DecodeCodeV1") is not _DECODE_CLASS
        or globals().get("KCC1ResourceKindV1") is not _RESOURCE_CLASS
        or globals().get("MAX_INPUT") is not _MAX_INPUT
        or globals().get("MAX_OUTPUT") is not _MAX_OUTPUT
        or (_MAX_INPUT, _MAX_OUTPUT) != (0, 1)
        or globals().get("_decode_error") is not _DECODE_ERROR
        or _DECODE_ERROR.__code__ is not _DECODE_ERROR_CODE
        or globals().get("_resource") is not _RESOURCE
        or _RESOURCE.__code__ is not _RESOURCE_CODE
        or globals().get("_snapshot_limits") is not _SNAPSHOT_LIMITS
        or _SNAPSHOT_LIMITS.__code__ is not _SNAPSHOT_LIMITS_CODE
        or globals().get("codec_empty_checker_config_v1") is not _CODEC
        or _CODEC.__code__ is not _CODEC_CODE
        or globals().get("KCC1_PREFIX") is not _PREFIX_FROZEN
        or _PREFIX_FROZEN != b"KCC1"
    )
    if drift:
        _LOGGER.error("_validate_parser_integrity_v1 error drift")
        _INTEGRITY_ERROR("kcc1-parser-integrity")
    _VALIDATE_BUILDER()
    _VALIDATE_COMMON()
    _LOGGER.debug("_validate_parser_integrity_v1 exit")


_VALIDATE_LOCAL = _validate_parser_integrity_v1
_VALIDATE_LOCAL_CODE = _VALIDATE_LOCAL.__code__


def _check_prefix_v1(raw: bytes) -> None:
    _LOGGER.debug("_check_prefix_v1 entry bytes=%d", len(raw))
    available = min(len(raw), 4)
    for index in range(available):
        if raw[index] != _PREFIX_FROZEN[index]:
            code = _DECODE_CLASS.BAD_DOMAIN if index < 3 else _DECODE_CLASS.BAD_VERSION
            _DECODE_ERROR(code, index)
    if available < 4:
        _DECODE_ERROR(_DECODE_CLASS.BAD_LENGTH, available)
    _LOGGER.debug("_check_prefix_v1 exit")


_CHECK_PREFIX = _check_prefix_v1
_CHECK_PREFIX_CODE = _CHECK_PREFIX.__code__


def parse_empty_checker_config_v1(
    raw: bytes,
    limits: KCC1LimitsV1 = DEFAULT_KCC1_LIMITS_V1,
) -> EmptyCheckerConfigV1:
    """Parse exactly ``4b4343310000`` and return the captured singleton."""
    _LOGGER.debug("parse_empty_checker_config_v1 entry")
    if (
        globals().get("_validate_parser_integrity_v1") is not _VALIDATE_LOCAL
        or _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
    ):
        _INTEGRITY_ERROR("kcc1-parser-validator-integrity")
    _VALIDATE_LOCAL()
    if type(raw) is not bytes:
        _LOGGER.error("parse_empty_checker_config_v1 error raw-type")
        raise TypeError("raw must be exact bytes")
    values = _SNAPSHOT_LIMITS(limits)
    if (
        globals().get("_check_prefix_v1") is not _CHECK_PREFIX
        or _CHECK_PREFIX.__code__ is not _CHECK_PREFIX_CODE
    ):
        _INTEGRITY_ERROR("kcc1-prefix-checker-integrity")
    if len(raw) > values[_MAX_INPUT]:
        _RESOURCE(
            _RESOURCE_CLASS.INPUT_BYTES,
            values[_MAX_INPUT],
            len(raw),
            values[_MAX_INPUT],
        )
    _CHECK_PREFIX(raw)
    if len(raw) < 5:
        _DECODE_ERROR(_DECODE_CLASS.BAD_LENGTH, 4)
    if raw[4] != 0:
        _DECODE_ERROR(_DECODE_CLASS.BAD_TAG, 4)
    if len(raw) < 6:
        _DECODE_ERROR(_DECODE_CLASS.BAD_LENGTH, 5)
    if raw[5] != 0:
        _DECODE_ERROR(_DECODE_CLASS.BAD_ARITY, 5)
    if len(raw) > 6:
        _DECODE_ERROR(_DECODE_CLASS.TRAILING, 6)
    if 6 > values[_MAX_OUTPUT]:
        _RESOURCE(_RESOURCE_CLASS.OUTPUT_BYTES, values[_MAX_OUTPUT], 6, 0)
    result = _BUILD()
    if result is not _SINGLETON or _CODEC(result, limits) != raw:
        _LOGGER.error("parse_empty_checker_config_v1 error roundtrip-integrity")
        _INTEGRITY_ERROR("kcc1-roundtrip-integrity")
    _LOGGER.debug("parse_empty_checker_config_v1 exit")
    return result
