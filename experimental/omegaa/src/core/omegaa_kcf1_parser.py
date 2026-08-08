"""Bounded first-offset inverse parser for inert private KCF1 frames."""

from __future__ import annotations

import logging

from . import omegaa_kpt1_builder as _kpt_builder_module
from . import omegaa_kpt1_common as _kpt_common_module
from . import omegaa_kpt1_parser as _kpt_parser_module
from .omegaa_kcf1_builder import build_frame_v1, validate_kcf1_builder_integrity_v1
from .omegaa_kcf1_codec import (
    _make_kpt_limits_v1, _scan_kpt_v1,
    _validate_kpt_dependency_integrity_v1, codec_kernel_continuation_frame_v1,
)
from .omegaa_kcf1_common import (
    DEFAULT_KCF1_LIMITS_V1, KCF1_PREFIX, KCF1DecodeCodeV1,
    KCF1LimitsV1, KCF1ResourceKindV1, MAX_DEPTH, MAX_INPUT, MAX_KPT_LIST,
    MAX_KPT_NAT, MAX_NESTED, MAX_NODES, MAX_OUTPUT, _decode_error,
    _host_error, _map_kpt_resource_v1, _resource, _snapshot_limits,
    validate_kcf1_error_enum_integrity_v1,
)
from .omegaa_kcf1_types import (
    KCF1_ARITIES as _ARITIES, KCF1_FIELD_KINDS as _FIELD_KINDS,
    KernelContinuationFrameV1, KernelContinuationTagV1,
    kcf1_tag_from_ordinal_v1,
)
from .omegaa_kpt1_common import KPT1DecodeCodeV1, KPT1DecodeError, KPT1ResourceLimit
from .omegaa_kpt1_parser import parse_kernel_proof_term_v1
from .omegaa_kpt1_types import KernelProofTermV1, KernelUniverseLevelV1

logger = logging.getLogger(__name__)
_KCF_BUILD = build_frame_v1
_KCF_BUILD_CODE = _KCF_BUILD.__code__
_KCF_VALIDATE_BUILDER = validate_kcf1_builder_integrity_v1
_KCF_VALIDATE_BUILDER_CODE = _KCF_VALIDATE_BUILDER.__code__
_KCF_CODEC = codec_kernel_continuation_frame_v1
_KCF_CODEC_CODE = _KCF_CODEC.__code__
_KPT_PARSE = parse_kernel_proof_term_v1
_KPT_PARSE_CODE = _KPT_PARSE.__code__
_KPT_PARSER_NS = vars(_kpt_parser_module)
_KPT_BUILD_TERM = _KPT_PARSER_NS["build_term_v1"]
_KPT_BUILD_LEVEL = _KPT_PARSER_NS["build_level_v1"]
_KPT_BUILD_TERM_CODE = _KPT_BUILD_TERM.__code__
_KPT_BUILD_LEVEL_CODE = _KPT_BUILD_LEVEL.__code__
_KPT_VALIDATE_BUILDER = _kpt_builder_module._validate_builder_integrity
_KPT_VALIDATE_BUILDER_CODE = _KPT_VALIDATE_BUILDER.__code__
_KPT_DECODE_CLASS = KPT1DecodeError
_KPT_RESOURCE_CLASS = KPT1ResourceLimit
_KPT_CODES = tuple(KPT1DecodeCodeV1(index) for index in range(11))
_KPT_CODES_FROZEN = _KPT_CODES
_KPT_TERM_TAGS = _KPT_PARSER_NS["_TERM_TAGS"]
_KPT_LEVEL_TAGS = _KPT_PARSER_NS["_LEVEL_TAGS"]
_KPT_LEVEL_ARITIES = _KPT_PARSER_NS["_LEVEL_ARITIES"]
_KPT_ARITIES = _KPT_PARSER_NS["_ARITIES"]
_KPT_FIELDS = _KPT_PARSER_NS["_FIELD_KINDS"]
_KPT_FUNCTION_NAMES = (
    "_wire_preflight", "_validate_parser_tables", "_check_prefix", "_take_frame",
    "_u64_at", "_parse_term", "_parse_level", "_parse_term_list", "_parse_nat",
)
_KPT_FUNCTIONS = tuple(_KPT_PARSER_NS[name] for name in _KPT_FUNCTION_NAMES)
_KPT_FUNCTION_CODES = tuple(function.__code__ for function in _KPT_FUNCTIONS)
_KPT_WIRE_PREFLIGHT = _KPT_PARSER_NS["_wire_preflight"]
_KPT_STATIC_NAMES = (
    "_TermTask", "_FieldsTask", "_LevelTask", "_LevelFieldsTask", "_ListTask",
    "_ListItemsTask", "_NatTask", "_DigestTask", "_decode_error", "_resource",
    "_snapshot_limits", "KPT1_PREFIX", "KPT1DecodeCodeV1", "KPT1ValidationError",
    "_OBJECT_GETATTRIBUTE", "MAX_INPUT", "MAX_OUTPUT", "MAX_DEPTH", "MAX_NODES",
    "MAX_LIST", "MAX_NAT", "logger",
)
_KPT_STATICS = tuple(_KPT_PARSER_NS[name] for name in _KPT_STATIC_NAMES)
_KCF_TAG_FROM = kcf1_tag_from_ordinal_v1
_KCF_TAG_FROM_CODE = _KCF_TAG_FROM.__code__
_ARITIES_FROZEN, _FIELD_KINDS_FROZEN = _ARITIES, _FIELD_KINDS


