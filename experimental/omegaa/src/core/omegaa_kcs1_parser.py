"""Decode-first, plan-before-commit inverse parsers for the six KCS1 wires."""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import logging
from typing import NoReturn, cast

from . import omegaa_kcs1_types as t
from .omegaa_kcs1_builder import (
    build_kcs1_accept_state_v1,
    build_kcs1_attempt_resource_v1,
    build_kcs1_compare_types_node_v1,
    build_kcs1_entry_node_v1,
    build_kcs1_infer_node_v1,
    build_kcs1_input_offset_locus_v1,
    build_kcs1_internal_attempt_v1,
    build_kcs1_nf_result_v1,
    build_kcs1_no_locus_v1,
    build_kcs1_parse_node_v1,
    build_kcs1_reduce_node_v1,
    build_kcs1_reject_state_v1,
    build_kcs1_resource_attempt_v1,
    build_kcs1_return_typed_node_v1,
    build_kcs1_run_state_v1,
    build_kcs1_state_step_locus_v1,
    build_kcs1_step_result_v1,
    build_kcs1_structural_count_locus_v1,
    build_kcs1_terminal_attempt_v1,
)
from .omegaa_kcs1_codec import _Preflight
from .omegaa_kcs1_common import (
    _ARITIES,
    _DOMAIN_NAMES,
    _PREFIXES,
    _decode_arm,
    _decoded_arm,
    _integrity_arm,
    _resource_arm,
    _snapshot_limits,
)
from .omegaa_kcc1_common import KCC1DecodeError, KCC1LimitsV1, KCC1ResourceLimit
from .omegaa_kcc1_parser import parse_empty_checker_config_v1
from .omegaa_kcc1_types import EmptyCheckerConfigV1
from .omegaa_kcf1_common import KCF1DecodeError, KCF1LimitsV1, KCF1ResourceLimit
from .omegaa_kcf1_parser import parse_kernel_continuation_frame_v1
from .omegaa_kcf1_types import KCF1_FIELD_KINDS, KernelContinuationFrameV1, KernelContinuationTagV1
from .omegaa_kci1_common import KCI1LimitsV1
from .omegaa_kci1_parser import parse_checker_input_syntax_v1
from .omegaa_kci1_types import (
    CheckerInputSyntaxV1,
    KCI1DecodeErrorResultV1,
    KCI1DecodedResultV1,
    KCI1ResourceParseResultV1,
)
from .omegaa_keb1_common import KEB1LimitsV1
from .omegaa_keb1_parser import parse_expected_binding_v1
from .omegaa_keb1_types import (
    ExpectedBindingSyntaxV1,
    KEB1DecodeErrorResultV1,
    KEB1DecodedResultV1,
    KEB1ResourceParseResultV1,
)
from .omegaa_kpt1_common import KPT1DecodeError, KPT1LimitsV1, KPT1ResourceLimit
from .omegaa_kpt1_parser import parse_kernel_proof_term_v1
from .omegaa_kpt1_types import (
    KPT1_FIELD_KINDS,
    KernelProofTermV1,
    KernelTermTagV1,
)

logger = logging.getLogger(__name__)
_U64_LIMIT = 1 << 64
_OWNED_KINDS = (
    (("keb",), ("bytes",), ("kpt",), ("kpt",), ("kpt", "kpt", "kpt"), ("bytes32",)),
    (
        ("kcn", "kcc", "kci", "vec-kpt", "vec-kpt", "vec-kcf", "u64"),
        ("kpt", "bytes32"),
        ("reject", "u64"),
    ),
    (("kpt",), ("kpt",)),
    (("u64",), ("nat",), ("nat",), ()),
    (("attempt-kind", "nat", "nat", "krl"),),
    (("terminal",), ("krf",), ("internal", "krl")),
)
_LEGAL_LOCUS = (0, 3, 2, 2, 2, 2, 2, 2, 1, 1, 2)


@dataclass(slots=True)
class _Dependency:
    kind: str
    start: int
    end: int
    depth: int
    tag: int
    frames: tuple[tuple[int, int, int], ...]


@dataclass(slots=True)
class _Profile:
    size: int
    depth: int
    nodes: int
    max_list: int
    max_nat: int
    nested_kpt: int = 0
    expected: int = 0
    term: int = 0
    expected_wire: int = 0


@dataclass(slots=True)
class _Capture:
    decode: list[tuple[int, int]] = field(default_factory=list)
    events: list[tuple[int, int, int]] = field(default_factory=list)
    dependencies: list[_Dependency] = field(default_factory=list)
    relations: list[tuple[int, int, int]] = field(default_factory=list)


