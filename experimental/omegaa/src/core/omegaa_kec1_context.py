"""Streaming hostile-safe input capture and immutable KEC1 snapshots."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from types import MappingProxyType
from typing import Mapping, cast

from .omegaa_kec1_builder import level_metrics, nat_bytes, snapshot_level, snapshot_term, term_metrics
from .omegaa_kec1_common import Metrics, _Integrity, _Resource, level_slot, locus, origin_v1, term_slot
from .omegaa_kec1_types import (
    ContextV1,
    KEC1ApiV1,
    KEC1IntegrityCodeV1,
    KEC1LocusV1,
    KEC1OffsetSpaceV1,
    KEC1OriginTagV1,
    KEC1OriginV1,
    KEC1ResourceKindV1,
)
from .omegaa_kpt1_types import (
    KPT1_FIELD_KINDS,
    KernelLevelTagV1,
    KernelProofTermV1,
    KernelTermTagV1,
    KernelUniverseLevelV1,
)
from .omegaa_kpt1_common import KPT1_MAX_SAFE_DEPTH

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _Cursor:
    node: object
    kind: str
    path: tuple[int, ...]
    origin: KEC1OriginV1
    entered: bool = False
    tag: object | None = None
    raw: tuple[object, ...] = ()
    clean: list[object] | None = None
    field: int = 0
    item: int = 0
    ordinal: int = 0
    list_items: list[int] | None = None
    where: KEC1LocusV1 | None = None


@dataclass(frozen=True, slots=True)
class _RawNode:
    kind: str
    tag: KernelTermTagV1 | KernelLevelTagV1
    fields: tuple[object, ...]
    locus: KEC1LocusV1


@dataclass(frozen=True, slots=True)
class PreparedInputs:
    """Owned immutable KPT snapshots; caller objects are deliberately absent."""

    context: ContextV1
    term: KernelProofTermV1
    expected: KernelProofTermV1 | None
    loci: Mapping[int, KEC1LocusV1]
    metrics: Mapping[int, Metrics]

    def where(self, node: object) -> KEC1LocusV1:
        logger.debug("PreparedInputs.where entry")
        try:
            result = self.loci[id(node)]
        except KeyError:
            logger.error("PreparedInputs.where error missing-snapshot")
            raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT) from None
        logger.debug("PreparedInputs.where exit")
        return result


def _origins(
    api: KEC1ApiV1, context: ContextV1, term: KernelProofTermV1, expected: KernelProofTermV1 | None
) -> list[tuple[KEC1OriginV1, KernelProofTermV1]]:
    logger.debug("_origins entry api=%s context=%d", api.name, len(context))
    roots = [(origin_v1(KEC1OriginTagV1.CONTEXT, i), context[i]) for i in range(len(context) - 1, -1, -1)]
    if api is KEC1ApiV1.CHECK:
        if expected is None:
            logger.error("_origins error missing-expected")
            raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
        roots.append((origin_v1(KEC1OriginTagV1.EXPECTED), expected))
    roots.append((origin_v1(KEC1OriginTagV1.TERM), term))
    logger.debug("_origins exit roots=%d", len(roots))
    return roots


def _capture(
    roots: list[tuple[KEC1OriginV1, KernelProofTermV1]], values: tuple[int, ...]
) -> tuple[
    dict[int, _RawNode],
    list[tuple[KEC1OriginV1, int, int]],
    list[tuple[int, KEC1LocusV1]],
    list[tuple[int, KEC1LocusV1]],
    list[tuple[int, KEC1LocusV1]],
    list[tuple[int, KEC1LocusV1]],
]:
    """Capture caller slots once with a one-child cursor and no KPT allocation."""
    logger.debug("_capture entry roots=%d", len(roots))
    raw_nodes: dict[int, _RawNode] = {}
    root_sizes: list[tuple[KEC1OriginV1, int, int]] = []
    node_sites: list[tuple[int, KEC1LocusV1]] = []
    depth_sites: list[tuple[int, KEC1LocusV1]] = []
    list_sites: list[tuple[int, KEC1LocusV1]] = []
    nat_sites: list[tuple[int, KEC1LocusV1]] = []
    seen: set[int] = set()
    active: set[int] = set()
    node_count = 0

    for origin, root in roots:
        wire = 0
        stack: list[_Cursor] = [_Cursor(root, "term", (), origin)]
        while stack:
            cursor = stack[-1]
            key = id(cursor.node)
            if not cursor.entered:
                depth = len(cursor.path)
                if depth > KPT1_MAX_SAFE_DEPTH:
                    logger.error("_capture error unsafe-depth=%d", depth)
                    raise _Resource(KEC1ResourceKindV1.INPUT_DEPTH, values[2], depth, locus(origin, cursor.path))
                if key in active:
                    logger.error("_capture error graph-cycle")
                    raise _Integrity(KEC1IntegrityCodeV1.GRAPH_CYCLE)
                if key in seen:
                    logger.error("_capture error graph-shared")
                    raise _Integrity(KEC1IntegrityCodeV1.GRAPH_SHARED)
                seen.add(key)
                active.add(key)
                node_count += 1
                if cursor.kind == "term":
                    if type(cursor.node) is not KernelProofTermV1:
                        logger.error("_capture error term-class")
                        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
                    tag, fields = term_slot(cursor.node)
                    if type(tag) is not KernelTermTagV1 or type(fields) is not tuple:
                        logger.error("_capture error term-slots")
                        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
                    try:
                        kinds = KPT1_FIELD_KINDS[tag]
                    except BaseException:
                        logger.error("_capture error field-table")
                        raise _Integrity(KEC1IntegrityCodeV1.TABLE_DRIFT) from None
                    if len(fields) != len(kinds):
                        logger.error("_capture error term-arity")
                        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
                    here = locus(origin, cursor.path, wire + 4)
                    wire += 6
                else:
                    if type(cursor.node) is not KernelUniverseLevelV1:
                        logger.error("_capture error level-class")
                        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
                    tag, fields = level_slot(cursor.node)
                    if type(tag) is not KernelLevelTagV1 or type(fields) is not tuple or len(fields) != int(tag):
                        logger.error("_capture error level-slots")
                        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
                    here = locus(origin, cursor.path, wire)
                    wire += 1
                cursor.entered = True
                cursor.tag = tag
                cursor.raw = fields
                cursor.clean = []
                cursor.where = here
                node_sites.append((node_count, here))
                depth_sites.append((depth, here))
                continue

            assert cursor.clean is not None
            kinds = (
                ("level",) * len(cursor.raw)
                if cursor.kind == "level"
                else KPT1_FIELD_KINDS[cast(KernelTermTagV1, cursor.tag)]
            )
            if cursor.field >= len(kinds):
                if cursor.list_items is not None:
                    cursor.clean.append(tuple(cursor.list_items))
                    cursor.list_items = None
                tag = cast(KernelTermTagV1 | KernelLevelTagV1, cursor.tag)
                if cursor.where is None:
                    logger.error("_capture error missing-locus")
                    raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
                raw_nodes[key] = _RawNode(cursor.kind, tag, tuple(cursor.clean), cursor.where)
                active.remove(key)
                stack.pop()
                continue

            field_kind = kinds[cursor.field]
            value = cursor.raw[cursor.field]
            if field_kind == "nat":
                wire += 8
                size = nat_bytes(cast(int, value))
                nat_sites.append((size, locus(origin, cursor.path, wire + 8)))
                wire += 8 + size
                cursor.clean.append(value)
                cursor.field += 1
                continue
            if field_kind == "digest":
                wire += 8
                if type(value) is not bytes or len(value) != 32:
                    logger.error("_capture error digest")
                    raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
                cursor.clean.append(value)
                wire += 32
                cursor.field += 1
                continue
            if field_kind in {"term", "level"}:
                wire += 8
                cursor.clean.append(id(value))
                child_path = cursor.path + (cursor.ordinal,)
                cursor.ordinal += 1
                cursor.field += 1
                stack.append(_Cursor(value, field_kind, child_path, origin))
                continue
            if cursor.list_items is None:
                wire += 8
                if type(value) is not tuple:
                    logger.error("_capture error terms-class")
                    raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
                list_sites.append((len(value), locus(origin, cursor.path, wire)))
                wire += 8
                cursor.list_items = []
            items = cast(tuple[object, ...], value)
            if cursor.item >= len(items):
                cursor.clean.append(tuple(cursor.list_items))
                cursor.list_items = None
                cursor.item = 0
                cursor.field += 1
                continue
            child = items[cursor.item]
            wire += 8
            cursor.list_items.append(id(child))
            child_path = cursor.path + (cursor.ordinal,)
            cursor.ordinal += 1
            cursor.item += 1
            stack.append(_Cursor(child, "term", child_path, origin))
        root_sizes.append((origin, id(root), wire))

    logger.debug("_capture exit nodes=%d", node_count)
    return raw_nodes, root_sizes, node_sites, depth_sites, list_sites, nat_sites


def _gate_inputs(
    root_sizes: list[tuple[KEC1OriginV1, int, int]],
    node_sites: list[tuple[int, KEC1LocusV1]],
    depth_sites: list[tuple[int, KEC1LocusV1]],
    list_sites: list[tuple[int, KEC1LocusV1]],
    nat_sites: list[tuple[int, KEC1LocusV1]],
    values: tuple[int, ...],
) -> None:
    """Apply exact INPUT_BYTES then node/depth/list/Nat ordinal gates."""
    logger.debug("_gate_inputs entry")
    total = 0
    for origin, _key, wire in root_sizes:
        framed = 8 + wire
        if total + framed > values[0]:
            excess = values[0] - total
            where = (
                locus(origin, (), excess, KEC1OffsetSpaceV1.ORIGIN_FRAME)
                if excess < 8
                else locus(origin, (), excess - 8, KEC1OffsetSpaceV1.KPT_WIRE)
            )
            logger.error("_gate_inputs resource input-bytes")
            raise _Resource(KEC1ResourceKindV1.INPUT_BYTES, values[0], values[0] + 1, where)
        total += framed
    for current, where in node_sites:
        if current > values[1]:
            logger.error("_gate_inputs resource input-nodes")
            raise _Resource(KEC1ResourceKindV1.INPUT_NODES, values[1], current, where)
    for current, where in depth_sites:
        if current > values[2]:
            logger.error("_gate_inputs resource input-depth")
            raise _Resource(KEC1ResourceKindV1.INPUT_DEPTH, values[2], current, where)
    for current, where in list_sites:
        if current > values[3]:
            logger.error("_gate_inputs resource input-list")
            raise _Resource(KEC1ResourceKindV1.INPUT_LIST_ITEMS, values[3], current, where)
    for current, where in nat_sites:
        if current > values[4]:
            logger.error("_gate_inputs resource input-nat")
            raise _Resource(KEC1ResourceKindV1.INPUT_NAT_BYTES, values[4], current, where)
    logger.debug("_gate_inputs exit")


def _build_snapshots(
    raw_nodes: dict[int, _RawNode], root_keys: tuple[int, ...]
) -> tuple[dict[int, KernelProofTermV1 | KernelUniverseLevelV1], dict[int, Metrics], dict[int, KEC1LocusV1]]:
    """Build hook-free owned snapshots only after every input gate succeeds."""
    logger.debug("_build_snapshots entry roots=%d", len(root_keys))
    postorder: list[int] = []
    for root_key in root_keys:
        stack: list[tuple[int, bool]] = [(root_key, False)]
        while stack:
            key, exiting = stack.pop()
            if exiting:
                postorder.append(key)
                continue
            stack.append((key, True))
            raw = raw_nodes[key]
            kinds = (
                ("level",) * len(raw.fields)
                if raw.kind == "level"
                else KPT1_FIELD_KINDS[cast(KernelTermTagV1, raw.tag)]
            )
            children: list[int] = []
            for kind, value in zip(kinds, raw.fields, strict=True):
                if kind in {"term", "level"}:
                    children.append(cast(int, value))
                elif kind == "terms":
                    children.extend(cast(tuple[int, ...], value))
            stack.extend((child, False) for child in reversed(children))
    built: dict[int, KernelProofTermV1 | KernelUniverseLevelV1] = {}
    metrics: dict[int, Metrics] = {}
    loci: dict[int, KEC1LocusV1] = {}
    for key in postorder:
        raw = raw_nodes[key]
        fields: list[object] = []
        kinds = (
            ("level",) * len(raw.fields) if raw.kind == "level" else KPT1_FIELD_KINDS[cast(KernelTermTagV1, raw.tag)]
        )
        for kind, value in zip(kinds, raw.fields, strict=True):
            if kind in {"term", "level"}:
                fields.append(built[cast(int, value)])
            elif kind == "terms":
                fields.append(tuple(cast(KernelProofTermV1, built[item]) for item in cast(tuple[int, ...], value)))
            else:
                fields.append(value)
        frozen = tuple(fields)
        if raw.kind == "level":
            tag = cast(KernelLevelTagV1, raw.tag)
            node = snapshot_level(tag, cast(tuple[KernelUniverseLevelV1, ...], frozen))
            metric = level_metrics(tag, cast(tuple[KernelUniverseLevelV1, ...], frozen), metrics)
        else:
            tag = cast(KernelTermTagV1, raw.tag)
            node = snapshot_term(tag, frozen)
            metric = term_metrics(tag, frozen, metrics)
        built[key] = node
        metrics[id(node)] = metric
        loci[id(node)] = raw.locus
    logger.debug("_build_snapshots exit")
    return built, metrics, loci


def prepare_inputs(
    api: KEC1ApiV1, context: object, term: object, expected: object, values: tuple[int, ...]
) -> PreparedInputs:
    """Capture once, gate deterministically, then publish only owned snapshots."""
    logger.debug("prepare_inputs entry api=%s", api.name)
    if type(context) is not tuple or any(type(x) is not KernelProofTermV1 for x in context):
        logger.error("prepare_inputs error context-shape")
        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
    if type(term) is not KernelProofTermV1:
        logger.error("prepare_inputs error term-shape")
        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
    if api is KEC1ApiV1.CHECK:
        if type(expected) is not KernelProofTermV1:
            logger.error("prepare_inputs error expected-shape")
            raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
    elif expected is not None:
        logger.error("prepare_inputs error unexpected-expected")
        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
    typed_context: ContextV1 = context
    typed_term = cast(KernelProofTermV1, term)
    typed_expected: KernelProofTermV1 | None = expected
    roots = _origins(api, typed_context, typed_term, typed_expected)
    raw, root_sizes, node_sites, depth_sites, list_sites, nat_sites = _capture(roots, values)
    _gate_inputs(root_sizes, node_sites, depth_sites, list_sites, nat_sites, values)
    built, metrics, loci = _build_snapshots(raw, tuple(key for _origin, key, _wire in root_sizes))
    owned_context = tuple(cast(KernelProofTermV1, built[id(item)]) for item in typed_context)
    owned_term = cast(KernelProofTermV1, built[id(typed_term)])
    owned_expected = None if typed_expected is None else cast(KernelProofTermV1, built[id(typed_expected)])
    logger.debug("prepare_inputs exit snapshots=%d", len(built))
    return PreparedInputs(
        owned_context,
        owned_term,
        owned_expected,
        MappingProxyType(loci),
        MappingProxyType(metrics),
    )