def _validate_nested_parser_integrity_v1() -> None:
    logger.debug("_validate_nested_parser_integrity_v1 entry")
    _validate_kpt_dependency_integrity_v1()
    drift = (
        _KPT_PARSER_NS.get("parse_kernel_proof_term_v1") is not _KPT_PARSE
        or _KPT_PARSE.__code__ is not _KPT_PARSE_CODE
        or _KPT_PARSER_NS.get("build_term_v1") is not _KPT_BUILD_TERM
        or _KPT_PARSER_NS.get("build_level_v1") is not _KPT_BUILD_LEVEL
        or _KPT_BUILD_TERM.__code__ is not _KPT_BUILD_TERM_CODE
        or _KPT_BUILD_LEVEL.__code__ is not _KPT_BUILD_LEVEL_CODE
        or _kpt_builder_module._validate_builder_integrity is not _KPT_VALIDATE_BUILDER
        or _KPT_VALIDATE_BUILDER.__code__ is not _KPT_VALIDATE_BUILDER_CODE
        or _KPT_PARSER_NS.get("KernelProofTermV1") is not KernelProofTermV1
        or _KPT_PARSER_NS.get("KernelUniverseLevelV1") is not KernelUniverseLevelV1
        or _KPT_PARSER_NS.get("_TERM_TAGS") is not _KPT_TERM_TAGS
        or _KPT_PARSER_NS.get("_LEVEL_TAGS") is not _KPT_LEVEL_TAGS
        or _KPT_PARSER_NS.get("_LEVEL_ARITIES") is not _KPT_LEVEL_ARITIES
        or _KPT_PARSER_NS.get("_ARITIES") is not _KPT_ARITIES
        or _KPT_PARSER_NS.get("_FIELD_KINDS") is not _KPT_FIELDS
        or any(
            _KPT_PARSER_NS.get(name) is not function or function.__code__ is not code
            for name, function, code in zip(
                _KPT_FUNCTION_NAMES, _KPT_FUNCTIONS, _KPT_FUNCTION_CODES, strict=True,
            )
        )
        or any(
            _KPT_PARSER_NS.get(name) is not value
            for name, value in zip(_KPT_STATIC_NAMES, _KPT_STATICS, strict=True)
        )
        or _kpt_common_module.KPT1DecodeError is not _KPT_DECODE_CLASS
        or _kpt_common_module.KPT1ResourceLimit is not _KPT_RESOURCE_CLASS
    )
    if drift:
        logger.error("_validate_nested_parser_integrity_v1 error drift")
        raise ValueError("kcf1-kpt-parser-integrity")
    _KPT_VALIDATE_BUILDER(KernelProofTermV1, KernelUniverseLevelV1)
    validate_kcf1_error_enum_integrity_v1()
    if (
        globals().get("_KPT_CODES") is not _KPT_CODES_FROZEN
        or len(_KPT_CODES_FROZEN) != 11
        or any(
            type(code) is not KPT1DecodeCodeV1
            or code is not KPT1DecodeCodeV1(index)
            or object.__getattribute__(code, "_value_") != index
            for index, code in enumerate(_KPT_CODES_FROZEN)
        )
    ):
        _host_error("kcf1-kpt-decode-enum-integrity")
    logger.debug("_validate_nested_parser_integrity_v1 exit")


