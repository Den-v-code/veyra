"""Bounded scan-first KCI1 parser with typed decode/resource results."""

from __future__ import annotations

import logging
from typing import TypeAlias

from . import omegaa_kci1_common as _common
from . import omegaa_kci1_types as _syntax
from .omegaa_kci1_builder import (
    _build_decode_error_result_v1,
    _build_decode_error_v1,
    _build_decoded_result_v1,
    _build_resource_parse_result_v1,
    _build_resource_result_v1,
    build_checker_input_syntax_v1,
    validate_kci1_builder_integrity_v1,
)
from .omegaa_kci1_codec import codec_checker_input_syntax_v1
from .omegaa_kci1_common import (
    DEFAULT_KCI1_LIMITS_V1,
    KCI1_PREFIX,
    MAX_EXPECTED,
    MAX_INPUT,
    MAX_OUTPUT,
    MAX_TERM,
    U64_LIMIT,
    KCI1DecodeCodeV1,
    KCI1LimitsV1,
    KCI1ResourceKindV1,
    _integrity_error,
    _snapshot_limits,
    validate_kci1_common_integrity_v1,
)

logger = logging.getLogger(__name__)
_LOGGER = logger
_COMMON_MODULE = _common
_SYNTAX_MODULE = _syntax
_PREFIX_FROZEN = KCI1_PREFIX
_DECODE_CLASS = KCI1DecodeCodeV1
_RESOURCE_CLASS = KCI1ResourceKindV1
_LIMITS_CLASS = KCI1LimitsV1
_DEFAULT_LIMITS = DEFAULT_KCI1_LIMITS_V1
_MAX_INPUT = MAX_INPUT
_MAX_OUTPUT = MAX_OUTPUT
_MAX_EXPECTED = MAX_EXPECTED
_MAX_TERM = MAX_TERM
_U64_LIMIT = U64_LIMIT
_U64_LIMIT_FROZEN = 18_446_744_073_709_551_616
_VALIDATE_COMMON = validate_kci1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON.__code__
_VALIDATE_BUILDER = validate_kci1_builder_integrity_v1
_VALIDATE_BUILDER_CODE = _VALIDATE_BUILDER.__code__
_INTEGRITY_ERROR = _integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__
_SNAPSHOT_LIMITS = _snapshot_limits
_SNAPSHOT_LIMITS_CODE = _SNAPSHOT_LIMITS.__code__
_BUILD_INPUT = build_checker_input_syntax_v1
_BUILD_INPUT_CODE = _BUILD_INPUT.__code__
_BUILD_DECODE_ERROR = _build_decode_error_v1
_BUILD_DECODE_ERROR_CODE = _BUILD_DECODE_ERROR.__code__
_BUILD_RESOURCE = _build_resource_result_v1
_BUILD_RESOURCE_CODE = _BUILD_RESOURCE.__code__
_BUILD_DECODED_RESULT = _build_decoded_result_v1
_BUILD_DECODED_RESULT_CODE = _BUILD_DECODED_RESULT.__code__
_BUILD_DECODE_RESULT = _build_decode_error_result_v1
_BUILD_DECODE_RESULT_CODE = _BUILD_DECODE_RESULT.__code__
_BUILD_RESOURCE_RESULT = _build_resource_parse_result_v1
_BUILD_RESOURCE_RESULT_CODE = _BUILD_RESOURCE_RESULT.__code__
_CODEC = codec_checker_input_syntax_v1
_CODEC_CODE = _CODEC.__code__
_Candidate: TypeAlias = tuple[KCI1DecodeCodeV1, int]
_Scan: TypeAlias = tuple[
    tuple[_Candidate, ...],
    tuple[_Candidate, ...],
    int | None,
    int | None,
    int | None,
    int | None,
]