class _Decode(ValueError):
    def __init__(self, ordinal: int, offset: int) -> None:
        logger.debug("_Decode.__init__ entry ordinal=%d offset=%d", ordinal, offset)
        self.ordinal = ordinal
        self.offset = offset
        super().__init__(f"{ordinal}@{offset}")
        logger.error("KCS1 decode rejected ordinal=%d offset=%d", ordinal, offset)
        logger.debug("_Decode.__init__ exit")


def _bad(ordinal: int, offset: int) -> NoReturn:
    logger.debug("_bad entry ordinal=%d offset=%d", ordinal, offset)
    raise _Decode(ordinal, offset)


def _candidate(capture: _Capture, ordinal: int, offset: int) -> None:
    logger.debug("_candidate entry ordinal=%d offset=%d", ordinal, offset)
    capture.decode.append((offset, ordinal))
    logger.debug("_candidate exit")


def _read_u64(raw: bytes, offset: int) -> int:
    logger.debug("_read_u64 entry offset=%d", offset)
    value = 0
    for index in range(offset, offset + 8):
        value = (value << 8) | raw[index]
    logger.debug("_read_u64 exit value=%d", value)
    return value


def _frames(
    raw: bytes,
    start: int,
    end: int,
    prefix: bytes,
    arities: tuple[int, ...],
    split_prefix: bool,
    capture: _Capture,
) -> tuple[int, tuple[tuple[int, int, int], ...]] | None:
    """Capture every safely locatable frame and defer a trailing candidate."""
    logger.debug("_frames entry start=%d end=%d", start, end)
    available = min(4, end - start)
    mismatch = False
    for index in range(available):
        if raw[start + index] != prefix[index]:
            _candidate(capture, 1 if split_prefix and index < 3 else 0, start + index)
            mismatch = True
    if available < 4:
        _candidate(capture, 5, start + available)
        return None
    if mismatch:
        return None
    if start + 5 > end:
        _candidate(capture, 5, start + 4)
        return None
    tag = raw[start + 4]
    if tag >= len(arities):
        _candidate(capture, 2, start + 4)
        return None
    if start + 6 > end:
        _candidate(capture, 5, start + 5)
        return None
    if raw[start + 5] != arities[tag]:
        _candidate(capture, 3, start + 5)
        return None
    offset = start + 6
    result: list[tuple[int, int, int]] = []
    for _ in range(arities[tag]):
        lp = offset
        if offset + 8 > end:
            _candidate(capture, 5, lp)
            return None
        length = _read_u64(raw, offset)
        body = offset + 8
        stop = body + length
        if stop >= _U64_LIMIT or stop > end:
            _candidate(capture, 5, lp)
            return None
        result.append((lp, body, stop))
        offset = stop
    if offset < end:
        _candidate(capture, 10, offset)
    frames = tuple(result)
    logger.debug("_frames exit tag=%d fields=%d", tag, len(frames))
    return tag, frames


def _nat(raw: bytes, frame: tuple[int, int, int], capture: _Capture) -> int | None:
    logger.debug("_nat entry base=%d", frame[1])
    _, start, stop = frame
    size = stop - start
    if size < 8:
        _candidate(capture, 5, start + size)
        return None
    magnitude = _read_u64(raw, start)
    if magnitude > size - 8:
        _candidate(capture, 5, start)
        return None
    if magnitude < size - 8:
        _candidate(capture, 10, start + 8 + magnitude)
        return None
    if magnitude and raw[start + 8] == 0:
        _candidate(capture, 6, start + 8)
        return None
    capture.events.append((start + 8, int(t.KCS1CodecResourceKindV1.NESTED_NAT_BYTES), magnitude))
    logger.debug("_nat exit magnitude=%d", magnitude)
    return int.from_bytes(memoryview(raw)[start + 8 : stop], "big")


def _enum(raw: bytes, frame: tuple[int, int, int], count: int, capture: _Capture) -> int | None:
    logger.debug("_enum entry base=%d count=%d", frame[1], count)
    lp, start, stop = frame
    if stop - start != 1:
        _candidate(capture, 5, lp)
        return None
    if raw[start] >= count:
        _candidate(capture, 2, start)
        return None
    logger.debug("_enum exit value=%d", raw[start])
    return raw[start]


def _push(
    heap: list[tuple[int, int, str, int, int, int, int]],
    sequence: int,
    kind: str,
    start: int,
    end: int,
    depth: int,
    detail: int,
) -> int:
    logger.debug("_push entry kind=%s start=%d", kind, start)
    heapq.heappush(heap, (start, sequence, kind, end, depth, detail, 0))
    logger.debug("_push exit")
    return sequence + 1


