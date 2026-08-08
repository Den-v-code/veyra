"""First-offset, bounded inverse parser for canonical private KPT1 bytes."""

from __future__ import annotations

import logging

from .omegaa_kpt1_builder import build_level_v1, build_term_v1
from .omegaa_kpt1_common import (
    DEFAULT_KPT1_LIMITS_V1,
    KPT1_PREFIX,
    MAX_DEPTH,
    MAX_INPUT,
    MAX_LIST,
    MAX_NAT,
    MAX_NODES,
    MAX_OUTPUT,
    KPT1DecodeCodeV1,
    KPT1LimitsV1,
    _decode_error,
    _resource,
    _snapshot_limits,
)
from .omegaa_kpt1_parser_tasks import (
    DigestTask as _DigestTask,
    FieldsTask as _FieldsTask,
    LevelFieldsTask as _LevelFieldsTask,
    LevelTask as _LevelTask,
    ListItemsTask as _ListItemsTask,
    ListTask as _ListTask,
    NatTask as _NatTask,
    TermTask as _TermTask,
    WireTask as _WireTask,
)
from .omegaa_kpt1_types import (
    KPT1_ARITIES as _ARITIES,
    KPT1_FIELD_KINDS as _FIELD_KINDS,
    KPT1ValidationError,
    KernelLevelTagV1,
    KernelProofTermV1,
    KernelTermTagV1,
    KernelUniverseLevelV1,
)

logger = logging.getLogger(__name__)
_TERM_TAGS = tuple(KernelTermTagV1)
_LEVEL_TAGS = tuple(KernelLevelTagV1)
_LEVEL_ARITIES = (0, 1, 2)
_OBJECT_GETATTRIBUTE = object.__getattribute__


def _validate_parser_tables() -> None:
    logger.debug("_validate_parser_tables entry")
    for ordinal, term_tag in enumerate(_TERM_TAGS):
        if _OBJECT_GETATTRIBUTE(term_tag, "_value_") != ordinal:
            logger.error("_validate_parser_tables error term ordinal=%d", ordinal)
            raise KPT1ValidationError("enum-ordinal-integrity")
    for ordinal, level_tag in enumerate(_LEVEL_TAGS):
        if _OBJECT_GETATTRIBUTE(level_tag, "_value_") != ordinal:
            logger.error("_validate_parser_tables error level ordinal=%d", ordinal)
            raise KPT1ValidationError("enum-ordinal-integrity")
    logger.debug("_validate_parser_tables exit")


def _u64_at(data: bytes, offset: int, end: int) -> int:
    logger.debug("_u64_at entry offset=%d end=%d", offset, end)
    if offset + 8 > end:
        _decode_error(KPT1DecodeCodeV1.BAD_LENGTH, offset)
    result = int.from_bytes(data[offset : offset + 8], "big")
    logger.debug("_u64_at exit value=%d", result)
    return result


def _take_frame(data: bytes, offset: int, end: int) -> tuple[int, int, int]:
    logger.debug("_take_frame entry offset=%d end=%d", offset, end)
    length = _u64_at(data, offset, end)
    start = offset + 8
    stop = start + length
    if stop > end:
        _decode_error(KPT1DecodeCodeV1.BAD_LENGTH, offset)
    logger.debug("_take_frame exit start=%d stop=%d", start, stop)
    return start, stop, stop


def _check_prefix(data: bytes, start: int, end: int) -> None:
    logger.debug("_check_prefix entry start=%d end=%d", start, end)
    available = min(4, end - start)
    for index in range(available):
        if data[start + index] != KPT1_PREFIX[index]:
            _decode_error(KPT1DecodeCodeV1.BAD_VERSION, start + index)
    if available < 4:
        _decode_error(KPT1DecodeCodeV1.BAD_LENGTH, start + available)
    logger.debug("_check_prefix exit")