def _validate_parser_integrity_v1() -> None:
    _LOGGER.debug("_validate_parser_integrity_v1 entry")
    common = vars(_COMMON_MODULE)
    syntax = vars(_SYNTAX_MODULE)
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("_common") is not _COMMON_MODULE
        or globals().get("_syntax") is not _SYNTAX_MODULE
        or globals().get("KCI1DecodeCodeV1") is not _DECODE_CLASS
        or globals().get("KCI1ResourceKindV1") is not _RESOURCE_CLASS
        or globals().get("KCI1LimitsV1") is not _LIMITS_CLASS
        or globals().get("DEFAULT_KCI1_LIMITS_V1") is not _DEFAULT_LIMITS
        or common.get("KCI1DecodeCodeV1") is not _DECODE_CLASS
        or common.get("KCI1ResourceKindV1") is not _RESOURCE_CLASS
        or type(common.get("U64_LIMIT")) is not int
        or common.get("U64_LIMIT") != 18_446_744_073_709_551_616
        or syntax.get("CheckerInputSyntaxV1") is not _syntax.CheckerInputSyntaxV1
        or globals().get("KCI1_PREFIX") is not _PREFIX_FROZEN
        or _PREFIX_FROZEN != b"KCI1"
        or type(globals().get("U64_LIMIT")) is not int
        or globals().get("U64_LIMIT") != 18_446_744_073_709_551_616
        or type(_U64_LIMIT) is not int
        or _U64_LIMIT != 18_446_744_073_709_551_616
        or type(_U64_LIMIT_FROZEN) is not int
        or _U64_LIMIT_FROZEN != 18_446_744_073_709_551_616
        or (_MAX_INPUT, _MAX_OUTPUT, _MAX_EXPECTED, _MAX_TERM) != (0, 1, 2, 3)
        or globals().get("validate_kci1_common_integrity_v1") is not _VALIDATE_COMMON
        or _VALIDATE_COMMON.__code__ is not _VALIDATE_COMMON_CODE
        or globals().get("validate_kci1_builder_integrity_v1") is not _VALIDATE_BUILDER
        or _VALIDATE_BUILDER.__code__ is not _VALIDATE_BUILDER_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or globals().get("_snapshot_limits") is not _SNAPSHOT_LIMITS
        or _SNAPSHOT_LIMITS.__code__ is not _SNAPSHOT_LIMITS_CODE
        or globals().get("build_checker_input_syntax_v1") is not _BUILD_INPUT
        or _BUILD_INPUT.__code__ is not _BUILD_INPUT_CODE
        or globals().get("_build_decode_error_v1") is not _BUILD_DECODE_ERROR
        or _BUILD_DECODE_ERROR.__code__ is not _BUILD_DECODE_ERROR_CODE
        or globals().get("_build_resource_result_v1") is not _BUILD_RESOURCE
        or _BUILD_RESOURCE.__code__ is not _BUILD_RESOURCE_CODE
        or globals().get("_build_decoded_result_v1") is not _BUILD_DECODED_RESULT
        or _BUILD_DECODED_RESULT.__code__ is not _BUILD_DECODED_RESULT_CODE
        or globals().get("_build_decode_error_result_v1") is not _BUILD_DECODE_RESULT
        or _BUILD_DECODE_RESULT.__code__ is not _BUILD_DECODE_RESULT_CODE
        or globals().get("_build_resource_parse_result_v1") is not _BUILD_RESOURCE_RESULT
        or _BUILD_RESOURCE_RESULT.__code__ is not _BUILD_RESOURCE_RESULT_CODE
        or globals().get("codec_checker_input_syntax_v1") is not _CODEC
        or _CODEC.__code__ is not _CODEC_CODE
    )
    if drift:
        _LOGGER.error("_validate_parser_integrity_v1 error drift")
        _INTEGRITY_ERROR("kci1-parser-integrity")
    _VALIDATE_COMMON()
    _VALIDATE_BUILDER()
    _LOGGER.debug("_validate_parser_integrity_v1 exit")


