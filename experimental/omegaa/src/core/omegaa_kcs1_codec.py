"""Plan-first canonical encoders and closed source identity for KCS1."""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from hashlib import sha256
import logging
import os
from pathlib import Path, PurePosixPath
import stat
from typing import NoReturn, cast
import unicodedata

from . import omegaa_kcs1_types as t
from .omegaa_kcs1_common import (
    _ARITIES,
    _DOMAIN_CLASSES,
    _DOMAIN_NAMES,
    _PREFIXES,
    _TAG_BY_CLASS,
    _encoded_arm,
    _frame,
    _integrity_arm,
    _resource_arm,
    _slot,
    _snapshot_limits,
    _u64,
    validate_kcs1_common_integrity_v1,
)
from .omegaa_kcc1_common import KCC1LimitsV1
from .omegaa_kcc1_codec import codec_empty_checker_config_v1, kcc1_source_root_v1
from .omegaa_kcc1_types import EMPTY_CHECKER_CONFIG_V1, EmptyCheckerConfigV1
from .omegaa_kcf1_common import KCF1LimitsV1
from .omegaa_kcf1_codec import codec_kernel_continuation_frame_v1
from .omegaa_kcf1_types import KCF1_FIELD_KINDS, KernelContinuationFrameV1, KernelContinuationTagV1
from .omegaa_kci1_common import KCI1LimitsV1
from .omegaa_kci1_codec import codec_checker_input_syntax_v1, kci1_source_root_v1
from .omegaa_kci1_types import CheckerInputSyntaxV1
from .omegaa_keb1_common import KEB1LimitsV1
from .omegaa_keb1_codec import codec_expected_binding_v1, keb1_source_root_v1
from .omegaa_keb1_types import ExpectedBindingSyntaxV1
from .omegaa_kpt1_common import KPT1LimitsV1
from .omegaa_kpt1_codec import codec_kernel_proof_term_v1
from .omegaa_kpt1_types import (
    KPT1_FIELD_KINDS,
    KernelLevelTagV1,
    KernelProofTermV1,
    KernelTermTagV1,
    KernelUniverseLevelV1,
)

logger = logging.getLogger(__name__)


class _Preflight(ValueError):
    def __init__(self, code: t.KCS1IntegrityCodeV1) -> None:
        logger.debug("_Preflight.__init__ entry code=%s", code.name)
        self.code = code
        super().__init__(code.name)
        logger.error("KCS1 preflight rejected code=%s", code.name)
        logger.debug("_Preflight.__init__ exit")


@dataclass(slots=True)
class _Metrics:
    nodes: int = 0
    depth: int = 0
    vector_items: int = 0
    nested_wire: int = 0
    list_items: int = 0
    nat_bytes: int = 0
    events: list[tuple[int, int, int]] = dataclass_field(default_factory=list)


def _fail(code: t.KCS1IntegrityCodeV1) -> NoReturn:
    logger.debug("_fail entry code=%s", code.name)
    logger.error("KCS1 preflight error code=%s", code.name)
    raise _Preflight(code)


def _mark(value: object, active: set[int], seen: set[int]) -> None:
    logger.debug("_mark entry")
    identity = id(value)
    if identity in active:
        _fail(t.KCS1IntegrityCodeV1.GRAPH_CYCLE)
    if identity in seen:
        _fail(t.KCS1IntegrityCodeV1.GRAPH_SHARED)
    active.add(identity)
    seen.add(identity)
    logger.debug("_mark exit")


def _finish(value: object, active: set[int]) -> None:
    logger.debug("_finish entry")
    active.remove(id(value))
    logger.debug("_finish exit")


