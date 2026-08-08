"""Canonical KCF1 encoder and exact composite identity/resource scan."""
from __future__ import annotations

import logging
from typing import Protocol, cast

from . import omegaa_kpt1_codec as _kpt_codec_module
from . import omegaa_kpt1_common as _kpt_common_module
from . import omegaa_kpt1_types as _kpt_syntax
from .omegaa_kcf1_builder import validate_kcf1_builder_integrity_v1
from .omegaa_kcf1_common import (
    DEFAULT_KCF1_LIMITS_V1, KCF1_PREFIX, KCF1LimitsV1,
    KCF1ResourceKindV1, MAX_DEPTH, MAX_KPT_LIST, MAX_KPT_NAT,
    MAX_NESTED, MAX_NODES, MAX_OUTPUT, _host_error, _map_kpt_resource_v1,
    _resource, _slot, _snapshot_limits, _frame,
    validate_kcf1_error_enum_integrity_v1,
)
from .omegaa_kcf1_types import (
    KCF1_ARITIES as _ARITIES, KCF1_FIELD_KINDS as _FIELD_KINDS,
    KernelContinuationFrameV1, KernelContinuationTagV1,
    kcf1_tag_ordinal_v1, validate_kcf1_enum_integrity_v1,
)
from .omegaa_kpt1_common import KPT1LimitsV1, KPT1ResourceLimit
from .omegaa_kpt1_types import (
    KPT1_FIELD_KINDS as _KPT_FIELDS, KernelLevelTagV1,
    KernelProofTermV1, KernelTermTagV1, KernelUniverseLevelV1,
    kpt1_level_arity_v1, validate_kpt1_enum_integrity_v1,
)

logger = logging.getLogger(__name__)
_VALIDATE_BUILDER = validate_kcf1_builder_integrity_v1
_VALIDATE_BUILDER_CODE = _VALIDATE_BUILDER.__code__
_TAG_ORDINAL = kcf1_tag_ordinal_v1
_TAG_ORDINAL_CODE = _TAG_ORDINAL.__code__
_KCF_ENUM_VALIDATE = validate_kcf1_enum_integrity_v1
_KCF_ENUM_VALIDATE_CODE = _KCF_ENUM_VALIDATE.__code__
_ARITIES_FROZEN, _FIELD_KINDS_FROZEN = _ARITIES, _FIELD_KINDS
_FRAME_TAG_SLOT = vars(KernelContinuationFrameV1)["tag"]
_FRAME_FIELDS_SLOT = vars(KernelContinuationFrameV1)["fields"]
_TERM_TAG_SLOT = vars(KernelProofTermV1)["tag"]
_TERM_FIELDS_SLOT = vars(KernelProofTermV1)["fields"]
_LEVEL_TAG_SLOT = vars(KernelUniverseLevelV1)["tag"]
_LEVEL_FIELDS_SLOT = vars(KernelUniverseLevelV1)["fields"]
_KPT_CODEC = _kpt_codec_module.codec_kernel_proof_term_v1
_KPT_CODEC_CODE = _KPT_CODEC.__code__
_KPT_ENUM_VALIDATE = validate_kpt1_enum_integrity_v1
_KPT_ENUM_VALIDATE_CODE = _KPT_ENUM_VALIDATE.__code__
_KPT_LEVEL_ARITY = kpt1_level_arity_v1
_KPT_LEVEL_ARITY_CODE = _KPT_LEVEL_ARITY.__code__
_KPT_LIMITS_CLASS = KPT1LimitsV1
_KPT_LIMITS_INIT = vars(_KPT_LIMITS_CLASS)["__init__"]
_KPT_LIMITS_POST = vars(_KPT_LIMITS_CLASS)["__post_init__"]
_KPT_LIMITS_INIT_CODE = _KPT_LIMITS_INIT.__code__
_KPT_LIMITS_POST_CODE = _KPT_LIMITS_POST.__code__
_KPT_LIMIT_NAMES = (
    "max_input_bytes", "max_output_bytes", "max_depth", "max_nodes",
    "max_list_items", "max_nat_bytes",
)
_KPT_LIMIT_SLOTS = tuple(vars(_KPT_LIMITS_CLASS)[name] for name in _KPT_LIMIT_NAMES)
_KPT_RESOURCE_CLASS = KPT1ResourceLimit
_OBJECT_NEW = object.__new__