def _capture_wire(raw: bytes, domain_index: int) -> _Capture:
    """Iteratively capture the complete wire; allocate no syntax DTO or output."""
    logger.debug("_capture_wire entry domain=%s", _DOMAIN_NAMES[domain_index])
    capture = _Capture()
    heap: list[tuple[int, int, str, int, int, int, int]] = []
    sequence = _push(heap, 0, "owned", 0, len(raw), 0, domain_index)
    while heap:
        start, _, task_kind, end, depth, detail, _ = heapq.heappop(heap)
        if task_kind in {"owned", "dep", "kpt", "level"}:
            capture.events.append((start, int(t.KCS1CodecResourceKindV1.COMPOSITE_DEPTH), depth))
            capture.events.append((start, int(t.KCS1CodecResourceKindV1.COMPOSITE_NODES), 1))
        if task_kind == "level":
            if start >= end:
                _candidate(capture, 5, start)
                continue
            tag = raw[start]
            if tag >= 3:
                _candidate(capture, 2, start)
                continue
            offset = start + 1
            children: list[tuple[int, int]] = []
            good = True
            for _ in range((0, 1, 2)[tag]):
                lp = offset
                if offset + 8 > end:
                    _candidate(capture, 5, lp)
                    good = False
                    break
                length = _read_u64(raw, offset)
                body, stop = offset + 8, offset + 8 + length
                if stop > end:
                    _candidate(capture, 5, lp)
                    good = False
                    break
                capture.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), length))
                children.append((body, stop))
                offset = stop
            if good and offset < end:
                _candidate(capture, 10, offset)
            for body, stop in children:
                sequence = _push(heap, sequence, "level", body, stop, depth + 1, 0)
            continue
        if task_kind == "owned":
            scanned = _frames(raw, start, end, _PREFIXES[detail], _ARITIES[detail], True, capture)
            if scanned is None:
                continue
            tag, frames = scanned
            kinds = _OWNED_KINDS[detail][tag]
            if detail == 4:
                resource_kind = _enum(raw, frames[0], len(t.KCS1AttemptResourceKindV1), capture)
                allowed = _nat(raw, frames[1], capture)
                required = _nat(raw, frames[2], capture)
                if allowed is not None and required is not None and required <= allowed:
                    _candidate(capture, 4, frames[2][1])
                if resource_kind is not None:
                    capture.relations.append((resource_kind, frames[3][1], frames[3][2]))
            for kind, frame in zip(kinds, frames, strict=True):
                lp, body, stop = frame
                length = stop - body
                if kind == "bytes32" and length != 32:
                    _candidate(capture, 5, lp)
                elif kind == "u64" and length != 8:
                    _candidate(capture, 5, lp)
                elif kind == "nat" and detail != 4:
                    _nat(raw, frame, capture)
                elif kind == "reject":
                    _enum(raw, frame, len(t.KCS1RejectCodeSyntaxV1), capture)
                elif kind == "internal":
                    _enum(raw, frame, len(t.KCS1InternalCodeV1), capture)
                elif kind == "attempt-kind" and detail != 4:
                    _enum(raw, frame, len(t.KCS1AttemptResourceKindV1), capture)
                elif kind in {"kpt", "kcf", "kci", "keb", "kcc"}:
                    capture.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), length))
                    sequence = _push(
                        heap, sequence, "dep", body, stop, depth + 1, ("kpt", "kcf", "kci", "keb", "kcc").index(kind)
                    )
                elif kind in {"kcn", "krl", "krf", "terminal"}:
                    capture.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), length))
                    child = {"kcn": 0, "krl": 3, "krf": 4, "terminal": 1}[kind]
                    if (
                        kind == "terminal"
                        and body + 5 <= stop
                        and raw[body : body + 4] == _PREFIXES[1]
                        and raw[body + 4] == 0
                    ):
                        _candidate(capture, 9, body + 4)
                    sequence = _push(heap, sequence, "owned", body, stop, depth + 1, child)
                elif kind.startswith("vec-"):
                    if length < 8:
                        _candidate(capture, 5, body + length)
                    else:
                        sequence = _push(heap, sequence, "vector", body, stop, depth + 1, 0 if kind == "vec-kpt" else 1)
            continue
        if task_kind == "vector":
            if start + 8 > end:
                _candidate(capture, 5, end)
                continue
            count = _read_u64(raw, start)
            capture.events.append((start, int(t.KCS1CodecResourceKindV1.VECTOR_ITEMS), count))
            offset = start + 8
            for _ in range(count):
                lp = offset
                if offset + 8 > end:
                    _candidate(capture, 5, lp)
                    break
                length = _read_u64(raw, offset)
                body, stop = offset + 8, offset + 8 + length
                if stop > end:
                    _candidate(capture, 5, lp)
                    break
                capture.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), length))
                sequence = _push(heap, sequence, "dep", body, stop, depth, detail)
                offset = stop
            else:
                if offset < end:
                    _candidate(capture, 10, offset)
            continue
        dep_kind = ("kpt", "kcf", "kci", "keb", "kcc")[detail]
        if dep_kind == "kpt":
            scanned = _frames(
                raw,
                start,
                end,
                b"KPT1",
                tuple(len(KPT1_FIELD_KINDS[tag]) for tag in KernelTermTagV1),
                False,
                capture,
            )
        elif dep_kind == "kcf":
            scanned = _frames(
                raw,
                start,
                end,
                b"KCF1",
                tuple(len(KCF1_FIELD_KINDS[tag]) for tag in KernelContinuationTagV1),
                False,
                capture,
            )
        else:
            scanned = _frames(
                raw,
                start,
                end,
                {"kci": b"KCI1", "keb": b"KEB1", "kcc": b"KCC1"}[dep_kind],
                {"kci": (2,), "keb": (2,), "kcc": (0,)}[dep_kind],
                True,
                capture,
            )
        if scanned is None:
            continue
        tag, frames = scanned
        capture.dependencies.append(_Dependency(dep_kind, start, end, depth, tag, frames))
        if dep_kind == "kpt":
            for kind, frame in zip(KPT1_FIELD_KINDS[KernelTermTagV1(tag)], frames, strict=True):
                lp, body, stop = frame
                length = stop - body
                if kind == "nat":
                    _nat(raw, frame, capture)
                elif kind == "digest" and length != 32:
                    _candidate(capture, 5, lp)
                elif kind in {"term", "level"}:
                    capture.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), length))
                    sequence = _push(heap, sequence, "kpt" if kind == "term" else "level", body, stop, depth + 1, 0)
                elif kind == "terms":
                    if length < 8:
                        _candidate(capture, 5, body + length)
                    else:
                        count = _read_u64(raw, body)
                        capture.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_LIST_ITEMS), count))
                        offset = body + 8
                        for _ in range(count):
                            lp_item = offset
                            if offset + 8 > stop:
                                _candidate(capture, 5, lp_item)
                                break
                            item_length = _read_u64(raw, offset)
                            item_body, item_stop = offset + 8, offset + 8 + item_length
                            if item_stop > stop:
                                _candidate(capture, 5, lp_item)
                                break
                            capture.events.append(
                                (item_body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), item_length)
                            )
                            sequence = _push(heap, sequence, "kpt", item_body, item_stop, depth + 1, 0)
                            offset = item_stop
                        else:
                            if offset < stop:
                                _candidate(capture, 10, offset)
        elif dep_kind == "kcf":
            for kind, frame in zip(KCF1_FIELD_KINDS[KernelContinuationTagV1(tag)], frames, strict=True):
                lp, body, stop = frame
                if kind == "term":
                    capture.events.append((body, int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), stop - body))
                    sequence = _push(heap, sequence, "dep", body, stop, depth + 1, 0)
                elif kind == "kernel_type_id" and stop - body != 32:
                    _candidate(capture, 5, lp)
        elif dep_kind == "keb":
            first, second = frames
            for frame in frames:
                capture.events.append((frame[1], int(t.KCS1CodecResourceKindV1.NESTED_WIRE_BYTES), frame[2] - frame[1]))
                sequence = _push(heap, sequence, "dep", frame[1], frame[2], depth + 1, 0)
            if first[2] - first[1] == second[2] - second[1]:
                for index in range(first[2] - first[1]):
                    if raw[first[1] + index] != raw[second[1] + index]:
                        _candidate(capture, 9, second[1] + index)
                        break
            else:
                _candidate(capture, 9, second[1] + min(first[2] - first[1], second[2] - second[1]))
    for resource_kind, locus_start, locus_end in capture.relations:
        scanned = _frames(raw, locus_start, locus_end, _PREFIXES[3], _ARITIES[3], True, _Capture())
        if scanned is not None and scanned[0] != _LEGAL_LOCUS[resource_kind]:
            _candidate(capture, 9, locus_start)
    logger.debug("_capture_wire exit decode=%d events=%d", len(capture.decode), len(capture.events))
    return capture


