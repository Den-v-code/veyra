"""Bounded first-offset inverse parser for private non-executing KCA1."""

from __future__ import annotations

import logging
from typing import NamedTuple, Protocol, cast
import unicodedata

from . import omegaa_kca1_types as _syntax_module
from .omegaa_kca1_common import (
    DEFAULT_KCA1_LIMITS_V1,
    KCA1_PREFIX,
    MAX_DEPTH,
    MAX_INPUT,
    MAX_NAT,
    MAX_NODES,
    MAX_OUTPUT,
    KCA1DecodeCodeV1,
    KCA1LimitsV1,
    _decode_error,
    _resource,
    _snapshot_limits,
    decode_code_ordinal_v1,
    decode_code_from_ordinal_v1,
)
from .omegaa_kca1_types import (
    KCA1_ARITIES as _ARITIES,
    KCA1_FIELD_KINDS as _FIELD_KINDS,
    KernelCheckerASTV1,
    KernelCheckerTagV1,
    kca1_mode_type_v1,
    kca1_tag_from_ordinal_v1,
    validate_kca1_enum_integrity_v1,
)

logger = logging.getLogger(__name__)
_AST_CLASS = KernelCheckerASTV1
_AST_INIT = vars(_AST_CLASS)["__init__"]
_AST_POST_INIT = vars(_AST_CLASS)["__post_init__"]
_AST_TAG_SLOT = vars(_AST_CLASS)["tag"]
_AST_FIELDS_SLOT = vars(_AST_CLASS)["fields"]


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def _validate_ast_constructor_integrity() -> None:
    logger.debug("_validate_ast_constructor_integrity entry")
    namespace = vars(_AST_CLASS)
    if (
        KernelCheckerASTV1 is not _AST_CLASS
        or _syntax_module.KernelCheckerASTV1 is not _AST_CLASS
        or namespace.get("__init__") is not _AST_INIT
        or namespace.get("__post_init__") is not _AST_POST_INIT
        or namespace.get("tag") is not _AST_TAG_SLOT
        or namespace.get("fields") is not _AST_FIELDS_SLOT
    ):
        logger.error("_validate_ast_constructor_integrity error drift")
        raise ValueError("ast-constructor-integrity")
    logger.debug("_validate_ast_constructor_integrity exit")


def _construct_ast(
    tag: KernelCheckerTagV1, fields: tuple[object, ...],
) -> KernelCheckerASTV1:
    logger.debug("_construct_ast entry tag=%s", tag.name)
    _validate_ast_constructor_integrity()
    result = object.__new__(_AST_CLASS)
    cast(_SlotSetter, _AST_TAG_SLOT).__set__(result, tag)
    cast(_SlotSetter, _AST_FIELDS_SLOT).__set__(result, fields)
    logger.debug("_construct_ast exit tag=%s", tag.name)
    return result


class _AstTask(NamedTuple):
    start: int
    end: int
    depth: int


class _FieldsTask(NamedTuple):
    tag: KernelCheckerTagV1
    position: int
    offset: int
    end: int
    depth: int


class _ScalarTask(NamedTuple):
    kind: str
    start: int
    end: int


_WireTask = _AstTask | _FieldsTask | _ScalarTask


def _u64_at(data: bytes, offset: int, end: int) -> int:
    logger.debug("_u64_at entry offset=%d end=%d", offset, end)
    if offset + 8 > end:
        _decode_error(KCA1DecodeCodeV1.BAD_LENGTH, offset)
    result = int.from_bytes(data[offset : offset + 8], "big")
    logger.debug("_u64_at exit value=%d", result)
    return result


def _take_frame(data: bytes, offset: int, end: int) -> tuple[int, int, int]:
    logger.debug("_take_frame entry offset=%d end=%d", offset, end)
    length = _u64_at(data, offset, end)
    start = offset + 8
    stop = start + length
    if stop > end:
        _decode_error(KCA1DecodeCodeV1.BAD_LENGTH, offset)
    logger.debug("_take_frame exit start=%d stop=%d", start, stop)
    return start, stop, stop


def _check_prefix(data: bytes, start: int, end: int) -> None:
    logger.debug("_check_prefix entry start=%d end=%d", start, end)
    available = min(4, end - start)
    for index in range(available):
        if data[start + index] != KCA1_PREFIX[index]:
            _decode_error(KCA1DecodeCodeV1.BAD_VERSION, start + index)
    if available < 4:
        _decode_error(KCA1DecodeCodeV1.BAD_LENGTH, start + available)
    logger.debug("_check_prefix exit")


