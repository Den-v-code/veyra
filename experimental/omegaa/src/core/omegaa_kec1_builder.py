"""Hook-free fresh KPT construction with prospective KEC1 generated charging."""

from __future__ import annotations

import logging
from typing import Protocol, cast

from .omegaa_kec1_common import (
    Engine,
    Metrics,
    WorkFactory,
    WorkGenerator,
    _Integrity,
    level_slot,
    locus,
    term_slot,
    work_request,
)
from .omegaa_kec1_types import KEC1IntegrityCodeV1, KEC1LocusV1, KEC1OriginV1
from .omegaa_kpt1_types import (
    KPT1_FIELD_KINDS,
    KernelLevelTagV1,
    KernelProofTermV1,
    KernelTermTagV1,
    KernelUniverseLevelV1,
)

logger = logging.getLogger(__name__)
_TERM_CLASS = KernelProofTermV1
_LEVEL_CLASS = KernelUniverseLevelV1
_TERM_TAG_SLOT = vars(_TERM_CLASS)["tag"]
_TERM_FIELDS_SLOT = vars(_TERM_CLASS)["fields"]
_LEVEL_TAG_SLOT = vars(_LEVEL_CLASS)["tag"]
_LEVEL_FIELDS_SLOT = vars(_LEVEL_CLASS)["fields"]
_OBJECT_NEW = object.__new__


class _Setter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def nat_bytes(value: int) -> int:
    """Return canonical unsigned magnitude bytes (zero has empty magnitude)."""
    logger.debug("nat_bytes entry")
    if type(value) is not int or value < 0:
        logger.error("nat_bytes error host-shape")
        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE)
    result = 0 if value == 0 else (value.bit_length() + 7) // 8
    logger.debug("nat_bytes exit bytes=%d", result)
    return result


def nat_add_bytes(left: int, right: int) -> bytes:
    """Compute canonical ``left+right`` bytes without allocating the sum integer."""
    logger.debug("nat_add_bytes entry")
    if type(left) is not int or type(right) is not int or left < 0 or right < 0:
        logger.error("nat_add_bytes error invalid-nat")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    width = max(nat_bytes(left), nat_bytes(right), 1)
    a = left.to_bytes(width, "big")
    b = right.to_bytes(width, "big")
    out = bytearray(width + 1)
    carry = 0
    for index in range(width - 1, -1, -1):
        total = a[index] + b[index] + carry
        out[index + 1] = total & 0xFF
        carry = total >> 8
    out[0] = carry
    result = bytes(out).lstrip(b"\x00")
    logger.debug("nat_add_bytes exit bytes=%d", len(result))
    return result


def nat_pred_bytes(value: int) -> bytes:
    """Compute canonical ``value-1`` bytes without allocating that integer."""
    logger.debug("nat_pred_bytes entry")
    if type(value) is not int or value <= 0:
        logger.error("nat_pred_bytes error nonpositive")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    out = bytearray(value.to_bytes(nat_bytes(value), "big"))
    index = len(out) - 1
    while out[index] == 0:
        out[index] = 0xFF
        index -= 1
    out[index] -= 1
    result = bytes(out).lstrip(b"\x00")
    logger.debug("nat_pred_bytes exit bytes=%d", len(result))
    return result


def snapshot_level(tag: KernelLevelTagV1, fields: tuple[KernelUniverseLevelV1, ...]) -> KernelUniverseLevelV1:
    """Construct one uncharged owned level snapshot after input gates."""
    logger.debug("snapshot_level entry tag=%s", tag.name)
    result = _OBJECT_NEW(_LEVEL_CLASS)
    cast(_Setter, _LEVEL_TAG_SLOT).__set__(result, tag)
    cast(_Setter, _LEVEL_FIELDS_SLOT).__set__(result, fields)
    logger.debug("snapshot_level exit tag=%s", tag.name)
    return result


def snapshot_term(tag: KernelTermTagV1, fields: tuple[object, ...]) -> KernelProofTermV1:
    """Construct one uncharged owned term snapshot after input gates."""
    logger.debug("snapshot_term entry tag=%s", tag.name)
    result = _OBJECT_NEW(_TERM_CLASS)
    cast(_Setter, _TERM_TAG_SLOT).__set__(result, tag)
    cast(_Setter, _TERM_FIELDS_SLOT).__set__(result, fields)
    logger.debug("snapshot_term exit tag=%s", tag.name)
    return result


