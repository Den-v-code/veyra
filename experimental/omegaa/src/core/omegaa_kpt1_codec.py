"""Bounded canonical codec/parser for the reviewed private KPT1 namespace."""

from __future__ import annotations

import logging
from typing import cast

from .omegaa_kpt1_common import (
    DEFAULT_KPT1_LIMITS_V1,
    KPT1_PREFIX,
    KPT1DecodeCodeV1 as KPT1DecodeCodeV1,
    KPT1DecodeError as KPT1DecodeError,
    KPT1LimitsV1,
    KPT1ResourceLimit as KPT1ResourceLimit,
    MAX_DEPTH,
    MAX_LIST,
    MAX_NAT,
    MAX_NODES,
    MAX_OUTPUT,
    _host_error,
    _resource,
    _slot,
    _snapshot_limits,
)

from .omegaa_kpt1_types import (
    KPT1_FIELD_KINDS as _FIELD_KINDS,
    KernelLevelTagV1,
    KernelProofTermV1,
    KernelTermTagV1,
    KernelUniverseLevelV1,
    kpt1_level_arity_v1,
    kpt1_level_ordinal_v1,
    kpt1_term_ordinal_v1,
    validate_kpt1_enum_integrity_v1,
)

logger = logging.getLogger(__name__)
_TERM_TAG_SLOT = vars(KernelProofTermV1)["tag"]
_TERM_FIELDS_SLOT = vars(KernelProofTermV1)["fields"]
_LEVEL_TAG_SLOT = vars(KernelUniverseLevelV1)["tag"]
_LEVEL_FIELDS_SLOT = vars(KernelUniverseLevelV1)["fields"]


def _check_slot_descriptors() -> None:
    logger.debug("_check_slot_descriptors entry")
    expected = (
        (KernelProofTermV1, "tag", _TERM_TAG_SLOT),
        (KernelProofTermV1, "fields", _TERM_FIELDS_SLOT),
        (KernelUniverseLevelV1, "tag", _LEVEL_TAG_SLOT),
        (KernelUniverseLevelV1, "fields", _LEVEL_FIELDS_SLOT),
    )
    if any(vars(owner).get(name) is not descriptor for owner, name, descriptor in expected):
        logger.error("_check_slot_descriptors error class-monkeypatch")
        raise ValueError("KPT1 slot descriptor integrity failure")
    logger.debug("_check_slot_descriptors exit")


def _mag_size(value: int, limits: tuple[int, ...]) -> int:
    logger.debug("_mag_size entry")
    size = 0 if value == 0 else (value.bit_length() + 7) // 8
    if size > limits[MAX_NAT]:
        _resource("max_nat_bytes")
    logger.debug("_mag_size exit size=%d", size)
    return size


