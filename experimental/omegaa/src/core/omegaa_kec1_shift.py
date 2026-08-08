"""Explicit-work de Bruijn shift and universe quotation for KEC1."""

from __future__ import annotations

import logging
from typing import cast

from .omegaa_kec1_builder import Builder, clone_level_task, nat_add_bytes, nat_bytes
from .omegaa_kec1_common import (
    WorkFactory,
    WorkGenerator,
    _Integrity,
    level_slot,
    locus,
    refuse,
    term_slot,
    work_request,
)
from .omegaa_kec1_types import KEC1IntegrityCodeV1, KEC1LocusV1, KEC1OriginV1, KEC1RefusalCodeV1
from .omegaa_kpt1_types import (
    KPT1_FIELD_KINDS,
    KernelLevelTagV1,
    KernelProofTermV1,
    KernelTermTagV1,
    KernelUniverseLevelV1,
)

logger = logging.getLogger(__name__)
_BINDERS = frozenset((KernelTermTagV1.PI, KernelTermTagV1.LAM, KernelTermTagV1.SIGMA, KernelTermTagV1.LET))
_EMPTY = frozenset((KernelTermTagV1.CONST, KernelTermTagV1.CTOR, KernelTermTagV1.REC))


def reject_unsupported(tag: KernelTermTagV1, where: KEC1LocusV1) -> None:
    """Refuse dependency tags before any semantic child is scheduled."""
    logger.debug("reject_unsupported entry tag=%s", tag.name)
    if tag in _EMPTY:
        logger.info("reject_unsupported refusal empty-dependency")
        refuse(KEC1RefusalCodeV1.EMPTY_DEPENDENCY, where)
    if tag is KernelTermTagV1.J:
        logger.info("reject_unsupported refusal j-unfrozen")
        refuse(KEC1RefusalCodeV1.J_RULE_UNFROZEN, where)
    logger.debug("reject_unsupported exit tag=%s", tag.name)


def quote_level_task(
    level: KernelUniverseLevelV1,
    builder: Builder,
    origin: KEC1OriginV1,
    path: tuple[int, ...] = (),
) -> WorkGenerator[KernelUniverseLevelV1]:
    """Apply QL on the explicit LIFO machine with exact child paths."""
    logger.debug("quote_level_task entry path=%s", path)
    tag, raw = level_slot(level)
    if type(tag) is not KernelLevelTagV1 or type(raw) is not tuple:
        logger.error("quote_level_task error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    here = locus(origin, path, 0)
    if raw:

        def allocate() -> tuple[WorkFactory, ...]:
            logger.debug("quote_level_task allocate children=%d", len(raw))
            return tuple(
                lambda child=child, child_path=path + (index,): quote_level_task(
                    cast(KernelUniverseLevelV1, child), builder, origin, child_path
                )
                for index, child in enumerate(raw)
            )

        children = cast(tuple[KernelUniverseLevelV1, ...], (yield work_request(len(raw), here, allocate)))
    else:
        children = ()
    result = builder.level(tag, children, here)
    logger.debug("quote_level_task exit path=%s", path)
    return result


def shift_task(
    cutoff: int,
    delta: int,
    root: KernelProofTermV1,
    builder: Builder,
    origin: KEC1OriginV1,
    refusal_root: KEC1LocusV1,
    path: tuple[int, ...] = (),
) -> WorkGenerator[KernelProofTermV1]:
    """Fresh exact shift using explicit child batches and precharged Nat bytes."""
    logger.debug("shift_task entry cutoff=%d delta=%d path=%s", cutoff, delta, path)
    if any(type(value) is not int or value < 0 for value in (cutoff, delta)):
        logger.error("shift_task error invalid-index")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    tag, raw = term_slot(root)
    if type(tag) is not KernelTermTagV1 or type(raw) is not tuple:
        logger.error("shift_task error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    here = locus(origin, path, 4)
    reject_unsupported(tag, refusal_root if not path else here)
    if tag is KernelTermTagV1.VAR:
        value = cast(int, raw[0])
        encoded = nat_add_bytes(value, delta) if value >= cutoff else value.to_bytes(nat_bytes(value), "big")
        result = builder.nat_term(encoded, here)
        logger.debug("shift_task exit var path=%s", path)
        return result

    specs: list[tuple[str, object, int, tuple[int, ...]]] = []
    ordinal = 0
    for position, (kind, value) in enumerate(zip(KPT1_FIELD_KINDS[tag], raw, strict=True)):
        child_cutoff = cutoff + 1 if tag in _BINDERS and position == len(raw) - 1 else cutoff
        if kind in {"term", "level"}:
            specs.append((kind, value, child_cutoff, path + (ordinal,)))
            ordinal += 1
        elif kind == "terms":
            for item in cast(tuple[KernelProofTermV1, ...], value):
                specs.append(("term", item, cutoff, path + (ordinal,)))
                ordinal += 1
    if specs:

        def allocate() -> tuple[WorkFactory, ...]:
            logger.debug("shift_task allocate children=%d", len(specs))
            factories: list[WorkFactory] = []
            for kind, child, child_cutoff, child_path in specs:
                if kind == "term":
                    factories.append(
                        lambda child=child, child_cutoff=child_cutoff, child_path=child_path: shift_task(  # type: ignore[misc]
                            child_cutoff,
                            delta,
                            cast(KernelProofTermV1, child),
                            builder,
                            origin,
                            refusal_root,
                            child_path,
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
    logger.debug("shift_task exit path=%s", path)
    return result