class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def _validate_kpt_dependency_integrity_v1() -> None:
    logger.debug("_validate_kpt_dependency_integrity_v1 entry")
    namespace = vars(_KPT_LIMITS_CLASS)
    drift = (
        _kpt_codec_module.codec_kernel_proof_term_v1 is not _KPT_CODEC
        or _KPT_CODEC.__code__ is not _KPT_CODEC_CODE
        or _kpt_common_module.KPT1LimitsV1 is not _KPT_LIMITS_CLASS
        or _kpt_common_module.KPT1ResourceLimit is not _KPT_RESOURCE_CLASS
        or _kpt_syntax.KernelProofTermV1 is not KernelProofTermV1
        or _kpt_syntax.KernelUniverseLevelV1 is not KernelUniverseLevelV1
        or _kpt_syntax.KernelTermTagV1 is not KernelTermTagV1
        or _kpt_syntax.KernelLevelTagV1 is not KernelLevelTagV1
        or _kpt_syntax.KPT1_FIELD_KINDS is not _KPT_FIELDS
        or _kpt_syntax.validate_kpt1_enum_integrity_v1 is not _KPT_ENUM_VALIDATE
        or _KPT_ENUM_VALIDATE.__code__ is not _KPT_ENUM_VALIDATE_CODE
        or _kpt_syntax.kpt1_level_arity_v1 is not _KPT_LEVEL_ARITY
        or _KPT_LEVEL_ARITY.__code__ is not _KPT_LEVEL_ARITY_CODE
        or namespace.get("__init__") is not _KPT_LIMITS_INIT
        or namespace.get("__post_init__") is not _KPT_LIMITS_POST
        or _KPT_LIMITS_INIT.__code__ is not _KPT_LIMITS_INIT_CODE
        or _KPT_LIMITS_POST.__code__ is not _KPT_LIMITS_POST_CODE
        or any(namespace.get(name) is not slot for name, slot in zip(
            _KPT_LIMIT_NAMES, _KPT_LIMIT_SLOTS, strict=True,
        ))
    )
    if drift:
        logger.error("_validate_kpt_dependency_integrity_v1 error drift")
        raise ValueError("kcf1-kpt-dependency-integrity")
    _KPT_ENUM_VALIDATE()
    logger.debug("_validate_kpt_dependency_integrity_v1 exit")


def _validate_codec_alias_integrity_v1() -> None:
    logger.debug("_validate_codec_alias_integrity_v1 entry")
    if (
        globals().get("validate_kcf1_builder_integrity_v1") is not _VALIDATE_BUILDER or globals().get("KPT1ResourceLimit") is not _KPT_RESOURCE_CLASS
        or _VALIDATE_BUILDER.__code__ is not _VALIDATE_BUILDER_CODE
        or globals().get("_ARITIES") is not _ARITIES_FROZEN
        or globals().get("_FIELD_KINDS") is not _FIELD_KINDS_FROZEN
        or globals().get("kcf1_tag_ordinal_v1") is not _TAG_ORDINAL
        or _TAG_ORDINAL.__code__ is not _TAG_ORDINAL_CODE
        or globals().get("validate_kcf1_enum_integrity_v1") is not _KCF_ENUM_VALIDATE
        or _KCF_ENUM_VALIDATE.__code__ is not _KCF_ENUM_VALIDATE_CODE
    ):
        logger.error("_validate_codec_alias_integrity_v1 error drift")
        raise ValueError("kcf1-codec-alias-integrity")
    logger.debug("_validate_codec_alias_integrity_v1 exit")


_VALIDATE_CODEC_ALIASES, _VALIDATE_CODEC_ALIASES_CODE = _validate_codec_alias_integrity_v1, _validate_codec_alias_integrity_v1.__code__


def _make_kpt_limits_v1(values: tuple[int, ...]) -> KPT1LimitsV1:
    logger.debug("_make_kpt_limits_v1 entry")
    _validate_kpt_dependency_integrity_v1()
    if len(values) != 6 or any(type(item) is not int or item <= 0 for item in values):
        _host_error("derived-kpt-limits")
    result = _OBJECT_NEW(_KPT_LIMITS_CLASS)
    for slot, value in zip(_KPT_LIMIT_SLOTS, values, strict=True):
        cast(_SlotSetter, slot).__set__(result, value)
    logger.debug("_make_kpt_limits_v1 exit")
    return result