def _profiles(capture: _Capture) -> dict[tuple[str, int], _Profile]:
    """Derive exact positive-floor dependency profiles from captured spans."""
    logger.debug("_profiles entry dependencies=%d", len(capture.dependencies))
    result: dict[tuple[str, int], _Profile] = {}
    for dependency in capture.dependencies:
        node_events = [
            event
            for event in capture.events
            if event[1] == int(t.KCS1CodecResourceKindV1.COMPOSITE_NODES)
            and dependency.start <= event[0] < dependency.end
        ]
        depth_events = [
            event[2]
            for event in capture.events
            if event[1] == int(t.KCS1CodecResourceKindV1.COMPOSITE_DEPTH)
            and dependency.start <= event[0] < dependency.end
        ]
        list_events = [
            event[2]
            for event in capture.events
            if event[1] == int(t.KCS1CodecResourceKindV1.NESTED_LIST_ITEMS)
            and dependency.start <= event[0] < dependency.end
        ]
        nat_events = [
            event[2]
            for event in capture.events
            if event[1] == int(t.KCS1CodecResourceKindV1.NESTED_NAT_BYTES)
            and dependency.start <= event[0] < dependency.end
        ]
        profile = _Profile(
            dependency.end - dependency.start,
            max(depth_events, default=dependency.depth) - dependency.depth,
            len(node_events),
            max(list_events, default=0),
            max(nat_events, default=0),
        )
        if dependency.kind == "kcf":
            profile.nested_kpt = sum(
                frame[2] - frame[1]
                for kind, frame in zip(
                    KCF1_FIELD_KINDS[KernelContinuationTagV1(dependency.tag)], dependency.frames, strict=True
                )
                if kind == "term"
            )
        elif dependency.kind == "kci":
            profile.expected = dependency.frames[0][2] - dependency.frames[0][1]
            profile.term = dependency.frames[1][2] - dependency.frames[1][1]
        elif dependency.kind == "keb":
            profile.nested_kpt = dependency.frames[0][2] - dependency.frames[0][1]
            profile.expected_wire = dependency.frames[1][2] - dependency.frames[1][1]
        result[(dependency.kind, dependency.start)] = profile
    logger.debug("_profiles exit count=%d", len(result))
    return result