def _wire_preflight(data: bytes, limits: tuple[int, ...]) -> None:
    logger.debug("_wire_preflight entry bytes=%d", len(data))
    _validate_parser_tables()
    nodes = 0
    stack: list[_WireTask] = [_TermTask(0, len(data), 0)]
    while stack:
        task = stack.pop()
        if isinstance(task, _TermTask):
            start, end, depth = task
            nodes += 1
            if nodes > limits[MAX_NODES]:
                _resource("max_nodes", start)
            if depth > limits[MAX_DEPTH]:
                _resource("max_depth", start)
            _check_prefix(data, start, end)
            if start + 5 > end:
                _decode_error(KPT1DecodeCodeV1.BAD_LENGTH, start + 4)
            raw_tag = data[start + 4]
            if raw_tag >= len(_ARITIES):
                _decode_error(KPT1DecodeCodeV1.BAD_TAG, start + 4)
            tag = _TERM_TAGS[raw_tag]
            if start + 6 > end:
                _decode_error(KPT1DecodeCodeV1.BAD_LENGTH, start + 5)
            if data[start + 5] != _ARITIES[tag]:
                _decode_error(KPT1DecodeCodeV1.BAD_ARITY, start + 5)
            stack.append(_FieldsTask(tag, 0, start + 6, end, depth))
        elif isinstance(task, _FieldsTask):
            tag, position, offset, end, depth = task
            kinds = _FIELD_KINDS[tag]
            if position == len(kinds):
                if offset != end:
                    _decode_error(KPT1DecodeCodeV1.TRAILING, offset)
                continue
            field_start, field_end, next_offset = _take_frame(data, offset, end)
            stack.append(_FieldsTask(tag, position + 1, next_offset, end, depth))
            field_kind = kinds[position]
            if field_kind == "term":
                stack.append(_TermTask(field_start, field_end, depth + 1))
            elif field_kind == "level":
                stack.append(_LevelTask(field_start, field_end, depth + 1))
            elif field_kind == "terms":
                stack.append(_ListTask(field_start, field_end, depth + 1))
            elif field_kind == "nat":
                stack.append(_NatTask(field_start, field_end))
            else:
                stack.append(_DigestTask(field_start, field_end))
        elif isinstance(task, _LevelTask):
            start, end, depth = task
            nodes += 1
            if nodes > limits[MAX_NODES]:
                _resource("max_nodes", start)
            if depth > limits[MAX_DEPTH]:
                _resource("max_depth", start)
            if start >= end:
                _decode_error(KPT1DecodeCodeV1.BAD_LENGTH, start)
            if data[start] >= 3:
                _decode_error(KPT1DecodeCodeV1.BAD_TAG, start)
            stack.append(_LevelFieldsTask(_LEVEL_ARITIES[data[start]], 0, start + 1, end, depth))
        elif isinstance(task, _LevelFieldsTask):
            item_count, position, offset, end, depth = task
            if position == item_count:
                if offset != end:
                    _decode_error(KPT1DecodeCodeV1.TRAILING, offset)
                continue
            child_start, child_end, next_offset = _take_frame(data, offset, end)
            stack.append(_LevelFieldsTask(item_count, position + 1, next_offset, end, depth))
            stack.append(_LevelTask(child_start, child_end, depth + 1))
        elif isinstance(task, _ListTask):
            start, end, depth = task
            count = _u64_at(data, start, end)
            if count > limits[MAX_LIST]:
                _resource("max_list_items", start)
            stack.append(_ListItemsTask(count, 0, start + 8, end, depth))
        elif isinstance(task, _ListItemsTask):
            item_count, position, offset, end, depth = task
            if position == item_count:
                if offset != end:
                    _decode_error(KPT1DecodeCodeV1.TRAILING, offset)
                continue
            child_start, child_end, next_offset = _take_frame(data, offset, end)
            stack.append(_ListItemsTask(item_count, position + 1, next_offset, end, depth))
            stack.append(_TermTask(child_start, child_end, depth + 1))
        elif isinstance(task, _NatTask):
            start, end = task
            mag_start, mag_end, next_offset = _take_frame(data, start, end)
            if next_offset != end:
                _decode_error(KPT1DecodeCodeV1.TRAILING, next_offset)
            if mag_end - mag_start > limits[MAX_NAT]:
                _resource("max_nat_bytes", mag_start)
            if mag_start < mag_end and data[mag_start] == 0:
                _decode_error(KPT1DecodeCodeV1.NONCANONICAL_NAT, mag_start)
        else:
            start, end = task
            if end - start != 32:
                _decode_error(KPT1DecodeCodeV1.BAD_LENGTH, start)
    logger.debug("_wire_preflight exit nodes=%d", nodes)