def _mark_identity(value: object, seen: set[int], active: set[int], leaving: bool) -> None:
    logger.debug("_mark_identity entry leaving=%s", leaving)
    key = id(value)
    if leaving:
        active.remove(key)
    elif key in active:
        _host_error("cyclic-host-graph")
    elif key in seen:
        _host_error("shared-host-graph")
    else:
        seen.add(key)
        active.add(key)
    logger.debug("_mark_identity exit seen=%d active=%d", len(seen), len(active))


def _scan_kpt_v1(
    root: KernelProofTermV1, seen: set[int], limits: tuple[int, ...], prior: int,
) -> tuple[int, int]:
    logger.debug("_scan_kpt_v1 entry prior=%d", prior)
    nodes = 0
    deepest = 0
    active: set[int] = set()
    stack: list[tuple[str, object, int, bool]] = [("term", root, 1, False)]
    while stack:
        kind, node, depth, leaving = stack.pop()
        if leaving:
            _mark_identity(node, seen, active, True)
            continue
        _mark_identity(node, seen, active, False)
        expected = KernelProofTermV1 if kind == "term" else KernelUniverseLevelV1
        if type(node) is not expected:
            _host_error(f"{kind}-host-shape")
        nodes += 1
        deepest = max(deepest, depth)
        if 1 + prior + nodes > limits[MAX_NODES]:
            _resource(KCF1ResourceKindV1.COMPOSITE_NODES)
        if 1 + depth > limits[MAX_DEPTH]:
            _resource(KCF1ResourceKindV1.COMPOSITE_DEPTH)
        tag_slot = _TERM_TAG_SLOT if kind == "term" else _LEVEL_TAG_SLOT
        fields_slot = _TERM_FIELDS_SLOT if kind == "term" else _LEVEL_FIELDS_SLOT
        tag = _slot(tag_slot, node, f"kpt-{kind}-tag")
        raw_fields = _slot(fields_slot, node, f"kpt-{kind}-fields")
        tag_type = KernelTermTagV1 if kind == "term" else KernelLevelTagV1
        if type(tag) is not tag_type or type(raw_fields) is not tuple:
            _host_error(f"{kind}-host-shape")
        fields = cast(tuple[object, ...], raw_fields)
        if fields:
            _mark_identity(fields, seen, active, False)
            active.remove(id(fields))
        kinds = _KPT_FIELDS[cast(KernelTermTagV1, tag)] if kind == "term" else (
            ("level",) * _KPT_LEVEL_ARITY(cast(KernelLevelTagV1, tag))
        )
        if len(fields) != len(kinds):
            _host_error(f"{kind}-arity")
        children: list[tuple[str, object]] = []
        for field_kind, field in zip(kinds, fields, strict=True):
            if field_kind == "nat":
                if type(field) is not int or field < 0:
                    _host_error("nat-host-shape")
                size = (field.bit_length() + 7) // 8
                if size > limits[MAX_KPT_NAT]:
                    _resource(KCF1ResourceKindV1.KPT_NAT_BYTES)
            elif field_kind == "digest":
                if type(field) is not bytes or len(field) != 32:
                    _host_error("digest-host-shape")
            elif field_kind in {"term", "level"}:
                children.append((field_kind, field))
            else:
                if type(field) is not tuple:
                    _host_error("terms-host-shape")
                if field:
                    _mark_identity(field, seen, active, False)
                    active.remove(id(field))
                if len(field) > limits[MAX_KPT_LIST]:
                    _resource(KCF1ResourceKindV1.KPT_LIST_ITEMS)
                children.extend(("term", item) for item in field)
        stack.append((kind, node, depth, True))
        stack.extend((child_kind, child, depth + 1, False) for child_kind, child in reversed(children))
    logger.debug("_scan_kpt_v1 exit nodes=%d depth=%d", nodes, deepest)
    return nodes, deepest