_VALIDATE_LOCAL = _validate_parser_integrity_v1
_VALIDATE_LOCAL_CODE = _VALIDATE_LOCAL.__code__


def _wire_add_v1(left: int, right: int) -> int | None:
    """Checked U64 wire arithmetic; overflow is a wire fault, not integrity."""
    _LOGGER.debug("_wire_add_v1 entry")
    if type(left) is not int or type(right) is not int or left < 0 or right < 0:
        _LOGGER.error("_wire_add_v1 error host-shape")
        _INTEGRITY_ERROR("kci1-wire-add-host-shape")
    result = left + right
    if result >= 18_446_744_073_709_551_616:
        _LOGGER.debug("_wire_add_v1 state=overflow")
        return None
    _LOGGER.debug("_wire_add_v1 exit result=%d", result)
    return result


_WIRE_ADD = _wire_add_v1
_WIRE_ADD_CODE = _WIRE_ADD.__code__


def _least_candidate_v1(candidates: tuple[_Candidate, ...]) -> _Candidate | None:
    _LOGGER.debug("_least_candidate_v1 entry count=%d", len(candidates))
    if type(candidates) is not tuple or any(
        type(row) is not tuple
        or len(row) != 2
        or type(row[0]) is not _DECODE_CLASS
        or type(row[1]) is not int
        or not 0 <= row[1] < 18_446_744_073_709_551_616
        for row in candidates
    ):
        _LOGGER.error("_least_candidate_v1 error host-shape")
        _INTEGRITY_ERROR("kci1-candidate-host-shape")
    result = min(
        candidates,
        key=lambda row: (row[1], object.__getattribute__(row[0], "_value_")),
        default=None,
    )
    _LOGGER.debug("_least_candidate_v1 exit found=%s", result is not None)
    return result


_LEAST = _least_candidate_v1
_LEAST_CODE = _LEAST.__code__


def _scan_two_frames_v1(raw: bytes) -> _Scan:
    """Scan every safely locatable outer boundary without constructing DTOs."""
    _LOGGER.debug("_scan_two_frames_v1 entry bytes=%d", len(raw))
    if type(raw) is not bytes:
        _LOGGER.error("_scan_two_frames_v1 error raw-type")
        _INTEGRITY_ERROR("kci1-scan-raw-type")
    early: list[_Candidate] = []
    late: list[_Candidate] = []
    available = min(len(raw), 4)
    for index in range(available):
        if raw[index] != _PREFIX_FROZEN[index]:
            code = _DECODE_CLASS.BAD_DOMAIN if index < 3 else _DECODE_CLASS.BAD_VERSION
            early.append((code, index))
            _LOGGER.debug("_scan_two_frames_v1 state=prefix-candidate offset=%d", index)
    if available < 4:
        early.append((_DECODE_CLASS.BAD_LENGTH, available))
    if len(raw) < 5:
        early.append((_DECODE_CLASS.BAD_LENGTH, 4))
    elif raw[4] != 0:
        early.append((_DECODE_CLASS.BAD_TAG, 4))
    if len(raw) < 6:
        early.append((_DECODE_CLASS.BAD_LENGTH, 5))
    elif raw[5] != 2:
        early.append((_DECODE_CLASS.BAD_ARITY, 5))

    expected_length: int | None = None
    b_term: int | None = None
    term_length: int | None = None
    end: int | None = None
    if len(raw) < 14:
        early.append((_DECODE_CLASS.BAD_LENGTH, 6))
    else:
        expected_length = int.from_bytes(raw[6:14], "big")
        lp_term = _WIRE_ADD(14, expected_length)
        if lp_term is None or lp_term > len(raw):
            early.append((_DECODE_CLASS.BAD_LENGTH, 6))
            expected_length = None
        else:
            b_term_candidate = _WIRE_ADD(lp_term, 8)
            if b_term_candidate is None or b_term_candidate > len(raw):
                late.append((_DECODE_CLASS.BAD_LENGTH, lp_term))
            else:
                b_term = b_term_candidate
                term_length = int.from_bytes(raw[lp_term:b_term], "big")
                end_candidate = _WIRE_ADD(b_term, term_length)
                if end_candidate is None or end_candidate > len(raw):
                    late.append((_DECODE_CLASS.BAD_LENGTH, lp_term))
                    term_length = None
                    b_term = None
                else:
                    end = end_candidate
                    if len(raw) > end:
                        late.append((_DECODE_CLASS.TRAILING, end))
    result = (
        tuple(early),
        tuple(late),
        expected_length,
        b_term,
        term_length,
        end,
    )
    _LOGGER.debug(
        "_scan_two_frames_v1 exit early=%d late=%d expected_safe=%s term_safe=%s",
        len(early),
        len(late),
        expected_length is not None,
        term_length is not None,
    )
    return result


