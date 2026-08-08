"""Canonical private KCA1 encoder with bounded hostile AST preflight."""

from __future__ import annotations

import logging
from typing import cast

from .omegaa_kca1_common import (
    DEFAULT_KCA1_LIMITS_V1,
    KCA1_PREFIX,
    MAX_DEPTH,
    MAX_NAT,
    MAX_NODES,
    MAX_OUTPUT,
    KCA1DecodeCodeV1,
    KCA1LimitsV1,
    decode_code_ordinal_v1,
    _host_error,
    _resource,
    _slot,
    _snapshot_limits,
)
from .omegaa_kca1_types import (
    KCA1_ARITIES as _ARITIES,
    KCA1_FIELD_KINDS as _FIELD_KINDS,
    KernelCheckerASTV1,
    KernelCheckerTagV1,
    _literal_ok,
    kca1_mode_type_v1,
    kca1_tag_ordinal_v1,
    validate_kca1_enum_integrity_v1,
)

logger = logging.getLogger(__name__)
_TAG_SLOT = vars(KernelCheckerASTV1)["tag"]
_FIELDS_SLOT = vars(KernelCheckerASTV1)["fields"]


def _mag_size(value: int, limits: tuple[int, ...]) -> int:
    logger.debug("_mag_size entry")
    size = (value.bit_length() + 7) // 8
    if size > limits[MAX_NAT]:
        _resource("max_nat_bytes")
    logger.debug("_mag_size exit bytes=%d", size)
    return size


def _field_size(kind: str, value: object, limits: tuple[int, ...]) -> int:
    logger.debug("_field_size entry kind=%s", kind)
    if kind == "ast":
        _host_error("ast-size-not-ready")
    if kind == "literal":
        if not _literal_ok(value):
            _host_error("literal-host-shape")
        result = len(cast(bytes, value))
    elif kind == "bytes":
        if type(value) is not bytes:
            _host_error("bytes-host-shape")
        result = len(value)
    elif kind == "nat":
        if type(value) is not int or value < 0:
            _host_error("nat-host-shape")
        result = 8 + _mag_size(value, limits)
    elif kind == "u8":
        if type(value) is not int or not 0 <= value <= 255:
            _host_error("u8-host-shape")
        result = 1
    elif kind == "decode_code":
        if type(value) is not KCA1DecodeCodeV1:
            _host_error("decode-code-host-shape")
        result = 1
    else:
        mode_type = kca1_mode_type_v1(kind)
        if type(value) is not mode_type:
            _host_error(f"{kind}-host-shape")
        result = 1
    logger.debug("_field_size exit bytes=%d", result)
    return result


def _capture_ast(
    root: KernelCheckerASTV1, limits: tuple[int, ...],
) -> tuple[dict[int, tuple[KernelCheckerTagV1, tuple[object, ...]]], dict[int, int], int]:
    logger.debug("_capture_ast entry")
    validate_kca1_enum_integrity_v1()
    if vars(KernelCheckerASTV1).get("tag") is not _TAG_SLOT or vars(
        KernelCheckerASTV1,
    ).get("fields") is not _FIELDS_SLOT:
        _host_error("ast-slot-descriptor-integrity")
    records: dict[int, tuple[KernelCheckerTagV1, tuple[object, ...]]] = {}
    sizes: dict[int, int] = {}
    active: set[int] = set()
    seen: set[int] = set()
    stack: list[tuple[object, int, bool]] = [(root, 0, False)]
    nodes = 0
    while stack:
        node, depth, exiting = stack.pop()
        key = id(node)
        if exiting:
            tag, fields = records[key]
            size = 6
            for kind, value in zip(_FIELD_KINDS[tag], fields, strict=True):
                payload_size = sizes[id(value)] if kind == "ast" else _field_size(kind, value, limits)
                size += 8 + payload_size
            sizes[key] = size
            active.remove(key)
            continue
        if key in active:
            _host_error("cyclic-host-graph")
        if key in seen:
            _host_error("shared-host-graph")
        seen.add(key)
        nodes += 1
        if nodes > limits[MAX_NODES]:
            _resource("max_nodes")
        if depth > limits[MAX_DEPTH]:
            _resource("max_depth")
        if type(node) is not KernelCheckerASTV1:
            _host_error("ast-host-shape")
        raw_tag = _slot(_TAG_SLOT, node, "ast-tag")
        raw_fields = _slot(_FIELDS_SLOT, node, "ast-fields")
        if type(raw_tag) is not KernelCheckerTagV1 or type(raw_fields) is not tuple:
            _host_error("ast-host-shape")
        tag = raw_tag
        fields = cast(tuple[object, ...], raw_fields)
        kinds = _FIELD_KINDS[tag]
        if len(fields) != _ARITIES[tag]:
            _host_error("ast-arity")
        records[key] = (tag, fields)
        active.add(key)
        stack.append((node, depth, True))
        for kind, value in reversed(tuple(zip(kinds, fields, strict=True))):
            if kind == "ast":
                stack.append((value, depth + 1, False))
            else:
                _field_size(kind, value, limits)
    total = sizes[id(root)]
    if total > limits[MAX_OUTPUT]:
        _resource("max_output_bytes")
    logger.debug("_capture_ast exit nodes=%d bytes=%d", nodes, total)
    return records, sizes, total


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


def codec_kernel_checker_ast_v1(
    ast: KernelCheckerASTV1, limits: KCA1LimitsV1 = DEFAULT_KCA1_LIMITS_V1,
) -> bytes:
    """Encode one exact KCA1 syntax tree; never execute it."""
    logger.debug("codec_kernel_checker_ast_v1 entry")
    limit_values = _snapshot_limits(limits)
    records, _, expected_size = _capture_ast(ast, limit_values)

    def encode(node: KernelCheckerASTV1) -> bytes:
        logger.debug("encode entry")
        tag, fields = records[id(node)]
        payloads: list[bytes] = []
        for kind, value in zip(_FIELD_KINDS[tag], fields, strict=True):
            if kind == "ast":
                payload = encode(cast(KernelCheckerASTV1, value))
            elif kind in {"literal", "bytes"}:
                payload = cast(bytes, value)
            elif kind == "nat":
                number = cast(int, value)
                payload = _frame(number.to_bytes(_mag_size(number, limit_values), "big"))
            elif kind == "u8":
                payload = bytes((cast(int, value),))
            elif kind == "decode_code":
                payload = bytes((decode_code_ordinal_v1(cast(KCA1DecodeCodeV1, value)),))
            else:
                payload = b"\x00"
            payloads.append(_frame(payload))
        result = KCA1_PREFIX + bytes((kca1_tag_ordinal_v1(tag), len(payloads))) + b"".join(payloads)
        logger.debug("encode exit bytes=%d", len(result))
        return result

    result = encode(ast)
    if len(result) != expected_size:
        logger.error("codec_kernel_checker_ast_v1 error size-mismatch")
        raise RuntimeError("KCA1 preflight size mismatch")
    logger.debug("codec_kernel_checker_ast_v1 exit bytes=%d", len(result))
    return result
