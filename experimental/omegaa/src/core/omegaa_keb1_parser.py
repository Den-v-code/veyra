"""Bounded first-offset inverse parser for canonical KEB1 bytes."""

from __future__ import annotations

import logging
from typing import Protocol, cast

from . import omegaa_keb1_types as _syntax
from . import omegaa_kpt1_builder as _kpt_builder_module
from . import omegaa_kpt1_common as _kpt_common_module
from . import omegaa_kpt1_parser as _kpt_parser_module
from .omegaa_keb1_builder import (
    _build_decode_error_result_v1, _build_decoded_result_v1,
    _build_prevalidated_binding_v1, _build_resource_parse_result_v1,
    validate_keb1_builder_integrity_v1,
)
from .omegaa_keb1_codec import codec_expected_binding_v1, validate_keb1_codec_integrity_v1
from .omegaa_keb1_common import (
    DEFAULT_KEB1_LIMITS_V1, KEB1_PREFIX, MAX_COMPOSITE_DEPTH, MAX_COMPOSITE_NODES,
    MAX_EXPECTED_WIRE, MAX_INPUT, MAX_KPT_LIST, MAX_KPT_NAT, MAX_NESTED_KPT, MAX_OUTPUT,
    U64_LIMIT, KEB1DecodeCodeV1, KEB1DecodeError, KEB1LimitsV1,
    KEB1ResourceKindV1, KEB1ResourceLimit, FirstUnsignedDifferenceV1,
    _decode_error, _integrity_error, _resource, _snapshot_limits,
)
from .omegaa_keb1_preflight import (
    KEBKPTStructuralPreflightV1, preflight_kpt_wire_v1,
    validate_keb1_preflight_integrity_v1,
)
from .omegaa_kpt1_common import KPT1DecodeError, KPT1LimitsV1, KPT1ResourceLimit
from .omegaa_kpt1_types import KernelProofTermV1, KernelUniverseLevelV1