def _parse_nat(data: bytes, start: int, end: int) -> int:
    logger.debug("_parse_nat entry start=%d", start)
    mag_start, mag_end, _ = _take_frame(data, start, end)
    result = int.from_bytes(data[mag_start:mag_end], "big")
    logger.debug("_parse_nat exit")
    return result


def _parse_level(data: bytes, start: int, end: int) -> KernelUniverseLevelV1:
    logger.debug("_parse_level entry start=%d", start)
    raw_tag = data[start]
    tag = _LEVEL_TAGS[raw_tag]
    offset = start + 1
    fields: list[KernelUniverseLevelV1] = []
    for _ in range(_LEVEL_ARITIES[raw_tag]):
        child_start, child_end, offset = _take_frame(data, offset, end)
        fields.append(_parse_level(data, child_start, child_end))
    result = build_level_v1(tag, tuple(fields), KernelProofTermV1, KernelUniverseLevelV1)
    logger.debug("_parse_level exit tag=%d", raw_tag)
    return result


def _parse_term_list(data: bytes, start: int, end: int) -> tuple[KernelProofTermV1, ...]:
    logger.debug("_parse_term_list entry start=%d", start)
    count = _u64_at(data, start, end)
    offset = start + 8
    result: list[KernelProofTermV1] = []
    for _ in range(count):
        child_start, child_end, offset = _take_frame(data, offset, end)
        result.append(_parse_term(data, child_start, child_end))
    logger.debug("_parse_term_list exit count=%d", count)
    return tuple(result)


def _parse_term(data: bytes, start: int, end: int) -> KernelProofTermV1:
    logger.debug("_parse_term entry start=%d", start)
    raw_tag = data[start + 4]
    tag = _TERM_TAGS[raw_tag]
    offset = start + 6
    fields: list[object] = []
    for field_kind in _FIELD_KINDS[tag]:
        field_start, field_end, offset = _take_frame(data, offset, end)
        field: object
        if field_kind == "nat":
            field = _parse_nat(data, field_start, field_end)
        elif field_kind == "digest":
            field = data[field_start:field_end]
        elif field_kind == "level":
            field = _parse_level(data, field_start, field_end)
        elif field_kind == "term":
            field = _parse_term(data, field_start, field_end)
        else:
            field = _parse_term_list(data, field_start, field_end)
        fields.append(field)
    result = build_term_v1(tag, tuple(fields), KernelProofTermV1, KernelUniverseLevelV1)
    logger.debug("_parse_term exit tag=%d", raw_tag)
    return result


def parse_kernel_proof_term_v1(
    raw: bytes, limits: KPT1LimitsV1 = DEFAULT_KPT1_LIMITS_V1,
) -> KernelProofTermV1:
    """Parse exact canonical KPT1 bytes after iterative bounded preflight."""
    logger.debug("parse_kernel_proof_term_v1 entry")
    if type(raw) is not bytes:
        logger.error("parse_kernel_proof_term_v1 error raw-type")
        raise TypeError("raw must be exact bytes")
    limit_values = _snapshot_limits(limits)
    if len(raw) > limit_values[MAX_INPUT]:
        _resource("max_input_bytes", limit_values[MAX_INPUT])
    if len(raw) > limit_values[MAX_OUTPUT]:
        _resource("max_output_bytes", limit_values[MAX_OUTPUT])
    _wire_preflight(raw, limit_values)
    result = _parse_term(raw, 0, len(raw))
    logger.debug("parse_kernel_proof_term_v1 exit")
    return result