def _measure_kpt(value: object, depth: int, metrics: _Metrics, active: set[int], seen: set[int], base: int = 0) -> int:
    logger.debug("_measure_kpt entry depth=%d base=%d", depth, base)
    if type(value) is not KernelProofTermV1:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _mark(value, active, seen)
    metrics.nodes += 1
    metrics.depth = max(metrics.depth, depth)
    metrics.events.extend(
        (
            (base, int(t.KCS1CodecResourceKindV1.COMPOSITE_DEPTH), depth),
            (base, int(t.KCS1CodecResourceKindV1.COMPOSITE_NODES), 1),
        )
    )
    tag = _slot(KernelProofTermV1, "tag", value)
    raw_fields = _slot(KernelProofTermV1, "fields", value)
    if type(tag) is not KernelTermTagV1 or type(raw_fields) is not tuple or tag not in KPT1_FIELD_KINDS:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    kinds = KPT1_FIELD_KINDS[tag]
    fields = cast(tuple[object, ...], raw_fields)
    if len(fields) != len(kinds):
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    total = 6
    for kind, field in zip(kinds, fields, strict=True):
        body = base + total + 8
        if kind == "nat":
            if type(field) is not int or field < 0:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            nat_value = field
            size = 0 if nat_value == 0 else (nat_value.bit_length() + 7) // 8
            metrics.nat_bytes += size
            metrics.events.append((body + 8, int(t.KCS1CodecResourceKindV1.NESTED_NAT_BYTES), size))
            payload = 8 + size
        elif kind == "digest":
            if type(field) is not bytes or len(field) != 32:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            payload = 32
        elif kind == "term":
            payload = _measure_kpt(field, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += payload
            metrics.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), payload))
        elif kind == "level":
            payload = _measure_level(field, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += payload
            metrics.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), payload))
        else:
            if type(field) is not tuple:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            items = cast(tuple[object, ...], field)
            metrics.list_items += len(items)
            metrics.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_LIST_ITEMS), len(items)))
            payload = 8
            for item in items:
                item_body = body + payload + 8
                item_size = _measure_kpt(item, depth + 1, metrics, active, seen, item_body)
                metrics.nested_wire += item_size
                metrics.events.append((item_body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), item_size))
                payload += 8 + item_size
        total += 8 + payload
    _finish(value, active)
    logger.debug("_measure_kpt exit bytes=%d", total)
    return total


def _measure_level(
    value: object, depth: int, metrics: _Metrics, active: set[int], seen: set[int], base: int = 0
) -> int:
    logger.debug("_measure_level entry depth=%d base=%d", depth, base)
    if type(value) is not KernelUniverseLevelV1:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _mark(value, active, seen)
    metrics.nodes += 1
    metrics.depth = max(metrics.depth, depth)
    metrics.events.extend(
        (
            (base, int(t.KCS1CodecResourceKindV1.COMPOSITE_DEPTH), depth),
            (base, int(t.KCS1CodecResourceKindV1.COMPOSITE_NODES), 1),
        )
    )
    tag = _slot(KernelUniverseLevelV1, "tag", value)
    raw_fields = _slot(KernelUniverseLevelV1, "fields", value)
    arities = (0, 1, 2)
    if type(tag) is not KernelLevelTagV1 or type(raw_fields) is not tuple:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    fields = cast(tuple[object, ...], raw_fields)
    if len(fields) != arities[object.__getattribute__(tag, "_value_")]:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    total = 1
    for child in fields:
        child_body = base + total + 8
        child_size = _measure_level(child, depth + 1, metrics, active, seen, child_body)
        metrics.nested_wire += child_size
        metrics.events.append((child_body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), child_size))
        total += 8 + child_size
    _finish(value, active)
    logger.debug("_measure_level exit bytes=%d", total)
    return total