logger = logging.getLogger(__name__)
_LOGGER = logger
_BINDING_CLASS = _syntax.ExpectedBindingSyntaxV1
_KPT_CLASS = KernelProofTermV1
_KPT_PARSE = _kpt_parser_module.parse_kernel_proof_term_v1
_KPT_PARSE_CODE = _KPT_PARSE.__code__
_KPT_DECODE_ERROR, _KPT_RESOURCE = KPT1DecodeError, KPT1ResourceLimit
_BUILD = _build_prevalidated_binding_v1
_BUILD_CODE = _BUILD.__code__
_CODEC = codec_expected_binding_v1
_CODEC_CODE = _CODEC.__code__
_KPT_LIMIT_CLASS = KPT1LimitsV1
_KPT_LIMIT_NAMES = ("max_input_bytes", "max_output_bytes", "max_depth", "max_nodes", "max_list_items", "max_nat_bytes")
_KPT_LIMIT_SLOTS = tuple(vars(_KPT_LIMIT_CLASS)[name] for name in _KPT_LIMIT_NAMES)
_OBJECT_NEW_FROZEN = object.__new__
_U64_LIMIT = U64_LIMIT
_PREFIX = KEB1_PREFIX
_DEFAULT_LIMITS_FROZEN = DEFAULT_KEB1_LIMITS_V1
_KPT_PARSER_NS = vars(_kpt_parser_module)
_KPT_BUILD_TERM = _KPT_PARSER_NS["build_term_v1"]
_KPT_BUILD_LEVEL = _KPT_PARSER_NS["build_level_v1"]
_KPT_BUILD_CODES = (_KPT_BUILD_TERM.__code__, _KPT_BUILD_LEVEL.__code__)
_KPT_VALIDATE_BUILDER = _kpt_builder_module._validate_builder_integrity
_KPT_VALIDATE_BUILDER_CODE = _KPT_VALIDATE_BUILDER.__code__
_KPT_FUNCTION_NAMES = (
    "_wire_preflight", "_validate_parser_tables", "_check_prefix", "_take_frame",
    "_u64_at", "_parse_term", "_parse_level", "_parse_term_list", "_parse_nat",
)
_KPT_FUNCTIONS = tuple(_KPT_PARSER_NS[name] for name in _KPT_FUNCTION_NAMES)
_KPT_FUNCTION_CODES = tuple(function.__code__ for function in _KPT_FUNCTIONS)
_KPT_STATIC_NAMES = (
    "_TermTask", "_FieldsTask", "_LevelTask", "_LevelFieldsTask", "_ListTask",
    "_ListItemsTask", "_NatTask", "_DigestTask", "_decode_error", "_resource",
    "_snapshot_limits", "KPT1_PREFIX", "KPT1DecodeCodeV1", "KPT1ValidationError",
    "_OBJECT_GETATTRIBUTE", "MAX_INPUT", "MAX_OUTPUT", "MAX_DEPTH", "MAX_NODES",
    "MAX_LIST", "MAX_NAT", "logger", "_TERM_TAGS", "_LEVEL_TAGS",
    "_LEVEL_ARITIES", "_ARITIES", "_FIELD_KINDS",
)
_KPT_STATICS = tuple(_KPT_PARSER_NS[name] for name in _KPT_STATIC_NAMES)
_BUILD_DECODE_RESULT = _build_decode_error_result_v1
_BUILD_DECODE_RESULT_CODE = _BUILD_DECODE_RESULT.__code__
_BUILD_RESOURCE_RESULT = _build_resource_parse_result_v1
_BUILD_RESOURCE_RESULT_CODE = _BUILD_RESOURCE_RESULT.__code__
_BUILD_DECODED_RESULT = _build_decoded_result_v1
_BUILD_DECODED_RESULT_CODE = _BUILD_DECODED_RESULT.__code__
_INTEGRITY_FROZEN = _integrity_error
_DECODE_ERROR_FROZEN, _RESOURCE_FROZEN, _SNAPSHOT_FROZEN = _decode_error, _resource, _snapshot_limits
_COMMON_FUNCTIONS = (_INTEGRITY_FROZEN, _DECODE_ERROR_FROZEN, _RESOURCE_FROZEN, _SNAPSHOT_FROZEN)
_COMMON_FUNCTION_CODES = tuple(function.__code__ for function in _COMMON_FUNCTIONS)
_PREFLIGHT_FROZEN = preflight_kpt_wire_v1
_PREFLIGHT_CODE = _PREFLIGHT_FROZEN.__code__
_VALIDATE_PREFLIGHT_FROZEN = validate_keb1_preflight_integrity_v1
_VALIDATE_PREFLIGHT_CODE = _VALIDATE_PREFLIGHT_FROZEN.__code__
_FIRST_DIFF_FROZEN = FirstUnsignedDifferenceV1
_FIRST_DIFF_CODE = _FIRST_DIFF_FROZEN.__code__
_VALIDATE_BUILDER_FROZEN = validate_keb1_builder_integrity_v1
_VALIDATE_BUILDER_CODE = _VALIDATE_BUILDER_FROZEN.__code__
_VALIDATE_CODEC_FROZEN = validate_keb1_codec_integrity_v1
_VALIDATE_CODEC_CODE = _VALIDATE_CODEC_FROZEN.__code__


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def _make_kpt_limits_v1(values: tuple[int, ...], root_only: bool) -> KPT1LimitsV1:
    _LOGGER.debug("_make_kpt_limits_v1 entry root_only=%s", root_only)
    if any(vars(_KPT_LIMIT_CLASS).get(name) is not slot for name, slot in zip(_KPT_LIMIT_NAMES, _KPT_LIMIT_SLOTS, strict=True)):
        _integrity_error("keb1-kpt-limits-integrity")
    depth = values[MAX_COMPOSITE_DEPTH] - 1
    if depth == 0 and root_only:
        depth = 1
    nodes = values[MAX_COMPOSITE_NODES] - 1
    if depth <= 0 or nodes <= 0:
        _integrity_error("keb1-delegated-limits-integrity")
    result = _OBJECT_NEW_FROZEN(_KPT_LIMIT_CLASS)
    raw = (values[MAX_NESTED_KPT], values[MAX_NESTED_KPT], depth, nodes, values[MAX_KPT_LIST], values[MAX_KPT_NAT])
    for slot, value in zip(_KPT_LIMIT_SLOTS, raw, strict=True):
        cast(_SlotSetter, slot).__set__(result, value)
    _LOGGER.debug("_make_kpt_limits_v1 exit depth=%d nodes=%d", depth, nodes)
    return result