def _resource_candidate(capture: _Capture, values: tuple[int, ...]) -> tuple[int, int, int, int] | None:
    """Choose the exact prospective resource excess by offset then ordinal."""
    logger.debug("_resource_candidate entry")
    totals = [0] * 8
    candidates: list[tuple[int, int, int, int]] = []
    for offset, ordinal, amount in sorted(capture.events, key=lambda item: (item[0], item[1])):
        allowed = values[ordinal]
        required = amount if ordinal == int(t.KCS1CodecResourceKindV1.COMPOSITE_DEPTH) else totals[ordinal] + amount
        if required > allowed:
            candidates.append((offset, ordinal, allowed, required))
        if ordinal == int(t.KCS1CodecResourceKindV1.COMPOSITE_DEPTH):
            totals[ordinal] = max(totals[ordinal], amount)
        else:
            totals[ordinal] = required
    result = min(candidates) if candidates else None
    logger.debug("_resource_candidate exit found=%s", result is not None)
    return result


def _nested_failure(exc: object, base: int) -> NoReturn:
    logger.debug("_nested_failure entry base=%d", base)
    code = object.__getattribute__(exc, "code")
    offset = object.__getattribute__(exc, "offset")
    ordinal = object.__getattribute__(code, "_value_")
    if type(offset) is not int or type(ordinal) is not int or not 0 <= ordinal < 11 or not 0 <= offset < _U64_LIMIT:
        raise _Preflight(t.KCS1IntegrityCodeV1.NESTED_MAP_DRIFT)
    _bad(ordinal, base + offset)