def _capture_frame_v1(
    frame: KernelContinuationFrameV1, limits: tuple[int, ...],
) -> tuple[KernelContinuationTagV1, tuple[object, ...], tuple[tuple[int, int], ...]]:
    logger.debug("_capture_frame_v1 entry")
    _VALIDATE_CODEC_ALIASES()
    _VALIDATE_BUILDER(KernelContinuationFrameV1, KernelContinuationTagV1)
    _validate_kpt_dependency_integrity_v1()
    _KCF_ENUM_VALIDATE()
    if type(frame) is not KernelContinuationFrameV1:
        _host_error("frame-host-shape")
    tag = _slot(_FRAME_TAG_SLOT, frame, "frame-tag")
    raw_fields = _slot(_FRAME_FIELDS_SLOT, frame, "frame-fields")
    if type(tag) is not KernelContinuationTagV1 or type(raw_fields) is not tuple:
        _host_error("frame-host-shape")
    fields = cast(tuple[object, ...], raw_fields)
    if len(fields) != _ARITIES[tag]:
        _host_error("frame-arity")
    seen = {id(frame)}
    if fields:
        seen.add(id(fields))
    metrics: list[tuple[int, int]] = []
    prior = 0
    for position, (kind, value) in enumerate(zip(_FIELD_KINDS[tag], fields, strict=True)):
        if kind == "term":
            if type(value) is not KernelProofTermV1:
                _host_error(f"field-{position}-term")
            metric = _scan_kpt_v1(value, seen, limits, prior)
            metrics.append(metric)
            prior += metric[0]
        elif kind == "term_bytes":
            if type(value) is not bytes:
                _host_error(f"field-{position}-term-bytes")
        elif type(value) is not bytes or len(value) != 32:
            _host_error(f"field-{position}-type-id")
    logger.debug("_capture_frame_v1 exit kpt=%d nodes=%d", len(metrics), 1 + prior)
    return tag, fields, tuple(metrics)


def codec_kernel_continuation_frame_v1(
    frame: KernelContinuationFrameV1,
    limits: KCF1LimitsV1 = DEFAULT_KCF1_LIMITS_V1,
) -> bytes:
    logger.debug("codec_kernel_continuation_frame_v1 entry")
    if _VALIDATE_CODEC_ALIASES.__code__ is not _VALIDATE_CODEC_ALIASES_CODE:
        logger.error("codec_kernel_continuation_frame_v1 error alias-code-drift")
        raise ValueError("kcf1-codec-alias-integrity")
    _VALIDATE_CODEC_ALIASES()
    validate_kcf1_error_enum_integrity_v1()
    values = _snapshot_limits(limits)
    tag, fields, metrics = _capture_frame_v1(frame, values)
    payloads: list[bytes] = []
    nested = 0
    prior_nodes = 0
    metric_index = 0
    offset = 6
    for kind, value in zip(_FIELD_KINDS[tag], fields, strict=True):
        if kind == "term":
            node_count, _ = metrics[metric_index]
            remaining_nodes = values[MAX_NODES] - 1 - prior_nodes
            remaining_nested = values[MAX_NESTED] - nested
            if remaining_nested <= 0:
                _resource(KCF1ResourceKindV1.NESTED_KPT_BYTES, offset + 8)
            derived = _make_kpt_limits_v1((
                remaining_nested, values[MAX_OUTPUT],
                max(1, values[MAX_DEPTH] - 1), remaining_nodes,
                values[MAX_KPT_LIST], values[MAX_KPT_NAT],
            ))
            logger.debug("codec_kernel_continuation_frame_v1 external KPT codec")
            try:
                payload = _KPT_CODEC(cast(KernelProofTermV1, value), derived)
            except KPT1ResourceLimit as exc:
                _map_kpt_resource_v1(exc, offset + 8, _KPT_RESOURCE_CLASS)
            nested += len(payload)
            if nested > values[MAX_NESTED]:
                _resource(KCF1ResourceKindV1.NESTED_KPT_BYTES, offset + 8)
            prior_nodes += node_count
            metric_index += 1
        else:
            payload = cast(bytes, value)
        payloads.append(payload)
        offset += 8 + len(payload)
    result = KCF1_PREFIX + bytes((_TAG_ORDINAL(tag), len(payloads))) + b"".join(
        _frame(payload) for payload in payloads
    )
    if len(result) > values[MAX_OUTPUT]:
        _resource(KCF1ResourceKindV1.OUTPUT_BYTES, values[MAX_OUTPUT])
    logger.debug("codec_kernel_continuation_frame_v1 exit bytes=%d", len(result))
    return result