_MAKE_KPT_LIMITS_FROZEN = _make_kpt_limits_v1
_MAKE_KPT_LIMITS_CODE = _MAKE_KPT_LIMITS_FROZEN.__code__


def _read_frame_v1(raw: bytes, offset: int) -> tuple[int, int, int] | None:
    _LOGGER.debug("_read_frame_v1 entry offset=%d", offset)
    if offset < 0 or offset > len(raw):
        _integrity_error("keb1-frame-offset-integrity")
    if offset > len(raw) - 8:
        _LOGGER.debug("_read_frame_v1 exit missing")
        return None
    length = int.from_bytes(raw[offset : offset + 8], "big")
    start = offset + 8
    if length > len(raw) - start:
        _LOGGER.debug("_read_frame_v1 exit truncated")
        return None
    stop = start + length
    _LOGGER.debug("_read_frame_v1 exit start=%d stop=%d", start, stop)
    return start, stop, stop


_READ_FRAME_FROZEN = _read_frame_v1
_READ_FRAME_CODE = _READ_FRAME_FROZEN.__code__


def validate_keb1_parser_integrity_v1() -> None:
    _LOGGER.debug("validate_keb1_parser_integrity_v1 entry")
    drift = (
        globals().get("logger") is not _LOGGER or vars(_syntax).get("ExpectedBindingSyntaxV1") is not _BINDING_CLASS
        or vars(_kpt_parser_module).get("parse_kernel_proof_term_v1") is not _KPT_PARSE or _KPT_PARSE.__code__ is not _KPT_PARSE_CODE
        or globals().get("_build_prevalidated_binding_v1") is not _BUILD or _BUILD.__code__ is not _BUILD_CODE
        or globals().get("codec_expected_binding_v1") is not _CODEC or _CODEC.__code__ is not _CODEC_CODE
        or globals().get("KEB1_PREFIX") is not _PREFIX or _PREFIX != b"KEB1"
        or globals().get("U64_LIMIT") != _U64_LIMIT or _U64_LIMIT != 18446744073709551616
        or object.__new__ is not _OBJECT_NEW_FROZEN
        or globals().get("_parse_expected_binding_or_raise_v1") is not _PARSE_RAISE_FROZEN
        or _PARSE_RAISE_FROZEN.__code__ is not _PARSE_RAISE_CODE
        or _PARSE_RAISE_FROZEN.__defaults__ is not _PARSE_RAISE_DEFAULTS
        or _PARSE_RAISE_DEFAULTS != (_DEFAULT_LIMITS_FROZEN,)
        or globals().get("parse_expected_binding_v1") is not _PARSE_PUBLIC_FROZEN
        or _PARSE_PUBLIC_FROZEN.__code__ is not _PARSE_PUBLIC_CODE
        or _PARSE_PUBLIC_FROZEN.__defaults__ is not _PARSE_PUBLIC_DEFAULTS
        or _PARSE_PUBLIC_DEFAULTS != (_DEFAULT_LIMITS_FROZEN,)
        or globals().get("_build_decode_error_result_v1") is not _BUILD_DECODE_RESULT or _BUILD_DECODE_RESULT.__code__ is not _BUILD_DECODE_RESULT_CODE
        or globals().get("_build_resource_parse_result_v1") is not _BUILD_RESOURCE_RESULT or _BUILD_RESOURCE_RESULT.__code__ is not _BUILD_RESOURCE_RESULT_CODE
        or globals().get("_build_decoded_result_v1") is not _BUILD_DECODED_RESULT or _BUILD_DECODED_RESULT.__code__ is not _BUILD_DECODED_RESULT_CODE
        or _KPT_PARSER_NS.get("build_term_v1") is not _KPT_BUILD_TERM
        or _KPT_PARSER_NS.get("build_level_v1") is not _KPT_BUILD_LEVEL
        or (_KPT_BUILD_TERM.__code__, _KPT_BUILD_LEVEL.__code__) != _KPT_BUILD_CODES
        or _kpt_builder_module._validate_builder_integrity is not _KPT_VALIDATE_BUILDER
        or _KPT_VALIDATE_BUILDER.__code__ is not _KPT_VALIDATE_BUILDER_CODE
        or _KPT_PARSER_NS.get("KernelProofTermV1") is not _KPT_CLASS
        or _KPT_PARSER_NS.get("KernelUniverseLevelV1") is not KernelUniverseLevelV1
        or any(_KPT_PARSER_NS.get(name) is not function or function.__code__ is not code for name, function, code in zip(_KPT_FUNCTION_NAMES, _KPT_FUNCTIONS, _KPT_FUNCTION_CODES, strict=True))
        or any(_KPT_PARSER_NS.get(name) is not value for name, value in zip(_KPT_STATIC_NAMES, _KPT_STATICS, strict=True))
        or _kpt_common_module.KPT1DecodeError is not _KPT_DECODE_ERROR
        or _kpt_common_module.KPT1ResourceLimit is not _KPT_RESOURCE
        or tuple(function.__code__ for function in _COMMON_FUNCTIONS) != _COMMON_FUNCTION_CODES
        or (globals().get("_integrity_error"), globals().get("_decode_error"), globals().get("_resource"), globals().get("_snapshot_limits")) != _COMMON_FUNCTIONS
        or globals().get("preflight_kpt_wire_v1") is not _PREFLIGHT_FROZEN or _PREFLIGHT_FROZEN.__code__ is not _PREFLIGHT_CODE
        or globals().get("validate_keb1_preflight_integrity_v1") is not _VALIDATE_PREFLIGHT_FROZEN or _VALIDATE_PREFLIGHT_FROZEN.__code__ is not _VALIDATE_PREFLIGHT_CODE
        or globals().get("FirstUnsignedDifferenceV1") is not _FIRST_DIFF_FROZEN or _FIRST_DIFF_FROZEN.__code__ is not _FIRST_DIFF_CODE
        or globals().get("validate_keb1_builder_integrity_v1") is not _VALIDATE_BUILDER_FROZEN or _VALIDATE_BUILDER_FROZEN.__code__ is not _VALIDATE_BUILDER_CODE
        or globals().get("validate_keb1_codec_integrity_v1") is not _VALIDATE_CODEC_FROZEN or _VALIDATE_CODEC_FROZEN.__code__ is not _VALIDATE_CODEC_CODE
        or globals().get("_make_kpt_limits_v1") is not _MAKE_KPT_LIMITS_FROZEN or _MAKE_KPT_LIMITS_FROZEN.__code__ is not _MAKE_KPT_LIMITS_CODE
        or globals().get("_read_frame_v1") is not _READ_FRAME_FROZEN or _READ_FRAME_FROZEN.__code__ is not _READ_FRAME_CODE
        or globals().get("_choose_resource_v1") is not _CHOOSE_RESOURCE_FROZEN or _CHOOSE_RESOURCE_FROZEN.__code__ is not _CHOOSE_RESOURCE_CODE
    )
    if drift:
        _INTEGRITY_FROZEN("keb1-parser-integrity")
    _VALIDATE_BUILDER_FROZEN()
    _VALIDATE_CODEC_FROZEN()
    _VALIDATE_PREFLIGHT_FROZEN()
    try:
        _KPT_VALIDATE_BUILDER(_KPT_CLASS, KernelUniverseLevelV1)
    except Exception:
        _INTEGRITY_FROZEN("keb1-kpt-builder-integrity")
    _LOGGER.debug("validate_keb1_parser_integrity_v1 exit")