def _parse_dependency(kind: str, payload: bytes, base: int, profile: _Profile) -> object:
    logger.debug("_parse_dependency entry kind=%s base=%d", kind, base)

    def positive(value: int) -> int:
        logger.debug("positive entry value=%d", value)
        result = max(1, value)
        logger.debug("positive exit result=%d", result)
        return result

    try:
        if kind == "kpt":
            result: object = parse_kernel_proof_term_v1(
                payload,
                KPT1LimitsV1(
                    positive(profile.size),
                    positive(profile.size),
                    positive(profile.depth),
                    positive(profile.nodes),
                    positive(profile.max_list),
                    positive(profile.max_nat),
                ),
            )
        elif kind == "kcf":
            result = parse_kernel_continuation_frame_v1(
                payload,
                KCF1LimitsV1(
                    positive(profile.size),
                    positive(profile.size),
                    positive(profile.depth + 1),
                    positive(profile.nodes),
                    positive(profile.nested_kpt),
                    positive(profile.max_list),
                    positive(profile.max_nat),
                ),
            )
        elif kind == "kcc":
            result = parse_empty_checker_config_v1(
                payload, KCC1LimitsV1(positive(profile.size), positive(profile.size))
            )
        elif kind == "kci":
            parsed = parse_checker_input_syntax_v1(
                payload,
                KCI1LimitsV1(
                    positive(profile.size), positive(profile.size), positive(profile.expected), positive(profile.term)
                ),
            )
            if type(parsed) is KCI1DecodedResultV1:
                result = object.__getattribute__(parsed, "value")
            elif type(parsed) is KCI1DecodeErrorResultV1:
                _nested_failure(object.__getattribute__(parsed, "error"), base)
            elif type(parsed) is KCI1ResourceParseResultV1:
                raise _Preflight(t.KCS1IntegrityCodeV1.NESTED_MAP_DRIFT)
            else:
                raise _Preflight(t.KCS1IntegrityCodeV1.NESTED_MAP_DRIFT)
        elif kind == "keb":
            parsed = parse_expected_binding_v1(
                payload,
                KEB1LimitsV1(
                    positive(profile.size),
                    positive(profile.size),
                    positive(profile.depth),
                    positive(profile.nodes),
                    positive(profile.nested_kpt),
                    positive(profile.max_list),
                    positive(profile.max_nat),
                    positive(profile.expected_wire),
                ),
            )
            if type(parsed) is KEB1DecodedResultV1:
                result = object.__getattribute__(parsed, "value")
            elif type(parsed) is KEB1DecodeErrorResultV1:
                _nested_failure(object.__getattribute__(parsed, "error"), base)
            elif type(parsed) is KEB1ResourceParseResultV1:
                raise _Preflight(t.KCS1IntegrityCodeV1.NESTED_MAP_DRIFT)
            else:
                raise _Preflight(t.KCS1IntegrityCodeV1.NESTED_MAP_DRIFT)
        else:
            raise _Preflight(t.KCS1IntegrityCodeV1.NESTED_MAP_DRIFT)
    except (KPT1DecodeError, KCF1DecodeError, KCC1DecodeError) as exc:
        _nested_failure(exc, base)
    except (KPT1ResourceLimit, KCF1ResourceLimit, KCC1ResourceLimit):
        raise _Preflight(t.KCS1IntegrityCodeV1.NESTED_MAP_DRIFT) from None
    logger.debug("_parse_dependency exit kind=%s", kind)
    return result


def _commit_frames(raw: bytes, start: int, arity: int) -> tuple[tuple[int, int, int], ...]:
    logger.debug("_commit_frames entry start=%d arity=%d", start, arity)
    offset = start + 6
    frames = []
    for _ in range(arity):
        length = _read_u64(raw, offset)
        frames.append((offset, offset + 8, offset + 8 + length))
        offset += 8 + length
    result = tuple(frames)
    logger.debug("_commit_frames exit")
    return result


def _commit_vector(
    raw: bytes, frame: tuple[int, int, int], kind: str, profiles: dict[tuple[str, int], _Profile]
) -> tuple[object, ...]:
    logger.debug("_commit_vector entry kind=%s", kind)
    _, start, _ = frame
    count = _read_u64(raw, start)
    offset = start + 8
    items = []
    for _ in range(count):
        length = _read_u64(raw, offset)
        body, stop = offset + 8, offset + 8 + length
        items.append(_parse_dependency(kind, raw[body:stop], body, profiles[(kind, body)]))
        offset = stop
    result = tuple(items)
    logger.debug("_commit_vector exit items=%d", len(result))
    return result