def _validate_local_alias_integrity_v1() -> None:
    logger.debug("_validate_local_alias_integrity_v1 entry")
    drift = (
        globals().get("build_frame_v1") is not _KCF_BUILD
        or _KCF_BUILD.__code__ is not _KCF_BUILD_CODE
        or globals().get("validate_kcf1_builder_integrity_v1") is not _KCF_VALIDATE_BUILDER
        or _KCF_VALIDATE_BUILDER.__code__ is not _KCF_VALIDATE_BUILDER_CODE
        or globals().get("codec_kernel_continuation_frame_v1") is not _KCF_CODEC
        or _KCF_CODEC.__code__ is not _KCF_CODEC_CODE
        or globals().get("_ARITIES") is not _ARITIES_FROZEN
        or globals().get("_FIELD_KINDS") is not _FIELD_KINDS_FROZEN
        or globals().get("kcf1_tag_from_ordinal_v1") is not _KCF_TAG_FROM
        or _KCF_TAG_FROM.__code__ is not _KCF_TAG_FROM_CODE
        or globals().get("KPT1DecodeError") is not _KPT_DECODE_CLASS or globals().get("KPT1ResourceLimit") is not _KPT_RESOURCE_CLASS
    )
    if drift:
        _host_error("kcf1-parser-alias-integrity")
    logger.debug("_validate_local_alias_integrity_v1 exit")


_VALIDATE_LOCAL = _validate_local_alias_integrity_v1
_VALIDATE_LOCAL_CODE = _VALIDATE_LOCAL.__code__
_VALIDATE_NESTED = _validate_nested_parser_integrity_v1
_VALIDATE_NESTED_CODE = _VALIDATE_NESTED.__code__


def _check_prefix(data: bytes) -> None:
    logger.debug("_check_prefix entry bytes=%d", len(data))
    available = min(4, len(data))
    for index in range(available):
        if data[index] != KCF1_PREFIX[index]:
            _decode_error(KCF1DecodeCodeV1.BAD_VERSION, index)
    if available < 4:
        _decode_error(KCF1DecodeCodeV1.BAD_LENGTH, available)
    logger.debug("_check_prefix exit")


def _scan_outer_v1(
    data: bytes, limits: tuple[int, ...],
) -> tuple[
    KernelContinuationTagV1, tuple[tuple[int, int], ...],
    tuple[KCF1DecodeCodeV1, int] | None,
]:
    logger.debug("_scan_outer_v1 entry")
    _check_prefix(data)
    if len(data) < 5:
        _decode_error(KCF1DecodeCodeV1.BAD_LENGTH, 4)
    raw_tag = data[4]
    if raw_tag >= len(_ARITIES):
        _decode_error(KCF1DecodeCodeV1.BAD_TAG, 4)
    tag = _KCF_TAG_FROM(raw_tag)
    if len(data) < 6:
        _decode_error(KCF1DecodeCodeV1.BAD_LENGTH, 5)
    if data[5] != _ARITIES[tag]:
        _decode_error(KCF1DecodeCodeV1.BAD_ARITY, 5)
    offset = 6
    spans: list[tuple[int, int]] = []
    nested = 0
    nested_over: int | None = None
    deferred: tuple[KCF1DecodeCodeV1, int] | None = None
    for kind in _FIELD_KINDS[tag]:
        if offset + 8 > len(data):
            deferred = (KCF1DecodeCodeV1.BAD_LENGTH, offset)
            break
        length = int.from_bytes(data[offset : offset + 8], "big")
        start, stop = offset + 8, offset + 8 + length
        if stop > len(data):
            deferred = (KCF1DecodeCodeV1.BAD_LENGTH, offset)
            break
        offset = stop
        spans.append((start, stop))
        if kind == "term":
            nested += stop - start
            if nested > limits[MAX_NESTED] and nested_over is None:
                nested_over = start
        elif kind == "kernel_type_id" and stop - start != 32 and deferred is None:
            deferred = (KCF1DecodeCodeV1.BAD_LENGTH, start)
    if offset != len(data) and deferred is None:
        deferred = (KCF1DecodeCodeV1.TRAILING, offset)
    if nested_over is not None:
        _resource(KCF1ResourceKindV1.NESTED_KPT_BYTES, nested_over)
    logger.debug("_scan_outer_v1 exit nested=%d", nested)
    return tag, tuple(spans), deferred