_SCAN = _scan_two_frames_v1
_SCAN_CODE = _SCAN.__code__


def _decode_result_v1(candidate: _Candidate) -> _syntax.KCI1DecodeErrorResultV1:
    _LOGGER.debug("_decode_result_v1 entry")
    error = _BUILD_DECODE_ERROR(candidate[0], candidate[1])
    result = _BUILD_DECODE_RESULT(error)
    _LOGGER.debug("_decode_result_v1 exit")
    return result


_DECODE_RESULT = _decode_result_v1
_DECODE_RESULT_CODE = _DECODE_RESULT.__code__


def _resource_result_v1(
    kind: KCI1ResourceKindV1,
    allowed: int,
    required: int,
    absolute_offset: int,
) -> _syntax.KCI1ResourceParseResultV1:
    _LOGGER.debug("_resource_result_v1 entry kind=%s", kind.name)
    resource = _BUILD_RESOURCE(kind, allowed, required, absolute_offset)
    result = _BUILD_RESOURCE_RESULT(resource)
    _LOGGER.debug("_resource_result_v1 exit")
    return result


_RESOURCE_RESULT = _resource_result_v1
_RESOURCE_RESULT_CODE = _RESOURCE_RESULT.__code__


def parse_checker_input_syntax_v1(
    raw: bytes,
    limits: KCI1LimitsV1 = DEFAULT_KCI1_LIMITS_V1,
) -> _syntax.KCI1ParseResultV1:
    """Return one fresh DECODED, DECODE_ERROR, or RESOURCE KCI1 result."""
    _LOGGER.debug("parse_checker_input_syntax_v1 entry")
    if (
        globals().get("parse_checker_input_syntax_v1") is not _PARSE_PUBLIC
        or _PARSE_PUBLIC.__code__ is not _PARSE_PUBLIC_CODE
        or _PARSE_PUBLIC.__defaults__ is not _PARSE_PUBLIC_DEFAULTS
        or type(_PARSE_PUBLIC_DEFAULTS) is not tuple
        or len(_PARSE_PUBLIC_DEFAULTS) != 1
        or _PARSE_PUBLIC_DEFAULTS[0] is not _DEFAULT_LIMITS
        or globals().get("_validate_parser_integrity_v1") is not _VALIDATE_LOCAL
        or _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
        or globals().get("_wire_add_v1") is not _WIRE_ADD
        or _WIRE_ADD.__code__ is not _WIRE_ADD_CODE
        or globals().get("_least_candidate_v1") is not _LEAST
        or _LEAST.__code__ is not _LEAST_CODE
        or globals().get("_scan_two_frames_v1") is not _SCAN
        or _SCAN.__code__ is not _SCAN_CODE
        or globals().get("_decode_result_v1") is not _DECODE_RESULT
        or _DECODE_RESULT.__code__ is not _DECODE_RESULT_CODE
        or globals().get("_resource_result_v1") is not _RESOURCE_RESULT
        or _RESOURCE_RESULT.__code__ is not _RESOURCE_RESULT_CODE
    ):
        _LOGGER.error("parse_checker_input_syntax_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-parser-helper-integrity")
    _VALIDATE_LOCAL()
    if type(raw) is not bytes:
        _LOGGER.error("parse_checker_input_syntax_v1 error raw-type")
        _INTEGRITY_ERROR("kci1-raw-type")
    limit_values = _SNAPSHOT_LIMITS(limits)
    if len(raw) > limit_values[_MAX_INPUT]:
        _LOGGER.debug("parse_checker_input_syntax_v1 state=input-resource")
        return _RESOURCE_RESULT(
            _RESOURCE_CLASS.INPUT_BYTES,
            limit_values[_MAX_INPUT],
            len(raw),
            limit_values[_MAX_INPUT],
        )

    early, late, expected_length, b_term, term_length, end = _SCAN(raw)
    early_failure = _LEAST(early)
    if early_failure is not None:
        _LOGGER.debug("parse_checker_input_syntax_v1 state=early-decode")
        return _DECODE_RESULT(early_failure)
    if expected_length is None:
        _LOGGER.error("parse_checker_input_syntax_v1 error expected-scan-invariant")
        _INTEGRITY_ERROR("kci1-expected-scan-invariant")
    if expected_length > limit_values[_MAX_EXPECTED]:
        _LOGGER.debug("parse_checker_input_syntax_v1 state=expected-resource")
        return _RESOURCE_RESULT(
            _RESOURCE_CLASS.EXPECTED_BYTES,
            limit_values[_MAX_EXPECTED],
            expected_length,
            14,
        )

    if term_length is None or b_term is None or end is None:
        late_failure = _LEAST(late)
        if late_failure is None:
            _LOGGER.error("parse_checker_input_syntax_v1 error term-scan-invariant")
            _INTEGRITY_ERROR("kci1-term-scan-invariant")
        _LOGGER.debug("parse_checker_input_syntax_v1 state=late-frame-decode")
        return _DECODE_RESULT(late_failure)
    if term_length > limit_values[_MAX_TERM]:
        _LOGGER.debug("parse_checker_input_syntax_v1 state=term-resource")
        return _RESOURCE_RESULT(
            _RESOURCE_CLASS.TERM_BYTES,
            limit_values[_MAX_TERM],
            term_length,
            b_term,
        )
    late_failure = _LEAST(late)
    if late_failure is not None:
        _LOGGER.debug("parse_checker_input_syntax_v1 state=remaining-decode")
        return _DECODE_RESULT(late_failure)
    if end > limit_values[_MAX_OUTPUT]:
        _LOGGER.debug("parse_checker_input_syntax_v1 state=output-resource")
        return _RESOURCE_RESULT(
            _RESOURCE_CLASS.OUTPUT_BYTES,
            limit_values[_MAX_OUTPUT],
            end,
            0,
        )

    expected = raw[14:14 + expected_length]
    term = raw[b_term:end]
    value = _BUILD_INPUT(expected, term)
    try:
        _LOGGER.debug("parse_checker_input_syntax_v1 external_call=codec-roundtrip")
        encoded = _CODEC(value, limits)
    except Exception as exc:
        _LOGGER.error(
            "parse_checker_input_syntax_v1 error roundtrip exception=%s",
            type(exc).__name__,
        )
        _INTEGRITY_ERROR("kci1-roundtrip-integrity")
    if encoded != raw:
        _LOGGER.error("parse_checker_input_syntax_v1 error roundtrip-bytes")
        _INTEGRITY_ERROR("kci1-roundtrip-integrity")
    result = _BUILD_DECODED_RESULT(value, end)
    _LOGGER.debug("parse_checker_input_syntax_v1 exit")
    return result


_PARSE_PUBLIC = parse_checker_input_syntax_v1
_PARSE_PUBLIC_CODE = _PARSE_PUBLIC.__code__
_PARSE_PUBLIC_DEFAULTS = _PARSE_PUBLIC.__defaults__