def _commit_value(raw: bytes, start: int, end: int, index: int, profiles: dict[tuple[str, int], _Profile]) -> object:
    logger.debug("_commit_value entry domain=%s start=%d", _DOMAIN_NAMES[index], start)
    tag = raw[start + 4]
    frames = _commit_frames(raw, start, _ARITIES[index][tag])

    def payload(position: int) -> bytes:
        logger.debug("payload entry position=%d", position)
        frame = frames[position]
        result = raw[frame[1] : frame[2]]
        logger.debug("payload exit bytes=%d", len(result))
        return result

    def dependency(position: int, kind: str) -> object:
        logger.debug("dependency entry position=%d kind=%s", position, kind)
        frame = frames[position]
        result = _parse_dependency(kind, raw[frame[1] : frame[2]], frame[1], profiles[(kind, frame[1])])
        logger.debug("dependency exit kind=%s", kind)
        return result

    result: object
    if index == 0:
        if tag == 0:
            result = build_kcs1_entry_node_v1(cast(ExpectedBindingSyntaxV1, dependency(0, "keb")))
        elif tag == 1:
            result = build_kcs1_parse_node_v1(payload(0))
        elif tag == 2:
            result = build_kcs1_infer_node_v1(cast(KernelProofTermV1, dependency(0, "kpt")))
        elif tag == 3:
            result = build_kcs1_reduce_node_v1(cast(KernelProofTermV1, dependency(0, "kpt")))
        elif tag == 4:
            result = build_kcs1_compare_types_node_v1(
                *(cast(KernelProofTermV1, dependency(position, "kpt")) for position in range(3))
            )
        else:
            result = build_kcs1_return_typed_node_v1(payload(0))
    elif index == 1:
        if tag == 0:
            result = build_kcs1_run_state_v1(
                cast(t.CheckerNodeSyntaxV1, _commit_value(raw, frames[0][1], frames[0][2], 0, profiles)),
                cast(EmptyCheckerConfigV1, dependency(1, "kcc")),
                cast(CheckerInputSyntaxV1, dependency(2, "kci")),
                cast(tuple[KernelProofTermV1, ...], _commit_vector(raw, frames[3], "kpt", profiles)),
                cast(tuple[KernelProofTermV1, ...], _commit_vector(raw, frames[4], "kpt", profiles)),
                cast(tuple[KernelContinuationFrameV1, ...], _commit_vector(raw, frames[5], "kcf", profiles)),
                _read_u64(raw, frames[6][1]),
            )
        elif tag == 1:
            result = build_kcs1_accept_state_v1(cast(KernelProofTermV1, dependency(0, "kpt")), payload(1))
        else:
            result = build_kcs1_reject_state_v1(
                t.KCS1RejectCodeSyntaxV1(raw[frames[0][1]]), _read_u64(raw, frames[1][1])
            )
    elif index == 2:
        term = cast(KernelProofTermV1, dependency(0, "kpt"))
        result = build_kcs1_nf_result_v1(term) if tag == 0 else build_kcs1_step_result_v1(term)
    elif index == 3:
        if tag == 0:
            result = build_kcs1_input_offset_locus_v1(_read_u64(raw, frames[0][1]))
        elif tag == 1:
            result = build_kcs1_state_step_locus_v1(cast(int, _nat(raw, frames[0], _Capture())))
        elif tag == 2:
            result = build_kcs1_structural_count_locus_v1(cast(int, _nat(raw, frames[0], _Capture())))
        else:
            result = build_kcs1_no_locus_v1()
    elif index == 4:
        result = build_kcs1_attempt_resource_v1(
            t.KCS1AttemptResourceKindV1(raw[frames[0][1]]),
            cast(int, _nat(raw, frames[1], _Capture())),
            cast(int, _nat(raw, frames[2], _Capture())),
            cast(t.ResourceLocusSyntaxV1, _commit_value(raw, frames[3][1], frames[3][2], 3, profiles)),
        )
    elif tag == 0:
        result = build_kcs1_terminal_attempt_v1(
            cast(
                t.KCS1AcceptStateV1 | t.KCS1RejectStateV1,
                _commit_value(raw, frames[0][1], frames[0][2], 1, profiles),
            )
        )
    elif tag == 1:
        result = build_kcs1_resource_attempt_v1(
            cast(t.KCS1AttemptResourceSyntaxV1, _commit_value(raw, frames[0][1], frames[0][2], 4, profiles))
        )
    else:
        result = build_kcs1_internal_attempt_v1(
            t.KCS1InternalCodeV1(raw[frames[0][1]]),
            cast(t.ResourceLocusSyntaxV1, _commit_value(raw, frames[1][1], frames[1][2], 3, profiles)),
        )
    logger.debug("_commit_value exit domain=%s", _DOMAIN_NAMES[index])
    return result