_VALIDATE_PARSER_FROZEN = validate_keb1_parser_integrity_v1
_VALIDATE_PARSER_CODE = _VALIDATE_PARSER_FROZEN.__code__


def _choose_resource_v1(payload: bytes, wire: bytes, values: tuple[int, ...], report: KEBKPTStructuralPreflightV1) -> None:
    _LOGGER.debug("_choose_resource_v1 entry")
    candidates: list[tuple[int, int, KEB1ResourceKindV1, int, int]] = []
    rows = (
        (KEB1ResourceKindV1.NESTED_KPT_BYTES, values[MAX_NESTED_KPT], len(payload), 14),
        (KEB1ResourceKindV1.EXPECTED_WIRE_BYTES, values[MAX_EXPECTED_WIRE], len(wire), 22 + len(payload)),
        (KEB1ResourceKindV1.OUTPUT_BYTES, values[MAX_OUTPUT], 22 + 2 * len(payload), 0),
    )
    for kind, allowed, required, offset in rows:
        if required > allowed:
            candidates.append((offset, int(kind), kind, allowed, required))
    for metric in report.nodes:
        required = 1 + metric.depth
        if required > values[MAX_COMPOSITE_DEPTH]:
            kind = KEB1ResourceKindV1.COMPOSITE_DEPTH
            candidates.append((14 + metric.node_start, int(kind), kind, values[MAX_COMPOSITE_DEPTH], required))
        required = 1 + metric.running_node_count
        if required > values[MAX_COMPOSITE_NODES]:
            kind = KEB1ResourceKindV1.COMPOSITE_NODES
            candidates.append((14 + metric.node_start, int(kind), kind, values[MAX_COMPOSITE_NODES], required))
    for list_metric in report.lists:
        if list_metric.count > values[MAX_KPT_LIST]:
            kind = KEB1ResourceKindV1.KPT_LIST_ITEMS
            candidates.append((14 + list_metric.count_start, int(kind), kind, values[MAX_KPT_LIST], list_metric.count))
    for nat_metric in report.nats:
        if nat_metric.count > values[MAX_KPT_NAT]:
            kind = KEB1ResourceKindV1.KPT_NAT_BYTES
            candidates.append((14 + nat_metric.count_start, int(kind), kind, values[MAX_KPT_NAT], nat_metric.count))
    if candidates:
        offset, _, kind, allowed, required = min(candidates)
        _resource(kind, allowed, required, offset)
    _LOGGER.debug("_choose_resource_v1 exit")


