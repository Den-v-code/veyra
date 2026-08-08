"""KEB-owned iterative, nonbuilding structural preflight for nested KPT1."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import NamedTuple

from . import omegaa_kpt1_types as _kpt_types
from .omegaa_keb1_common import KEB1DecodeCodeV1, _integrity_error
from .omegaa_kpt1_common import KPT1_PREFIX

logger = logging.getLogger(__name__)
_LOGGER = logger
_PREFIX = KPT1_PREFIX
_TERM_ENUM = _kpt_types.KernelTermTagV1
_LEVEL_ENUM = _kpt_types.KernelLevelTagV1
_TERM_TAGS = tuple(_TERM_ENUM(index) for index in range(16))
_LEVEL_TAGS = tuple(_LEVEL_ENUM(index) for index in range(3))
_FIELD_KINDS = tuple(tuple(_kpt_types.KPT1_FIELD_KINDS[tag]) for tag in _TERM_TAGS)
_ARITIES = tuple(len(kinds) for kinds in _FIELD_KINDS)
_LEVEL_ARITIES = (0, 1, 2)
_KPT_MODULE = _kpt_types
_INTEGRITY_FROZEN = _integrity_error
_INTEGRITY_CODE = _INTEGRITY_FROZEN.__code__


@dataclass(frozen=True, slots=True)
class KEB1NodeMetricV1:
    running_node_count: int
    depth: int
    node_start: int


@dataclass(frozen=True, slots=True)
class KEB1CountMetricV1:
    count: int
    count_start: int


@dataclass(frozen=True, slots=True)
class KEBKPTStructuralPreflightV1:
    decode_candidates: tuple[tuple[KEB1DecodeCodeV1, int], ...]
    nodes: tuple[KEB1NodeMetricV1, ...]
    lists: tuple[KEB1CountMetricV1, ...]
    nats: tuple[KEB1CountMetricV1, ...]
    root_consumed: bool


class _Term(NamedTuple):
    start: int
    end: int
    depth: int


class _Fields(NamedTuple):
    ordinal: int
    position: int
    offset: int
    end: int
    depth: int


class _Level(NamedTuple):
    start: int
    end: int
    depth: int


class _LevelFields(NamedTuple):
    item_count: int
    position: int
    offset: int
    end: int
    depth: int


class _List(NamedTuple):
    start: int
    end: int
    depth: int


class _ListItems(NamedTuple):
    item_count: int
    position: int
    offset: int
    end: int
    depth: int


class _Nat(NamedTuple):
    start: int
    end: int


class _Digest(NamedTuple):
    start: int
    end: int


_Task = _Term | _Fields | _Level | _LevelFields | _List | _ListItems | _Nat | _Digest


def validate_keb1_preflight_integrity_v1() -> None:
    """Reject drift from the accepted KPT1 wire language tables."""
    _LOGGER.debug("validate_keb1_preflight_integrity_v1 entry")
    module = vars(_KPT_MODULE)
    drift = (
        globals().get("logger") is not _LOGGER
        or module.get("KernelTermTagV1") is not _TERM_ENUM
        or module.get("KernelLevelTagV1") is not _LEVEL_ENUM
        or globals().get("KPT1_PREFIX") is not _PREFIX
        or _PREFIX != b"KPT1"
        or tuple(module.get("KernelTermTagV1", ())) != _TERM_TAGS
        or tuple(module.get("KernelLevelTagV1", ())) != _LEVEL_TAGS
        or any(object.__getattribute__(tag, "_value_") != index for index, tag in enumerate(_TERM_TAGS))
        or any(object.__getattribute__(tag, "_value_") != index for index, tag in enumerate(_LEVEL_TAGS))
        or tuple(tuple(module["KPT1_FIELD_KINDS"][tag]) for tag in _TERM_TAGS) != _FIELD_KINDS
        or tuple(module["KPT1_ARITIES"][tag] for tag in _TERM_TAGS) != _ARITIES
    )
    if drift:
        _INTEGRITY_FROZEN("keb1-kpt-table-integrity")
    _LOGGER.debug("validate_keb1_preflight_integrity_v1 exit")


_VALIDATE_PREFLIGHT_FROZEN = validate_keb1_preflight_integrity_v1
_VALIDATE_PREFLIGHT_CODE = _VALIDATE_PREFLIGHT_FROZEN.__code__


def _u64_at(data: bytes, offset: int, end: int) -> int | None:
    _LOGGER.debug("_u64_at entry offset=%d end=%d", offset, end)
    if offset < 0 or end < offset or end > len(data):
        _INTEGRITY_FROZEN("keb1-preflight-bounds-integrity")
    if offset > end - 8:
        _LOGGER.debug("_u64_at exit missing")
        return None
    result = int.from_bytes(data[offset : offset + 8], "big")
    _LOGGER.debug("_u64_at exit value=%d", result)
    return result


_U64_AT_FROZEN = _u64_at
_U64_AT_CODE = _U64_AT_FROZEN.__code__


def _take_frame(data: bytes, offset: int, end: int) -> tuple[int, int, int] | None:
    _LOGGER.debug("_take_frame entry offset=%d end=%d", offset, end)
    length = _U64_AT_FROZEN(data, offset, end)
    if length is None:
        _LOGGER.debug("_take_frame exit missing-prefix")
        return None
    start = offset + 8
    if length > end - start:
        _LOGGER.debug("_take_frame exit truncated")
        return None
    stop = start + length
    _LOGGER.debug("_take_frame exit start=%d stop=%d", start, stop)
    return start, stop, stop


_TAKE_FRAME_FROZEN = _take_frame
_TAKE_FRAME_CODE = _TAKE_FRAME_FROZEN.__code__


def preflight_kpt_wire_v1(data: bytes) -> KEBKPTStructuralPreflightV1:
    """Walk safe KPT frames, recording decode candidates and exact metrics."""
    _LOGGER.debug("preflight_kpt_wire_v1 entry bytes=%d", len(data) if type(data) is bytes else -1)
    if (
        globals().get("validate_keb1_preflight_integrity_v1") is not _VALIDATE_PREFLIGHT_FROZEN
        or _VALIDATE_PREFLIGHT_FROZEN.__code__ is not _VALIDATE_PREFLIGHT_CODE
        or globals().get("_u64_at") is not _U64_AT_FROZEN
        or _U64_AT_FROZEN.__code__ is not _U64_AT_CODE
        or globals().get("_take_frame") is not _TAKE_FRAME_FROZEN
        or _TAKE_FRAME_FROZEN.__code__ is not _TAKE_FRAME_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_FROZEN
        or _INTEGRITY_FROZEN.__code__ is not _INTEGRITY_CODE
    ):
        _INTEGRITY_FROZEN("keb1-preflight-helper-integrity")
    _VALIDATE_PREFLIGHT_FROZEN()
    if type(data) is not bytes:
        _INTEGRITY_FROZEN("keb1-preflight-host-shape")
    candidates: list[tuple[KEB1DecodeCodeV1, int]] = []
    nodes: list[KEB1NodeMetricV1] = []
    lists: list[KEB1CountMetricV1] = []
    nats: list[KEB1CountMetricV1] = []
    stack: list[_Task] = [_Term(0, len(data), 0)]
    root_consumed = False

    def fault(code: KEB1DecodeCodeV1, offset: int) -> None:
        _LOGGER.debug("preflight fault entry code=%s offset=%d", code.name, offset)
        candidates.append((code, offset))
        _LOGGER.debug("preflight fault exit")

    while stack:
        task = stack.pop()
        if isinstance(task, _Term):
            start, end, depth = task
            nodes.append(KEB1NodeMetricV1(len(nodes) + 1, depth, start))
            available = min(4, end - start)
            mismatch = next((i for i in range(available) if data[start + i] != _PREFIX[i]), None)
            if mismatch is not None:
                fault(KEB1DecodeCodeV1.BAD_VERSION, start + mismatch)
                continue
            if available < 4:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, start + available)
                continue
            if start + 5 > end:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, start + 4)
                continue
            ordinal = data[start + 4]
            if ordinal >= len(_ARITIES):
                fault(KEB1DecodeCodeV1.BAD_TAG, start + 4)
                continue
            if start + 6 > end:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, start + 5)
                continue
            if data[start + 5] != _ARITIES[ordinal]:
                fault(KEB1DecodeCodeV1.BAD_ARITY, start + 5)
                continue
            stack.append(_Fields(ordinal, 0, start + 6, end, depth))
        elif isinstance(task, _Fields):
            ordinal, position, offset, end, depth = task
            kinds = _FIELD_KINDS[ordinal]
            if position == len(kinds):
                if offset != end:
                    fault(KEB1DecodeCodeV1.TRAILING, offset)
                elif end == len(data) and depth == 0:
                    root_consumed = True
                continue
            frame = _TAKE_FRAME_FROZEN(data, offset, end)
            if frame is None:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, offset)
                continue
            field_start, field_end, next_offset = frame
            stack.append(_Fields(ordinal, position + 1, next_offset, end, depth))
            kind = kinds[position]
            if kind == "term":
                stack.append(_Term(field_start, field_end, depth + 1))
            elif kind == "level":
                stack.append(_Level(field_start, field_end, depth + 1))
            elif kind == "terms":
                stack.append(_List(field_start, field_end, depth + 1))
            elif kind == "nat":
                stack.append(_Nat(field_start, field_end))
            else:
                stack.append(_Digest(field_start, field_end))
        elif isinstance(task, _Level):
            start, end, depth = task
            nodes.append(KEB1NodeMetricV1(len(nodes) + 1, depth, start))
            if start >= end:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, start)
                continue
            ordinal = data[start]
            if ordinal >= 3:
                fault(KEB1DecodeCodeV1.BAD_TAG, start)
                continue
            stack.append(_LevelFields(_LEVEL_ARITIES[ordinal], 0, start + 1, end, depth))
        elif isinstance(task, _LevelFields):
            count, position, offset, end, depth = task
            if position == count:
                if offset != end:
                    fault(KEB1DecodeCodeV1.TRAILING, offset)
                continue
            frame = _TAKE_FRAME_FROZEN(data, offset, end)
            if frame is None:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, offset)
                continue
            child_start, child_end, next_offset = frame
            stack.append(_LevelFields(count, position + 1, next_offset, end, depth))
            stack.append(_Level(child_start, child_end, depth + 1))
        elif isinstance(task, _List):
            start, end, depth = task
            list_count = _U64_AT_FROZEN(data, start, end)
            if list_count is None:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, start)
                continue
            lists.append(KEB1CountMetricV1(list_count, start))
            stack.append(_ListItems(list_count, 0, start + 8, end, depth))
        elif isinstance(task, _ListItems):
            count, position, offset, end, depth = task
            if position == count:
                if offset != end:
                    fault(KEB1DecodeCodeV1.TRAILING, offset)
                continue
            frame = _TAKE_FRAME_FROZEN(data, offset, end)
            if frame is None:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, offset)
                continue
            child_start, child_end, next_offset = frame
            stack.append(_ListItems(count, position + 1, next_offset, end, depth))
            stack.append(_Term(child_start, child_end, depth + 1))
        elif isinstance(task, _Nat):
            start, end = task
            frame = _TAKE_FRAME_FROZEN(data, start, end)
            if frame is None:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, start)
                continue
            mag_start, mag_end, next_offset = frame
            nats.append(KEB1CountMetricV1(mag_end - mag_start, mag_start))
            if next_offset != end:
                fault(KEB1DecodeCodeV1.TRAILING, next_offset)
            elif mag_start < mag_end and data[mag_start] == 0:
                fault(KEB1DecodeCodeV1.NONCANONICAL_NAT, mag_start)
        else:
            start, end = task
            if end - start != 32:
                fault(KEB1DecodeCodeV1.BAD_LENGTH, start)

    result = KEBKPTStructuralPreflightV1(tuple(candidates), tuple(nodes), tuple(lists), tuple(nats), root_consumed)
    _LOGGER.debug("preflight_kpt_wire_v1 exit candidates=%d nodes=%d", len(candidates), len(nodes))
    return result