def _map_kpt_decode_v1(exc: KPT1DecodeError, base: int) -> None:
    logger.debug("_map_kpt_decode_v1 entry base=%d", base)
    if type(exc) is not _KPT_DECODE_CLASS:
        _host_error("nested-kpt-decode-type")
    code = object.__getattribute__(exc, "code")
    offset = object.__getattribute__(exc, "offset")
    if type(code) is not KPT1DecodeCodeV1 or type(offset) is not int or offset < 0:
        _host_error("nested-kpt-decode-integrity")
    _VALIDATE_NESTED()
    ordinal = _KPT_CODES_FROZEN.index(code)
    _decode_error(KCF1DecodeCodeV1(ordinal), base + offset)


def parse_kernel_continuation_frame_v1(
    raw: bytes, limits: KCF1LimitsV1 = DEFAULT_KCF1_LIMITS_V1,
) -> KernelContinuationFrameV1:
    """Parse canonical KCF1 bytes without executing continuation semantics."""
    logger.debug("parse_kernel_continuation_frame_v1 entry")
    if (
        _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
        or _VALIDATE_NESTED.__code__ is not _VALIDATE_NESTED_CODE
    ):
        _host_error("kcf1-parser-alias-integrity")
    _VALIDATE_LOCAL()
    _KCF_VALIDATE_BUILDER(KernelContinuationFrameV1, KernelContinuationTagV1)
    _VALIDATE_NESTED()
    if type(raw) is not bytes:
        logger.error("parse_kernel_continuation_frame_v1 error raw-type")
        raise TypeError("raw must be exact bytes")
    values = _snapshot_limits(limits)
    if len(raw) > values[MAX_INPUT]:
        _resource(KCF1ResourceKindV1.INPUT_BYTES, values[MAX_INPUT])
    if len(raw) > values[MAX_OUTPUT]:
        _resource(KCF1ResourceKindV1.OUTPUT_BYTES, values[MAX_OUTPUT])
    tag, spans, deferred = _scan_outer_v1(raw, values)
    fields: list[object] = []
    nested_used = 0
    nodes_used = 0
    seen: set[int] = set()
    for kind, (start, stop) in zip(_FIELD_KINDS[tag], spans):
        if deferred is not None and start >= deferred[1]:
            _decode_error(*deferred)
        if kind != "term":
            fields.append(raw[start:stop])
            continue
        remaining_nodes = values[MAX_NODES] - 1 - nodes_used
        remaining_nested = values[MAX_NESTED] - nested_used
        if remaining_nodes <= 0:
            _resource(KCF1ResourceKindV1.COMPOSITE_NODES, start)
        if remaining_nested <= 0:
            _resource(KCF1ResourceKindV1.NESTED_KPT_BYTES, start)
        if values[MAX_DEPTH] - 2 < 0:
            _resource(KCF1ResourceKindV1.COMPOSITE_DEPTH, start)
        payload = raw[start:stop]
        wire_limits = (
            remaining_nested, values[MAX_OUTPUT], values[MAX_DEPTH] - 2,
            remaining_nodes, values[MAX_KPT_LIST], values[MAX_KPT_NAT],
        )
        try:
            _KPT_WIRE_PREFLIGHT(payload, wire_limits)
        except KPT1DecodeError as exc:
            _map_kpt_decode_v1(exc, start)
        except KPT1ResourceLimit as exc:
            _map_kpt_resource_v1(exc, start, _KPT_RESOURCE_CLASS)
        derived = _make_kpt_limits_v1((
            remaining_nested, values[MAX_OUTPUT], max(1, values[MAX_DEPTH] - 2),
            remaining_nodes, values[MAX_KPT_LIST], values[MAX_KPT_NAT],
        ))
        logger.debug("parse_kernel_continuation_frame_v1 external KPT parse start=%d", start)
        try:
            term = _KPT_PARSE(payload, derived)
        except KPT1DecodeError as exc:
            _map_kpt_decode_v1(exc, start)
        except KPT1ResourceLimit as exc:
            _map_kpt_resource_v1(exc, start, _KPT_RESOURCE_CLASS)
        metric = _scan_kpt_v1(term, seen, values, nodes_used)
        nodes_used += metric[0]
        nested_used += len(payload)
        fields.append(term)
    if deferred is not None:
        _decode_error(*deferred)
    result = _KCF_BUILD(
        tag, tuple(fields), KernelContinuationFrameV1, KernelContinuationTagV1,
    )
    encoded = _KCF_CODEC(result, limits)
    if encoded != raw:
        _decode_error(KCF1DecodeCodeV1.DEPENDENCY, 0)
    logger.debug("parse_kernel_continuation_frame_v1 exit tag=%s", tag.name)
    return result