_CHOOSE_RESOURCE_FROZEN = _choose_resource_v1
_CHOOSE_RESOURCE_CODE = _CHOOSE_RESOURCE_FROZEN.__code__


def _parse_expected_binding_or_raise_v1(raw: bytes, limits: KEB1LimitsV1 = DEFAULT_KEB1_LIMITS_V1) -> _syntax.ExpectedBindingSyntaxV1:
    """Parse KEB1 after decode-first global selection and own resource gates."""
    _LOGGER.debug("_parse_expected_binding_or_raise_v1 entry bytes=%d", len(raw) if type(raw) is bytes else -1)
    if globals().get("validate_keb1_parser_integrity_v1") is not _VALIDATE_PARSER_FROZEN or _VALIDATE_PARSER_FROZEN.__code__ is not _VALIDATE_PARSER_CODE:
        _INTEGRITY_FROZEN("keb1-parser-validator-integrity")
    _VALIDATE_PARSER_FROZEN()
    if type(raw) is not bytes:
        _INTEGRITY_FROZEN("keb1-raw-type")
    values = _SNAPSHOT_FROZEN(limits)
    if len(raw) > values[MAX_INPUT]:
        _RESOURCE_FROZEN(KEB1ResourceKindV1.INPUT_BYTES, values[MAX_INPUT], len(raw), values[MAX_INPUT])

    available = min(4, len(raw))
    for index in range(available):
        if raw[index] != _PREFIX[index]:
            _DECODE_ERROR_FROZEN(KEB1DecodeCodeV1.BAD_DOMAIN if index < 3 else KEB1DecodeCodeV1.BAD_VERSION, index)
    if available < 4:
        _DECODE_ERROR_FROZEN(KEB1DecodeCodeV1.BAD_LENGTH, available)
    if len(raw) < 5:
        _DECODE_ERROR_FROZEN(KEB1DecodeCodeV1.BAD_LENGTH, 4)
    if raw[4] != 0:
        _DECODE_ERROR_FROZEN(KEB1DecodeCodeV1.BAD_TAG, 4)
    if len(raw) < 6:
        _DECODE_ERROR_FROZEN(KEB1DecodeCodeV1.BAD_LENGTH, 5)
    if raw[5] != 2:
        _DECODE_ERROR_FROZEN(KEB1DecodeCodeV1.BAD_ARITY, 5)
    first = _READ_FRAME_FROZEN(raw, 6)
    if first is None:
        _DECODE_ERROR_FROZEN(KEB1DecodeCodeV1.BAD_LENGTH, 6)
    p_start, p_end, lp_w = first
    payload = memoryview(raw)[p_start:p_end].tobytes()
    report = _PREFLIGHT_FROZEN(payload)
    decode_candidates = [(code, p_start + offset) for code, offset in report.decode_candidates]

    second = _READ_FRAME_FROZEN(raw, lp_w)
    wire: bytes | None = None
    end = lp_w
    if second is None:
        decode_candidates.append((KEB1DecodeCodeV1.BAD_LENGTH, lp_w))
    else:
        w_start, w_end, end = second
        wire = memoryview(raw)[w_start:w_end].tobytes()
        if end != len(raw):
            decode_candidates.append((KEB1DecodeCodeV1.TRAILING, end))
        if not report.decode_candidates and report.root_consumed and wire != payload:
            difference = _FIRST_DIFF_FROZEN(wire, payload)
            if type(difference) is not int:
                _INTEGRITY_FROZEN("keb1-first-difference-integrity")
            decode_candidates.append((KEB1DecodeCodeV1.DEPENDENCY, w_start + difference))
    if decode_candidates:
        code, offset = min(decode_candidates, key=lambda item: (item[1], int(item[0])))
        _DECODE_ERROR_FROZEN(code, offset)
    if wire is None or not report.root_consumed:
        _INTEGRITY_FROZEN("keb1-parser-canonicality-integrity")
    _CHOOSE_RESOURCE_FROZEN(payload, wire, values, report)

    derived = _MAKE_KPT_LIMITS_FROZEN(values, len(report.nodes) == 1)
    _LOGGER.debug("parse_expected_binding_v1 external KPT parser")
    try:
        term = _KPT_PARSE(payload, derived)
    except (_KPT_DECODE_ERROR, _KPT_RESOURCE) as exc:
        _LOGGER.error("parse_expected_binding_v1 error unexpected-dependency=%s", type(exc).__name__)
        _INTEGRITY_FROZEN("keb1-kpt-parser-differential-integrity")
    except Exception as exc:
        _LOGGER.error("parse_expected_binding_v1 error dependency=%s", type(exc).__name__)
        _INTEGRITY_FROZEN("keb1-kpt-parser-integrity")
    if type(term) is not _KPT_CLASS:
        _INTEGRITY_FROZEN("keb1-kpt-parser-result")
    result = _BUILD(term, wire, _KPT_CLASS, _BINDING_CLASS)
    try:
        reencoded = _CODEC(result, limits)
    except Exception as exc:
        _LOGGER.error("parse_expected_binding_v1 error reencode=%s", type(exc).__name__)
        _INTEGRITY_FROZEN("keb1-roundtrip-integrity")
    if reencoded != raw:
        _INTEGRITY_FROZEN("keb1-roundtrip-integrity")
    _LOGGER.debug("_parse_expected_binding_or_raise_v1 exit")
    return result