def _preflight(
    root: KernelProofTermV1, limits: tuple[int, ...],
) -> tuple[dict[int, tuple[KernelTermTagV1, tuple[object, ...]]], dict[int, tuple[KernelLevelTagV1, tuple[object, ...]]], int]:
    logger.debug("_preflight entry")
    _check_slot_descriptors()
    validate_kpt1_enum_integrity_v1()
    if type(root) is not KernelProofTermV1:
        _host_error("term-host-shape")
    terms: dict[int, tuple[KernelTermTagV1, tuple[object, ...]]] = {}
    levels: dict[int, tuple[KernelLevelTagV1, tuple[object, ...]]] = {}
    sizes: dict[int, int] = {}
    active: set[int] = set()
    nodes = 0
    stack: list[tuple[str, object, int, bool]] = [("term", root, 0, False)]
    while stack:
        kind, node, depth, leaving = stack.pop()
        key = id(node)
        if leaving:
            active.remove(key)
            if kind == "level":
                _, level_fields = levels[key]
                sizes[key] = 1 + sum(8 + sizes[id(child)] for child in level_fields)
            else:
                term_tag, term_fields = terms[key]
                total = 6
                for field_kind, field in zip(_FIELD_KINDS[term_tag], term_fields, strict=True):
                    if field_kind == "nat":
                        payload = 8 + _mag_size(cast(int, field), limits)
                    elif field_kind == "digest":
                        payload = 32
                    elif field_kind in {"term", "level"}:
                        payload = sizes[id(field)]
                    else:
                        items = cast(tuple[KernelProofTermV1, ...], field)
                        payload = 8 + sum(8 + sizes[id(item)] for item in items)
                    total += 8 + payload
                sizes[key] = total
            continue
        nodes += 1
        if nodes > limits[MAX_NODES]:
            _resource("max_nodes")
        if depth > limits[MAX_DEPTH]:
            _resource("max_depth")
        if key in active:
            _host_error("cyclic-host-graph")
        if key in sizes:
            continue
        expected_type = KernelProofTermV1 if kind == "term" else KernelUniverseLevelV1
        if type(node) is not expected_type:
            _host_error(f"{kind}-host-shape")
        if kind == "term":
            raw_tag = _slot(_TERM_TAG_SLOT, node, "term-tag")
            raw_fields = _slot(_TERM_FIELDS_SLOT, node, "term-fields")
            if type(raw_tag) is not KernelTermTagV1 or type(raw_fields) is not tuple:
                _host_error("term-host-shape")
            term_tag = raw_tag
            fields = cast(tuple[object, ...], raw_fields)
            kinds = _FIELD_KINDS[term_tag]
            if len(fields) != len(kinds):
                _host_error("term-arity")
            terms[key] = (term_tag, fields)
        else:
            raw_tag = _slot(_LEVEL_TAG_SLOT, node, "level-tag")
            raw_fields = _slot(_LEVEL_FIELDS_SLOT, node, "level-fields")
            if type(raw_tag) is not KernelLevelTagV1 or type(raw_fields) is not tuple:
                _host_error("level-host-shape")
            level_tag = raw_tag
            fields = cast(tuple[object, ...], raw_fields)
            level_arity = kpt1_level_arity_v1(level_tag)
            if len(fields) != level_arity:
                _host_error("level-arity")
            levels[key] = (level_tag, fields)
            kinds = ("level",) * level_arity
        children: list[tuple[str, object]] = []
        for field_kind, field in zip(kinds, fields, strict=True):
            if field_kind == "nat":
                if type(field) is not int or field < 0:
                    _host_error("nat-host-shape")
                _mag_size(field, limits)
            elif field_kind == "digest":
                if type(field) is not bytes or len(field) != 32:
                    _host_error("digest-host-shape")
            elif field_kind in {"term", "level"}:
                children.append((field_kind, field))
            else:
                if type(field) is not tuple:
                    _host_error("terms-host-shape")
                if len(field) > limits[MAX_LIST]:
                    _resource("max_list_items")
                children.extend(("term", item) for item in field)
        active.add(key)
        stack.append((kind, node, depth, True))
        stack.extend((child_kind, child, depth + 1, False) for child_kind, child in reversed(children))
    total = sizes[id(root)]
    if total > limits[MAX_OUTPUT]:
        _resource("max_output_bytes")
    logger.debug("_preflight exit nodes=%d bytes=%d", nodes, total)
    return terms, levels, total


def _u64(value: int) -> bytes:
    logger.debug("_u64 entry")
    result = value.to_bytes(8, "big")
    logger.debug("_u64 exit")
    return result


def _frame(payload: bytes) -> bytes:
    logger.debug("_frame entry bytes=%d", len(payload))
    result = _u64(len(payload)) + payload
    logger.debug("_frame exit bytes=%d", len(result))
    return result


def codec_kernel_proof_term_v1(
    term: KernelProofTermV1, limits: KPT1LimitsV1 = DEFAULT_KPT1_LIMITS_V1,
) -> bytes:
    """Encode one exact KPT1 term after iterative hostile-safe preflight."""
    logger.debug("codec_kernel_proof_term_v1 entry")
    limit_values = _snapshot_limits(limits)
    terms, levels, expected_size = _preflight(term, limit_values)
    def encode_level(level: KernelUniverseLevelV1) -> bytes:
        logger.debug("encode_level entry")
        tag, fields = levels[id(level)]
        children = cast(tuple[KernelUniverseLevelV1, ...], fields)
        result = bytes((kpt1_level_ordinal_v1(tag),)) + b"".join(_frame(encode_level(child)) for child in children)
        logger.debug("encode_level exit bytes=%d", len(result))
        return result
    def encode_term(node: KernelProofTermV1) -> bytes:
        logger.debug("encode_term entry")
        tag, fields = terms[id(node)]
        payloads: list[bytes] = []
        for kind, field in zip(_FIELD_KINDS[tag], fields, strict=True):
            if kind == "nat":
                value = cast(int, field)
                size = _mag_size(value, limit_values)
                magnitude = value.to_bytes(size, "big")
                payloads.append(_frame(magnitude))
            elif kind == "digest":
                payloads.append(cast(bytes, field))
            elif kind == "level":
                payloads.append(encode_level(cast(KernelUniverseLevelV1, field)))
            elif kind == "term":
                payloads.append(encode_term(cast(KernelProofTermV1, field)))
            else:
                items = cast(tuple[KernelProofTermV1, ...], field)
                payloads.append(_u64(len(items)) + b"".join(_frame(encode_term(item)) for item in items))
        result = KPT1_PREFIX + bytes((kpt1_term_ordinal_v1(tag), len(payloads))) + b"".join(_frame(item) for item in payloads)
        logger.debug("encode_term exit bytes=%d", len(result))
        return result

    result = encode_term(term)
    if len(result) != expected_size:
        logger.error("codec_kernel_proof_term_v1 error size-mismatch")
        raise RuntimeError("KPT1 preflight size mismatch")
    logger.debug("codec_kernel_proof_term_v1 exit bytes=%d", len(result))
    return result