def level_metrics(
    tag: KernelLevelTagV1, fields: tuple[KernelUniverseLevelV1, ...], metrics: dict[int, Metrics]
) -> Metrics:
    """Compute complete prospective level metrics without constructing it."""
    logger.debug("level_metrics entry tag=%s", tag.name)
    if type(tag) is not KernelLevelTagV1 or type(fields) is not tuple:
        logger.error("level_metrics error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    children = [metrics[id(child)] for child in fields]
    result = Metrics(
        0 if not children else 1 + max(x.depth for x in children),
        1 + sum(x.nodes for x in children),
        1 + sum(8 + x.wire_bytes for x in children),
        max((x.list_items for x in children), default=0),
        max((x.nat_bytes for x in children), default=0),
    )
    logger.debug("level_metrics exit nodes=%d", result.nodes)
    return result


def term_metrics(tag: KernelTermTagV1, fields: tuple[object, ...], metrics: dict[int, Metrics]) -> Metrics:
    """Compute complete prospective canonical KPT metrics without construction."""
    logger.debug("term_metrics entry tag=%s", tag.name)
    if type(tag) is not KernelTermTagV1 or type(fields) is not tuple:
        logger.error("term_metrics error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    child_metrics: list[Metrics] = []
    wire = 6
    own_list = 0
    own_nat = 0
    for kind, value in zip(KPT1_FIELD_KINDS[tag], fields, strict=True):
        if kind == "nat":
            own_nat = max(own_nat, nat_bytes(cast(int, value)))
            wire += 16 + own_nat
        elif kind == "digest":
            wire += 40
        elif kind in {"term", "level"}:
            metric = metrics[id(value)]
            child_metrics.append(metric)
            wire += 8 + metric.wire_bytes
        else:
            items = cast(tuple[KernelProofTermV1, ...], value)
            own_list = max(own_list, len(items))
            item_metrics = [metrics[id(item)] for item in items]
            child_metrics.extend(item_metrics)
            wire += 16 + sum(8 + metric.wire_bytes for metric in item_metrics)
    result = Metrics(
        0 if not child_metrics else 1 + max(x.depth for x in child_metrics),
        1 + sum(x.nodes for x in child_metrics),
        wire,
        max([own_list, *(x.list_items for x in child_metrics)]),
        max([own_nat, *(x.nat_bytes for x in child_metrics)]),
    )
    logger.debug("term_metrics exit nodes=%d", result.nodes)
    return result


class Builder:
    """Captured plan/charge/commit builder for one request engine."""

    def __init__(self, engine: Engine) -> None:
        logger.debug("Builder.__init__ entry")
        self.engine = engine
        self.metrics: dict[int, Metrics] = {}
        self.loci: dict[int, KEC1LocusV1] = {}
        logger.debug("Builder.__init__ exit")

    def level(
        self, tag: KernelLevelTagV1, fields: tuple[KernelUniverseLevelV1, ...], where: KEC1LocusV1
    ) -> KernelUniverseLevelV1:
        logger.debug("Builder.level entry")
        planned = level_metrics(tag, fields, self.metrics)
        self.engine.generated(planned, where)
        result = _OBJECT_NEW(_LEVEL_CLASS)
        cast(_Setter, _LEVEL_TAG_SLOT).__set__(result, tag)
        cast(_Setter, _LEVEL_FIELDS_SLOT).__set__(result, fields)
        self.metrics[id(result)] = planned
        self.loci[id(result)] = where
        logger.debug("Builder.level exit")
        return result

    def term(self, tag: KernelTermTagV1, fields: tuple[object, ...], where: KEC1LocusV1) -> KernelProofTermV1:
        logger.debug("Builder.term entry tag=%s", tag.name)
        planned = term_metrics(tag, fields, self.metrics)
        self.engine.generated(planned, where)
        result = _OBJECT_NEW(_TERM_CLASS)
        cast(_Setter, _TERM_TAG_SLOT).__set__(result, tag)
        cast(_Setter, _TERM_FIELDS_SLOT).__set__(result, fields)
        self.metrics[id(result)] = planned
        self.loci[id(result)] = where
        logger.debug("Builder.term exit tag=%s", tag.name)
        return result

    def nat_term(self, encoded: bytes, where: KEC1LocusV1) -> KernelProofTermV1:
        """Charge a complete VAR plan before allocating its Nat integer or node."""
        logger.debug("Builder.nat_term entry bytes=%d", len(encoded))
        if type(encoded) is not bytes or (encoded[:1] == b"\x00"):
            logger.error("Builder.nat_term error noncanonical")
            raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
        planned = Metrics(0, 1, 22 + len(encoded), 0, len(encoded))
        self.engine.generated(planned, where)
        value = int.from_bytes(encoded, "big") if encoded else 0
        result = snapshot_term(KernelTermTagV1.VAR, (value,))
        self.metrics[id(result)] = planned
        self.loci[id(result)] = where
        logger.debug("Builder.nat_term exit")
        return result


def clone_level_task(
    root: KernelUniverseLevelV1,
    builder: Builder,
    origin: KEC1OriginV1,
    path: tuple[int, ...] = (),
) -> WorkGenerator[KernelUniverseLevelV1]:
    """Explicit-work deep clone of one level snapshot."""
    logger.debug("clone_level_task entry path=%s", path)
    tag, raw = level_slot(root)
    if type(tag) is not KernelLevelTagV1 or type(raw) is not tuple:
        logger.error("clone_level_task error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    here = locus(origin, path, 0)
    if raw:

        def allocate() -> tuple[WorkFactory, ...]:
            logger.debug("clone_level_task allocate children=%d", len(raw))
            return tuple(
                lambda child=child, child_path=path + (index,): clone_level_task(
                    cast(KernelUniverseLevelV1, child), builder, origin, child_path
                )
                for index, child in enumerate(raw)
            )

        children = cast(tuple[KernelUniverseLevelV1, ...], (yield work_request(len(raw), here, allocate)))
    else:
        children = ()
    result = builder.level(tag, children, here)
    logger.debug("clone_level_task exit path=%s", path)
    return result


def clone_term_task(
    root: KernelProofTermV1,
    builder: Builder,
    origin: KEC1OriginV1,
    path: tuple[int, ...] = (),
) -> WorkGenerator[KernelProofTermV1]:
    """Explicit-work deep clone preserving the exact base path and ordinals."""
    logger.debug("clone_term_task entry path=%s", path)
    tag, raw = term_slot(root)
    if type(tag) is not KernelTermTagV1 or type(raw) is not tuple:
        logger.error("clone_term_task error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    specs: list[tuple[str, object, tuple[int, ...]]] = []
    ordinal = 0
    for kind, value in zip(KPT1_FIELD_KINDS[tag], raw, strict=True):
        if kind in {"term", "level"}:
            specs.append((kind, value, path + (ordinal,)))
            ordinal += 1
        elif kind == "terms":
            for item in cast(tuple[KernelProofTermV1, ...], value):
                specs.append(("term", item, path + (ordinal,)))
                ordinal += 1
    here = locus(origin, path, 4)
    if specs:

        def allocate() -> tuple[WorkFactory, ...]:
            logger.debug("clone_term_task allocate children=%d", len(specs))
            factories: list[WorkFactory] = []
            for kind, child, child_path in specs:
                if kind == "term":
                    factories.append(
                        lambda child=child, child_path=child_path: clone_term_task(  # type: ignore[misc]
                            cast(KernelProofTermV1, child), builder, origin, child_path
                        )
                    )
                else:
                    factories.append(
                        lambda child=child, child_path=child_path: clone_level_task(  # type: ignore[misc]
                            cast(KernelUniverseLevelV1, child), builder, origin, child_path
                        )
                    )
            return tuple(factories)

        children = cast(tuple[object, ...], (yield work_request(len(specs), here, allocate)))
    else:
        children = ()
    child_index = 0
    built: list[object] = []
    for kind, value in zip(KPT1_FIELD_KINDS[tag], raw, strict=True):
        if kind in {"term", "level"}:
            built.append(children[child_index])
            child_index += 1
        elif kind == "terms":
            count = len(cast(tuple[KernelProofTermV1, ...], value))
            built.append(tuple(cast(KernelProofTermV1, item) for item in children[child_index : child_index + count]))
            child_index += count
        else:
            built.append(value)
    result = builder.term(tag, tuple(built), here)
    logger.debug("clone_term_task exit path=%s", path)
    return result