def parse_expected_binding_v1(raw: bytes, limits: KEB1LimitsV1 = DEFAULT_KEB1_LIMITS_V1) -> _syntax.KEB1ParseResultV1:
    """Return a fresh typed DECODED, DECODE_ERROR or RESOURCE result."""
    _LOGGER.debug("parse_expected_binding_v1 entry bytes=%d", len(raw) if type(raw) is bytes else -1)
    try:
        value = _PARSE_RAISE_FROZEN(raw, limits)
    except KEB1DecodeError as exc:
        result: _syntax.KEB1ParseResultV1 = _BUILD_DECODE_RESULT(exc.code, exc.absolute_offset)
        _LOGGER.debug("parse_expected_binding_v1 exit state=decode-error")
        return result
    except KEB1ResourceLimit as exc:
        result = _BUILD_RESOURCE_RESULT(exc.kind, exc.allowed, exc.required, exc.absolute_offset)
        _LOGGER.debug("parse_expected_binding_v1 exit state=resource")
        return result
    result = _BUILD_DECODED_RESULT(value, len(raw))
    _LOGGER.debug("parse_expected_binding_v1 exit state=decoded")
    return result


_PARSE_RAISE_FROZEN = _parse_expected_binding_or_raise_v1
_PARSE_RAISE_CODE = _PARSE_RAISE_FROZEN.__code__
_PARSE_RAISE_DEFAULTS = _PARSE_RAISE_FROZEN.__defaults__
_PARSE_PUBLIC_FROZEN = parse_expected_binding_v1
_PARSE_PUBLIC_CODE = _PARSE_PUBLIC_FROZEN.__code__
_PARSE_PUBLIC_DEFAULTS = _PARSE_PUBLIC_FROZEN.__defaults__

ExpectedBindingSyntaxV1 = _BINDING_CLASS