def _measure_kcf(value: object, depth: int, metrics: _Metrics, active: set[int], seen: set[int], base: int = 0) -> int:
    logger.debug("_measure_kcf entry depth=%d base=%d", depth, base)
    if type(value) is not KernelContinuationFrameV1:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _mark(value, active, seen)
    metrics.nodes += 1
    metrics.depth = max(metrics.depth, depth)
    metrics.events.extend(((base, 2, depth), (base, 3, 1)))
    tag = _slot(KernelContinuationFrameV1, "tag", value)
    raw_fields = _slot(KernelContinuationFrameV1, "fields", value)
    if type(tag) is not KernelContinuationTagV1 or type(raw_fields) is not tuple or tag not in KCF1_FIELD_KINDS:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    kinds = KCF1_FIELD_KINDS[tag]
    fields = cast(tuple[object, ...], raw_fields)
    if len(fields) != len(kinds):
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    total = 6
    for kind, field in zip(kinds, fields, strict=True):
        body = base + total + 8
        if kind == "term":
            payload = _measure_kpt(field, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += payload
            metrics.events.append((body, 5, payload))
        elif kind == "term_bytes":
            if type(field) is not bytes:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            payload = len(field)
        else:
            if type(field) is not bytes or len(field) != 32:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            payload = 32
        total += 8 + payload
    _finish(value, active)
    logger.debug("_measure_kcf exit bytes=%d", total)
    return total


def _measure_kci(value: object, depth: int, metrics: _Metrics, active: set[int], seen: set[int], base: int = 0) -> int:
    logger.debug("_measure_kci entry depth=%d base=%d", depth, base)
    if type(value) is not CheckerInputSyntaxV1:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _mark(value, active, seen)
    metrics.nodes += 1
    metrics.depth = max(metrics.depth, depth)
    metrics.events.extend(((base, 2, depth), (base, 3, 1)))
    expected = _slot(CheckerInputSyntaxV1, "expected_bytes", value)
    term = _slot(CheckerInputSyntaxV1, "term_bytes", value)
    if type(expected) is not bytes or type(term) is not bytes:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _finish(value, active)
    result = 22 + len(expected) + len(term)
    logger.debug("_measure_kci exit bytes=%d", result)
    return result


def _measure_keb(value: object, depth: int, metrics: _Metrics, active: set[int], seen: set[int], base: int = 0) -> int:
    logger.debug("_measure_keb entry depth=%d base=%d", depth, base)
    if type(value) is not ExpectedBindingSyntaxV1:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _mark(value, active, seen)
    metrics.nodes += 1
    metrics.depth = max(metrics.depth, depth)
    metrics.events.extend(((base, 2, depth), (base, 3, 1)))
    term = _slot(ExpectedBindingSyntaxV1, "expected_term", value)
    wire = _slot(ExpectedBindingSyntaxV1, "expected_wire", value)
    if type(wire) is not bytes:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    first_body = base + 14
    before = len(metrics.events)
    nested_before = metrics.nested_wire
    size = _measure_kpt(term, depth + 1, metrics, active, seen, first_body)
    if len(wire) != size:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    nested_delta = metrics.nested_wire - nested_before
    metrics.nested_wire += nested_delta + size * 2
    metrics.events.append((first_body, 5, size))
    second_body = base + 22 + size
    duplicated = tuple(
        (second_body + offset - first_body, kind, amount) for offset, kind, amount in metrics.events[before:]
    )
    metrics.events.extend(duplicated)
    first_nodes = sum(1 for _, kind, _ in metrics.events[before:] if kind == 3) // 2
    first_lists = sum(amount for _, kind, amount in metrics.events[before:] if kind == 6) // 2
    first_nats = sum(amount for _, kind, amount in metrics.events[before:] if kind == 7) // 2
    metrics.nodes += first_nodes
    metrics.list_items += first_lists
    metrics.nat_bytes += first_nats
    _finish(value, active)
    result = 22 + size * 2
    logger.debug("_measure_keb exit bytes=%d", result)
    return result


def _measure_kcc(value: object, depth: int, metrics: _Metrics, active: set[int], seen: set[int], base: int = 0) -> int:
    logger.debug("_measure_kcc entry depth=%d base=%d", depth, base)
    if value is not EMPTY_CHECKER_CONFIG_V1:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _mark(value, active, seen)
    metrics.nodes += 1
    metrics.depth = max(metrics.depth, depth)
    metrics.events.extend(((base, 2, depth), (base, 3, 1)))
    _finish(value, active)
    logger.debug("_measure_kcc exit bytes=6")
    return 6


def _fields(
    value: object,
    domain_index: int,
    depth: int,
    metrics: _Metrics,
    active: set[int],
    seen: set[int],
    base: int = 0,
) -> tuple[int, tuple[tuple[str, object], ...]]:
    logger.debug("_fields entry domain=%s depth=%d base=%d", _DOMAIN_NAMES[domain_index], depth, base)
    cls = type(value)
    if cls not in _DOMAIN_CLASSES[domain_index]:
        _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _mark(value, active, seen)
    metrics.nodes += 1
    metrics.depth = max(metrics.depth, depth)
    metrics.events.extend(((base, 2, depth), (base, 3, 1)))
    tag = _TAG_BY_CLASS[domain_index][cls]
    names = cast(tuple[str, ...], getattr(cls, "__slots__", ()))
    values = tuple(_slot(cls, name, value) for name in names)
    if len(values) != _ARITIES[domain_index][tag]:
        _fail(t.KCS1IntegrityCodeV1.SLOT_DRIFT)
    kinds: tuple[str, ...]
    if domain_index == 0:
        kinds = (("keb",), ("bytes",), ("kpt",), ("kpt",), ("kpt", "kpt", "kpt"), ("bytes32",))[tag]
    elif domain_index == 1:
        kinds = (("kcn", "kcc", "kci", "vec-kpt", "vec-kpt", "vec-kcf", "u64"), ("kpt", "bytes32"), ("reject", "u64"))[
            tag
        ]
    elif domain_index == 2:
        kinds = (("kpt",), ("kpt",))[tag]
    elif domain_index == 3:
        kinds = (("u64",), ("nat",), ("nat",), ())[tag]
    elif domain_index == 4:
        kinds = ("attempt-kind", "nat", "nat", "krl")
    else:
        kinds = (("terminal",), ("krf",), ("internal", "krl"))[tag]
    result = tuple(zip(kinds, values, strict=True))
    logger.debug("_fields exit tag=%d", tag)
    return tag, result


def _plan(
    value: object,
    domain_index: int,
    depth: int,
    metrics: _Metrics,
    active: set[int],
    seen: set[int],
    base: int = 0,
) -> int:
    logger.debug("_plan entry domain=%s depth=%d base=%d", _DOMAIN_NAMES[domain_index], depth, base)
    tag, fields = _fields(value, domain_index, depth, metrics, active, seen, base)
    total = 6
    for kind, field in fields:
        body = base + total + 8
        if kind == "bytes":
            if type(field) is not bytes:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            size = len(field)
        elif kind == "bytes32":
            if type(field) is not bytes or len(field) != 32:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            size = 32
        elif kind == "u64":
            if type(field) is not int or not 0 <= field < 2**64:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            size = 8
        elif kind == "nat":
            if type(field) is not int or field < 0:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            nat_value = field
            magnitude = 0 if nat_value == 0 else (nat_value.bit_length() + 7) // 8
            metrics.nat_bytes += magnitude
            metrics.events.append((body + 8, 7, magnitude))
            size = 8 + magnitude
        elif kind in {"reject", "attempt-kind", "internal"}:
            enum_cls = {
                "reject": t.KCS1RejectCodeSyntaxV1,
                "attempt-kind": t.KCS1AttemptResourceKindV1,
                "internal": t.KCS1InternalCodeV1,
            }[kind]
            if type(field) is not enum_cls:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            size = 1
        elif kind == "kpt":
            size = _measure_kpt(field, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += size
            metrics.events.append((body, 5, size))
        elif kind == "kcf":
            size = _measure_kcf(field, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += size
            metrics.events.append((body, 5, size))
        elif kind == "kci":
            size = _measure_kci(field, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += size
            metrics.events.append((body, 5, size))
        elif kind == "keb":
            size = _measure_keb(field, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += size
            metrics.events.append((body, 5, size))
        elif kind == "kcc":
            size = _measure_kcc(field, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += size
            metrics.events.append((body, 5, size))
        elif kind in {"kcn", "krl", "krf"}:
            child_index = {"kcn": 0, "krl": 3, "krf": 4}[kind]
            size = _plan(field, child_index, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += size
            metrics.events.append((body, 5, size))
        elif kind.startswith("vec-"):
            if type(field) is not tuple:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            items = cast(tuple[object, ...], field)
            metrics.vector_items += len(items)
            metrics.events.append((body, 4, len(items)))
            size = 8
            for item in items:
                item_body = body + size + 8
                item_size = (
                    _measure_kpt(item, depth + 1, metrics, active, seen, item_body)
                    if kind == "vec-kpt"
                    else _measure_kcf(item, depth + 1, metrics, active, seen, item_body)
                )
                metrics.nested_wire += item_size
                metrics.events.append((item_body, 5, item_size))
                size += 8 + item_size
        elif kind == "terminal":
            if type(field) is t.KCS1RunStateV1:
                _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
            size = _plan(field, 1, depth + 1, metrics, active, seen, body)
            metrics.nested_wire += size
            metrics.events.append((body, 5, size))
        else:
            _fail(t.KCS1IntegrityCodeV1.INTERNAL_INVARIANT)
        total += 8 + size
    if domain_index == 4:
        relation_kind = cast(t.KCS1AttemptResourceKindV1, fields[0][1])
        allowed = fields[1][1]
        required = fields[2][1]
        locus = fields[3][1]
        locus_map = {
            0: t.KCS1InputOffsetLocusV1,
            1: t.KCS1NoLocusV1,
            2: t.KCS1StructuralCountLocusV1,
            3: t.KCS1StructuralCountLocusV1,
            4: t.KCS1StructuralCountLocusV1,
            5: t.KCS1StructuralCountLocusV1,
            6: t.KCS1StructuralCountLocusV1,
            7: t.KCS1StructuralCountLocusV1,
            8: t.KCS1StateStepLocusV1,
            9: t.KCS1StateStepLocusV1,
            10: t.KCS1StructuralCountLocusV1,
        }
        if (
            type(allowed) is not int
            or type(required) is not int
            or allowed < 0
            or required <= allowed
            or type(locus) is not locus_map[object.__getattribute__(relation_kind, "_value_")]
        ):
            _fail(t.KCS1IntegrityCodeV1.HOST_SHAPE)
    _finish(value, active)
    logger.debug("_plan exit bytes=%d", total)
    return total


def _dependency_wire(kind: str, value: object) -> bytes:
    logger.debug("_dependency_wire entry kind=%s", kind)
    logger.debug("_dependency_wire external call kind=%s", kind)
    big = 2**63
    if kind == "kpt":
        return cast(
            bytes,
            codec_kernel_proof_term_v1(cast(KernelProofTermV1, value), KPT1LimitsV1(big, big, 128, 20_000, 4096, 64)),
        )
    if kind == "kcf":
        return cast(
            bytes,
            codec_kernel_continuation_frame_v1(
                cast(KernelContinuationFrameV1, value), KCF1LimitsV1(big, big, 128, 20_000, big, 4096, 64)
            ),
        )
    if kind == "kci":
        item = cast(CheckerInputSyntaxV1, value)
        a = cast(bytes, _slot(CheckerInputSyntaxV1, "expected_bytes", item))
        b = cast(bytes, _slot(CheckerInputSyntaxV1, "term_bytes", item))
        return cast(bytes, codec_checker_input_syntax_v1(item, KCI1LimitsV1(big, big, max(1, len(a)), max(1, len(b)))))
    if kind == "keb":
        return cast(
            bytes,
            codec_expected_binding_v1(
                cast(ExpectedBindingSyntaxV1, value), KEB1LimitsV1(big, big, 129, 20_000, big, 4096, 64, big)
            ),
        )
    if kind == "kcc":
        return cast(bytes, codec_empty_checker_config_v1(cast(EmptyCheckerConfigV1, value), KCC1LimitsV1(big, big)))
    raise ValueError("kcs1-dependency-kind")


def _encode(value: object, domain_index: int) -> bytes:
    logger.debug("_encode entry domain=%s", _DOMAIN_NAMES[domain_index])
    tag, fields = _fields(value, domain_index, 0, _Metrics(), set(), set())
    payloads: list[bytes] = []
    for kind, field in fields:
        if kind == "bytes" or kind == "bytes32":
            payload = cast(bytes, field)
        elif kind == "u64":
            payload = _u64(cast(int, field))
        elif kind == "nat":
            from .omegaa_kcs1_common import _nat

            payload = _nat(cast(int, field))
        elif kind in {"reject", "attempt-kind", "internal"}:
            payload = bytes((object.__getattribute__(field, "_value_"),))
        elif kind in {"kpt", "kcf", "kci", "keb", "kcc"}:
            payload = _dependency_wire(kind, field)
        elif kind in {"kcn", "krl", "krf"}:
            payload = _encode(field, {"kcn": 0, "krl": 3, "krf": 4}[kind])
        elif kind.startswith("vec-"):
            dep = "kpt" if kind == "vec-kpt" else "kcf"
            items = cast(tuple[object, ...], field)
            payload = _u64(len(items)) + b"".join(_frame(_dependency_wire(dep, item)) for item in items)
        elif kind == "terminal":
            payload = _encode(field, 1)
        else:
            raise ValueError("kcs1-encode-kind")
        payloads.append(payload)
    result = _PREFIXES[domain_index] + bytes((tag, len(payloads))) + b"".join(_frame(payload) for payload in payloads)
    logger.debug("_encode exit bytes=%d", len(result))
    return result


def _metric_excess(metrics: _Metrics, values: tuple[int, ...]) -> tuple[int, int, int, int] | None:
    logger.debug("_metric_excess entry events=%d", len(metrics.events))
    totals = [0] * 8
    candidates: list[tuple[int, int, int, int]] = []
    for offset, ordinal, amount in sorted(metrics.events, key=lambda item: (item[0], item[1])):
        allowed = values[ordinal]
        required = amount if ordinal == 2 else totals[ordinal] + amount
        if required > allowed:
            candidates.append((offset, ordinal, allowed, required))
        totals[ordinal] = max(totals[ordinal], amount) if ordinal == 2 else required
    result = min(candidates) if candidates else None
    logger.debug("_metric_excess exit found=%s", result is not None)
    return result


def _codec(domain: str, value: object, limits: t.KCS1CodecLimitsV1) -> object:
    logger.debug("_codec entry domain=%s", domain)
    try:
        _validate_codec_public_v1()
        values = _snapshot_limits(limits)
        index = _DOMAIN_NAMES.index(domain)
        metrics = _Metrics()
        size = _plan(value, index, 0, metrics, set(), set())
        excess = _metric_excess(metrics, values)
        if excess is not None:
            offset, ordinal, allowed, required = excess
            return _resource_arm(domain, t.KCS1CodecResourceKindV1(ordinal), allowed, required, offset)
        if size > values[1]:
            return _resource_arm(domain, t.KCS1CodecResourceKindV1.OUTPUT_BYTES, values[1], size, 0)
        wire = _encode(value, index)
        if len(wire) != size:
            return _integrity_arm(domain, t.KCS1IntegrityCodeV1.INTERNAL_INVARIANT)
        result = _encoded_arm(domain, wire)
        logger.debug("_codec exit domain=%s bytes=%d", domain, len(wire))
        return result
    except _Preflight as exc:
        return _integrity_arm(domain, exc.code)
    except Exception as exc:
        logger.error("_codec error domain=%s exception=%s", domain, type(exc).__name__)
        return _integrity_arm(domain, t.KCS1IntegrityCodeV1.HOST_SHAPE)


def codec_kcn1_v1(
    value: t.CheckerNodeSyntaxV1, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1
) -> t.KCN1EncodeResultV1:
    logger.debug("codec_kcn1_v1 entry")
    result = cast(t.KCN1EncodeResultV1, _codec("KCN1", value, limits))
    logger.debug("codec_kcn1_v1 exit")
    return result


def codec_kcs1_v1(
    value: t.CheckerStateSyntaxV1, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1
) -> t.KCS1EncodeResultV1:
    logger.debug("codec_kcs1_v1 entry")
    result = cast(t.KCS1EncodeResultV1, _codec("KCS1", value, limits))
    logger.debug("codec_kcs1_v1 exit")
    return result


def codec_krr1_v1(
    value: t.ReductionResultSyntaxV1, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1
) -> t.KRR1EncodeResultV1:
    logger.debug("codec_krr1_v1 entry")
    result = cast(t.KRR1EncodeResultV1, _codec("KRR1", value, limits))
    logger.debug("codec_krr1_v1 exit")
    return result


def codec_krl1_v1(
    value: t.ResourceLocusSyntaxV1, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1
) -> t.KRL1EncodeResultV1:
    logger.debug("codec_krl1_v1 entry")
    result = cast(t.KRL1EncodeResultV1, _codec("KRL1", value, limits))
    logger.debug("codec_krl1_v1 exit")
    return result


def codec_krf1_v1(
    value: t.KCS1AttemptResourceSyntaxV1, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1
) -> t.KRF1EncodeResultV1:
    logger.debug("codec_krf1_v1 entry")
    result = cast(t.KRF1EncodeResultV1, _codec("KRF1", value, limits))
    logger.debug("codec_krf1_v1 exit")
    return result


def codec_kar1_v1(
    value: t.CheckerAttemptSyntaxV1, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1
) -> t.KAR1EncodeResultV1:
    logger.debug("codec_kar1_v1 entry")
    result = cast(t.KAR1EncodeResultV1, _codec("KAR1", value, limits))
    logger.debug("codec_kar1_v1 exit")
    return result


_CODEC_FUNCTIONS = (codec_kcn1_v1, codec_kcs1_v1, codec_krr1_v1, codec_krl1_v1, codec_krf1_v1, codec_kar1_v1)
_CODEC_NAMES = tuple(function.__name__ for function in _CODEC_FUNCTIONS)
_CODEC_CODES = tuple(function.__code__ for function in _CODEC_FUNCTIONS)


def _validate_codec_public_v1() -> None:
    logger.debug("_validate_codec_public_v1 entry")
    if any(
        globals().get(name) is not function
        or function.__code__ is not code
        or type(function.__defaults__) is not tuple
        or len(cast(tuple[object, ...], function.__defaults__)) != 1
        or cast(tuple[object, ...], function.__defaults__)[0] is not t.DEFAULT_KCS1_CODEC_LIMITS_V1
        for name, function, code in zip(_CODEC_NAMES, _CODEC_FUNCTIONS, _CODEC_CODES, strict=True)
    ):
        raise ValueError("kcs1-codec-public-drift")
    logger.debug("_validate_codec_public_v1 exit")


KCS1_SOURCE_PATHS_V1 = (
    "src/core/omegaa_kcs1_builder.py",
    "src/core/omegaa_kcs1_codec.py",
    "src/core/omegaa_kcs1_common.py",
    "src/core/omegaa_kcs1_parser.py",
    "src/core/omegaa_kcs1_types.py",
)
_SOURCE_PATHS = KCS1_SOURCE_PATHS_V1
_ROOT = Path(__file__).parents[2]
_ROOT_FROZEN = _ROOT
_ROOT_TYPE = type(_ROOT_FROZEN)
_KPT_ROOT = bytes.fromhex("55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a")
_KCA_ROOT = bytes.fromhex("e98c6e880727148d05c4d061192f842a71d77a28d65a704cfc7fa63194cc301c")
_KCF_ROOT = bytes.fromhex("95d24a28eb0a3a0f09ed7e8621d0e27b83de87e25efeb1aa641bbeb345ce22bf")
_KCI_ROOT_FN = kci1_source_root_v1
_KEB_ROOT_FN = keb1_source_root_v1
_KCC_ROOT_FN = kcc1_source_root_v1
_ROOT_FN_CODES = (_KCI_ROOT_FN.__code__, _KEB_ROOT_FN.__code__, _KCC_ROOT_FN.__code__)


def _read_source(name: str) -> bytes:
    logger.debug("_read_source entry name=%s", name)
    if globals().get("_ROOT") is not _ROOT_FROZEN or type(_ROOT_FROZEN) is not _ROOT_TYPE:
        raise ValueError("kcs1-source-root-drift")
    if type(name) is not str or unicodedata.normalize("NFC", name) != name:
        raise ValueError("kcs1-source-name")
    pure = PurePosixPath(name)
    if pure.is_absolute() or str(pure) != name or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("kcs1-source-path")
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    directory = os.open(_ROOT, flags | os.O_DIRECTORY)
    file_fd = -1
    try:
        for part in pure.parts[:-1]:
            next_fd = os.open(part, flags | os.O_DIRECTORY, dir_fd=directory)
            os.close(directory)
            directory = next_fd
        file_fd = os.open(pure.parts[-1], flags, dir_fd=directory)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("kcs1-source-regular")
        chunks = []
        while True:
            chunk = os.read(file_fd, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(file_fd)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("kcs1-source-drift")
        result = b"".join(chunks)
        logger.debug("_read_source exit bytes=%d", len(result))
        return result
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        os.close(directory)


def _manifest() -> bytes:
    logger.debug("_manifest entry")
    if (
        globals().get("KCS1_SOURCE_PATHS_V1") is not _SOURCE_PATHS
        or _SOURCE_PATHS != tuple(sorted(_SOURCE_PATHS))
        or len(set(_SOURCE_PATHS)) != 5
    ):
        raise ValueError("kcs1-source-manifest")
    result = _u64(5) + b"".join(_frame(name.encode()) + _frame(_read_source(name)) for name in _SOURCE_PATHS)
    logger.debug("_manifest exit bytes=%d", len(result))
    return result


def kcs1_source_root_v1() -> bytes:
    """Compute the exact seven-field acyclic KCS1 source root."""
    logger.debug("kcs1_source_root_v1 entry")
    validate_kcs1_common_integrity_v1()
    functions = (kci1_source_root_v1, keb1_source_root_v1, kcc1_source_root_v1)
    expected = (_KCI_ROOT_FN, _KEB_ROOT_FN, _KCC_ROOT_FN)
    if any(
        function is not frozen or function.__code__ is not code
        for function, frozen, code in zip(functions, expected, _ROOT_FN_CODES, strict=True)
    ):
        raise ValueError("kcs1-prerequisite-root-drift")
    roots = (
        _KPT_ROOT,
        _KCA_ROOT,
        _KCF_ROOT,
        kci1_source_root_v1(),
        keb1_source_root_v1(),
        kcc1_source_root_v1(),
        _manifest(),
    )
    if any(type(root) is not bytes or len(root) != 32 for root in roots[:6]):
        raise ValueError("kcs1-prerequisite-root")
    result = sha256(_frame(b"omegaa.kcs1-source.v1") + b"".join(_frame(root) for root in roots)).digest()
    logger.debug("kcs1_source_root_v1 exit")
    return result
