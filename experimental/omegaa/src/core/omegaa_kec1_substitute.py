"""Explicit-work capture-avoiding KEC1 de Bruijn substitution."""

from __future__ import annotations

import logging
from typing import cast

from .omegaa_kec1_builder import (
    Builder,
    clone_level_task,
    clone_term_task,
    nat_bytes,
    nat_pred_bytes,
)
from .omegaa_kec1_common import WorkFactory, WorkGenerator, _Integrity, locus, term_slot, work_request
from .omegaa_kec1_shift import reject_unsupported, shift_task
from .omegaa_kec1_types import KEC1IntegrityCodeV1, KEC1LocusV1, KEC1OriginV1
from .omegaa_kpt1_types import KPT1_FIELD_KINDS, KernelProofTermV1, KernelTermTagV1, KernelUniverseLevelV1

logger = logging.getLogger(__name__)
_BINDERS = frozenset((KernelTermTagV1.PI, KernelTermTagV1.LAM, KernelTermTagV1.SIGMA, KernelTermTagV1.LET))


def _single(factory: WorkFactory, where: KEC1LocusV1) -> WorkGenerator[object]:
    """Schedule one delayed child through the explicit LIFO machine."""
    logger.debug("_single entry")

    def allocate() -> tuple[WorkFactory, ...]:
        logger.debug("_single allocate")
        return (factory,)

    result = cast(tuple[object, ...], (yield work_request(1, where, allocate)))[0]
    logger.debug("_single exit")
    return result


def substitute_task(
    index: int,
    substitute: KernelProofTermV1,
    root: KernelProofTermV1,
    builder: Builder,
    origin: KEC1OriginV1,
    refusal_root: KEC1LocusV1,
    path: tuple[int, ...] = (),
) -> WorkGenerator[KernelProofTermV1]:
    """Return fresh ``subst(index,substitute,root)`` without Python recursion."""
    logger.debug("substitute_task entry index=%d path=%s", index, path)
    if type(index) is not int or index < 0:
        logger.error("substitute_task error invalid-index")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    tag, raw = term_slot(root)
    if type(tag) is not KernelTermTagV1 or type(raw) is not tuple:
        logger.error("substitute_task error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    here = locus(origin, path, 4)
    reject_unsupported(tag, refusal_root if not path else here)
    if tag is KernelTermTagV1.VAR:
        value = cast(int, raw[0])
        if value < index:
            encoded = value.to_bytes(nat_bytes(value), "big")
            result = builder.nat_term(encoded, here)
        elif value == index:
            result = cast(
                KernelProofTermV1,
                (
                    yield from _single(
                        lambda: clone_term_task(substitute, builder, origin, path),
                        here,
                    )
                ),
            )
        else:
            encoded = nat_pred_bytes(value)
            result = builder.nat_term(encoded, here)
        logger.debug("substitute_task exit var path=%s", path)
        return result

    built: list[object] = []
    ordinal = 0
    for position, (kind, value) in enumerate(zip(KPT1_FIELD_KINDS[tag], raw, strict=True)):
        if kind == "term":
            child_path = path + (ordinal,)
            ordinal += 1
            child_index = index
            child_substitute = substitute
            if tag in _BINDERS and position == len(raw) - 1:
                shift_origin = builder.engine.begin()
                shifted = yield from _single(
                    lambda value=substitute, shift_origin=shift_origin: shift_task(  # type: ignore[misc]
                        0, 1, value, builder, shift_origin, refusal_root
                    ),
                    here,
                )
                child_index += 1
                child_substitute = cast(KernelProofTermV1, shifted)
            child = yield from _single(
                lambda value=value, child_index=child_index, child_substitute=child_substitute, child_path=child_path: (  # type: ignore[misc]
                    substitute_task(
                        child_index,
                        child_substitute,
                        cast(KernelProofTermV1, value),
                        builder,
                        origin,
                        refusal_root,
                        child_path,
                    )
                ),
                here,
            )
            built.append(cast(KernelProofTermV1, child))
        elif kind == "level":
            child_path = path + (ordinal,)
            ordinal += 1
            child = yield from _single(
                lambda value=value, child_path=child_path: clone_level_task(  # type: ignore[misc]
                    cast(KernelUniverseLevelV1, value), builder, origin, child_path
                ),
                here,
            )
            built.append(cast(KernelUniverseLevelV1, child))
        elif kind == "terms":
            items: list[KernelProofTermV1] = []
            for item in cast(tuple[KernelProofTermV1, ...], value):
                child_path = path + (ordinal,)
                ordinal += 1
                child = yield from _single(
                    lambda item=item, child_path=child_path: substitute_task(  # type: ignore[misc]
                        index, substitute, item, builder, origin, refusal_root, child_path
                    ),
                    here,
                )
                items.append(cast(KernelProofTermV1, child))
            built.append(tuple(items))
        else:
            built.append(value)
    result = builder.term(tag, tuple(built), here)
    logger.debug("substitute_task exit path=%s", path)
    return result


def subst0_task(
    body: KernelProofTermV1,
    value: KernelProofTermV1,
    builder: Builder,
    origin: KEC1OriginV1,
    where: KEC1LocusV1,
    path: tuple[int, ...] = (),
) -> WorkGenerator[KernelProofTermV1]:
    """Exact fresh top-level substitution task."""
    logger.debug("subst0_task entry path=%s", path)
    result = yield from substitute_task(0, value, body, builder, origin, where, path)
    logger.debug("subst0_task exit path=%s", path)
    return result