def _validate_literal(data: bytes, start: int, end: int) -> None:
    logger.debug("_validate_literal entry start=%d end=%d", start, end)
    try:
        text = data[start:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        _decode_error(KCA1DecodeCodeV1.BAD_ORDER, start + exc.start)
    if unicodedata.normalize("NFC", text) != text:
        _decode_error(KCA1DecodeCodeV1.BAD_ORDER, start)
    logger.debug("_validate_literal exit")


def _validate_scalar(
    data: bytes, kind: str, start: int, end: int, limits: tuple[int, ...],
) -> None:
    logger.debug("_validate_scalar entry kind=%s", kind)
    if kind == "literal":
        _validate_literal(data, start, end)
    elif kind == "bytes":
        pass
    elif kind == "nat":
        mag_start, mag_end, next_offset = _take_frame(data, start, end)
        if mag_end - mag_start > limits[MAX_NAT]:
            _resource("max_nat_bytes", mag_start)
        findings: list[tuple[KCA1DecodeCodeV1, int]] = []
        if next_offset != end:
            findings.append((KCA1DecodeCodeV1.TRAILING, next_offset))
        if mag_start < mag_end and data[mag_start] == 0:
            findings.append((KCA1DecodeCodeV1.NONCANONICAL_NAT, mag_start))
        if findings:
            code, offset = min(
                findings, key=lambda item: (item[1], decode_code_ordinal_v1(item[0])),
            )
            _decode_error(code, offset)
    elif kind == "u8":
        if end - start != 1:
            _decode_error(KCA1DecodeCodeV1.BAD_LENGTH, start)
    elif kind == "decode_code":
        if end - start != 1:
            _decode_error(KCA1DecodeCodeV1.BAD_LENGTH, start)
        if data[start] >= 11:
            _decode_error(KCA1DecodeCodeV1.BAD_TAG, start)
        decode_code_from_ordinal_v1(data[start])
    else:
        if end - start != 1:
            _decode_error(KCA1DecodeCodeV1.BAD_LENGTH, start)
        if data[start] != 0:
            _decode_error(KCA1DecodeCodeV1.BAD_ORDER, start)
        kca1_mode_type_v1(kind)
    logger.debug("_validate_scalar exit")


def _wire_preflight(data: bytes, limits: tuple[int, ...]) -> None:
    logger.debug("_wire_preflight entry bytes=%d", len(data))
    validate_kca1_enum_integrity_v1()
    nodes = 0
    stack: list[_WireTask] = [_AstTask(0, len(data), 0)]
    while stack:
        task = stack.pop()
        if isinstance(task, _AstTask):
            start, end, depth = task
            nodes += 1
            if nodes > limits[MAX_NODES]:
                _resource("max_nodes", start)
            if depth > limits[MAX_DEPTH]:
                _resource("max_depth", start)
            _check_prefix(data, start, end)
            if start + 5 > end:
                _decode_error(KCA1DecodeCodeV1.BAD_LENGTH, start + 4)
            raw_tag = data[start + 4]
            if raw_tag >= len(_ARITIES):
                _decode_error(KCA1DecodeCodeV1.BAD_TAG, start + 4)
            tag = kca1_tag_from_ordinal_v1(raw_tag)
            if start + 6 > end:
                _decode_error(KCA1DecodeCodeV1.BAD_LENGTH, start + 5)
            if data[start + 5] != _ARITIES[tag]:
                _decode_error(KCA1DecodeCodeV1.BAD_ARITY, start + 5)
            stack.append(_FieldsTask(tag, 0, start + 6, end, depth))
        elif isinstance(task, _FieldsTask):
            tag, position, offset, end, depth = task
            kinds = _FIELD_KINDS[tag]
            if position == len(kinds):
                if offset != end:
                    _decode_error(KCA1DecodeCodeV1.TRAILING, offset)
                continue
            field_start, field_end, next_offset = _take_frame(data, offset, end)
            stack.append(_FieldsTask(tag, position + 1, next_offset, end, depth))
            kind = kinds[position]
            if kind == "ast":
                stack.append(_AstTask(field_start, field_end, depth + 1))
            else:
                stack.append(_ScalarTask(kind, field_start, field_end))
        else:
            _validate_scalar(data, task.kind, task.start, task.end, limits)
    logger.debug("_wire_preflight exit nodes=%d", nodes)


def _parse_nat(data: bytes, start: int, end: int) -> int:
    logger.debug("_parse_nat entry start=%d", start)
    mag_start, mag_end, _ = _take_frame(data, start, end)
    result = int.from_bytes(data[mag_start:mag_end], "big")
    logger.debug("_parse_nat exit")
    return result


def _parse_ast(data: bytes, start: int, end: int) -> KernelCheckerASTV1:
    logger.debug("_parse_ast entry start=%d", start)
    tag = kca1_tag_from_ordinal_v1(data[start + 4])
    offset = start + 6
    fields: list[object] = []
    for kind in _FIELD_KINDS[tag]:
        field_start, field_end, offset = _take_frame(data, offset, end)
        if kind == "ast":
            value: object = _parse_ast(data, field_start, field_end)
        elif kind in {"literal", "bytes"}:
            value = data[field_start:field_end]
        elif kind == "nat":
            value = _parse_nat(data, field_start, field_end)
        elif kind == "u8":
            value = data[field_start]
        elif kind == "decode_code":
            value = decode_code_from_ordinal_v1(data[field_start])
        else:
            mode_type = kca1_mode_type_v1(kind)
            value = tuple(mode_type)[0]
        fields.append(value)
    result = _construct_ast(tag, tuple(fields))
    logger.debug("_parse_ast exit tag=%s", tag.name)
    return result


def parse_kernel_checker_ast_v1(
    raw: bytes, limits: KCA1LimitsV1 = DEFAULT_KCA1_LIMITS_V1,
) -> KernelCheckerASTV1:
    """Parse canonical KCA1 bytes after iterative bounded preflight."""
    logger.debug("parse_kernel_checker_ast_v1 entry")
    _validate_ast_constructor_integrity()
    if type(raw) is not bytes:
        logger.error("parse_kernel_checker_ast_v1 error raw-type")
        raise TypeError("raw must be exact bytes")
    limit_values = _snapshot_limits(limits)
    if len(raw) > limit_values[MAX_INPUT]:
        _resource("max_input_bytes", limit_values[MAX_INPUT])
    if len(raw) > limit_values[MAX_OUTPUT]:
        _resource("max_output_bytes", limit_values[MAX_OUTPUT])
    _wire_preflight(raw, limit_values)
    result = _parse_ast(raw, 0, len(raw))
    logger.debug("parse_kernel_checker_ast_v1 exit")
    return result