def _parse(domain: str, raw: bytes, limits: t.KCS1CodecLimitsV1) -> object:
    logger.debug("_parse entry domain=%s", domain)
    try:
        _validate_parser_public_v1()
        values = _snapshot_limits(limits)
        if type(raw) is not bytes:
            return _integrity_arm(domain, t.KCS1IntegrityCodeV1.HOST_SHAPE)
        if len(raw) > values[0]:
            return _resource_arm(domain, t.KCS1CodecResourceKindV1.INPUT_BYTES, values[0], len(raw), values[0])
        index = _DOMAIN_NAMES.index(domain)
        capture = _capture_wire(raw, index)
        if capture.decode:
            offset, ordinal = min(capture.decode)
            return _decode_arm(domain, ordinal, offset)
        profiles = _profiles(capture)
        excess = _resource_candidate(capture, values)
        if excess is not None:
            offset, ordinal, allowed, required = excess
            return _resource_arm(domain, t.KCS1CodecResourceKindV1(ordinal), allowed, required, offset)
        planned = len(raw)
        if planned > values[1]:
            return _resource_arm(domain, t.KCS1CodecResourceKindV1.OUTPUT_BYTES, values[1], planned, 0)
        value = _commit_value(raw, 0, len(raw), index, profiles)
        result = _decoded_arm(domain, value, planned)
        logger.debug("_parse exit domain=%s state=decoded", domain)
        return result
    except _Decode as exc:
        logger.debug("_parse exit domain=%s state=decode", domain)
        return _decode_arm(domain, exc.ordinal, exc.offset)
    except _Preflight as exc:
        logger.error("_parse error domain=%s integrity=%s", domain, exc.code.name)
        return _integrity_arm(domain, exc.code)
    except Exception as exc:
        logger.error("_parse error domain=%s exception=%s", domain, type(exc).__name__)
        return _integrity_arm(domain, t.KCS1IntegrityCodeV1.HOST_SHAPE)


def parse_kcn1_v1(raw: bytes, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1) -> t.KCN1ParseResultV1:
    logger.debug("parse_kcn1_v1 entry")
    result = cast(t.KCN1ParseResultV1, _parse("KCN1", raw, limits))
    logger.debug("parse_kcn1_v1 exit")
    return result


def parse_kcs1_v1(raw: bytes, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1) -> t.KCS1ParseResultV1:
    logger.debug("parse_kcs1_v1 entry")
    result = cast(t.KCS1ParseResultV1, _parse("KCS1", raw, limits))
    logger.debug("parse_kcs1_v1 exit")
    return result


def parse_krr1_v1(raw: bytes, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1) -> t.KRR1ParseResultV1:
    logger.debug("parse_krr1_v1 entry")
    result = cast(t.KRR1ParseResultV1, _parse("KRR1", raw, limits))
    logger.debug("parse_krr1_v1 exit")
    return result


def parse_krl1_v1(raw: bytes, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1) -> t.KRL1ParseResultV1:
    logger.debug("parse_krl1_v1 entry")
    result = cast(t.KRL1ParseResultV1, _parse("KRL1", raw, limits))
    logger.debug("parse_krl1_v1 exit")
    return result


def parse_krf1_v1(raw: bytes, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1) -> t.KRF1ParseResultV1:
    logger.debug("parse_krf1_v1 entry")
    result = cast(t.KRF1ParseResultV1, _parse("KRF1", raw, limits))
    logger.debug("parse_krf1_v1 exit")
    return result


def parse_kar1_v1(raw: bytes, limits: t.KCS1CodecLimitsV1 = t.DEFAULT_KCS1_CODEC_LIMITS_V1) -> t.KAR1ParseResultV1:
    logger.debug("parse_kar1_v1 entry")
    result = cast(t.KAR1ParseResultV1, _parse("KAR1", raw, limits))
    logger.debug("parse_kar1_v1 exit")
    return result


_PARSER_FUNCTIONS = (parse_kcn1_v1, parse_kcs1_v1, parse_krr1_v1, parse_krl1_v1, parse_krf1_v1, parse_kar1_v1)
_PARSER_NAMES = tuple(function.__name__ for function in _PARSER_FUNCTIONS)
_PARSER_CODES = tuple(function.__code__ for function in _PARSER_FUNCTIONS)


def _validate_parser_public_v1() -> None:
    logger.debug("_validate_parser_public_v1 entry")
    if any(
        globals().get(name) is not function
        or function.__code__ is not code
        or type(function.__defaults__) is not tuple
        or len(cast(tuple[object, ...], function.__defaults__)) != 1
        or cast(tuple[object, ...], function.__defaults__)[0] is not t.DEFAULT_KCS1_CODEC_LIMITS_V1
        for name, function, code in zip(_PARSER_NAMES, _PARSER_FUNCTIONS, _PARSER_CODES, strict=True)
    ):
        logger.error("_validate_parser_public_v1 error drift")
        raise ValueError("kcs1-parser-public-drift")
    logger.debug("_validate_parser_public_v1 exit")
