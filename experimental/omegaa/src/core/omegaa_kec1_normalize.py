"""Explicit-LIFO beta-zero reduction, WHNF and NF for KEC1."""

from __future__ import annotations

import logging
from typing import cast

from .omegaa_kec1_builder import Builder, clone_level_task, clone_term_task
from .omegaa_kec1_common import WorkFactory, WorkGenerator, _Integrity, locus, term_slot, work_request
from .omegaa_kec1_context import PreparedInputs
from .omegaa_kec1_shift import reject_unsupported
from .omegaa_kec1_substitute import subst0_task
from .omegaa_kec1_types import KEC1IntegrityCodeV1, KEC1LocusV1
from .omegaa_kpt1_types import KPT1_FIELD_KINDS, KernelProofTermV1, KernelTermTagV1, KernelUniverseLevelV1

logger = logging.getLogger(__name__)


def _where(prepared: PreparedInputs, builder: Builder, node: KernelProofTermV1) -> KEC1LocusV1:
    logger.debug("_where entry")
    result = prepared.loci.get(id(node), builder.loci.get(id(node)))
    if type(result) is not KEC1LocusV1:
        logger.error("_where error missing-locus")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    logger.debug("_where exit path=%s", result.path)
    return result


def _single(factory: WorkFactory, where: KEC1LocusV1) -> WorkGenerator[object]:
    logger.debug("_single entry")

    def allocate() -> tuple[WorkFactory, ...]:
        logger.debug("_single allocate")
        return (factory,)

    result = cast(tuple[object, ...], (yield work_request(1, where, allocate)))[0]
    logger.debug("_single exit")
    return result


def _children(tag: KernelTermTagV1, raw: tuple[object, ...]) -> list[KernelProofTermV1]:
    logger.debug("_children entry tag=%s", tag.name)
    result: list[KernelProofTermV1] = []
    for kind, value in zip(KPT1_FIELD_KINDS[tag], raw, strict=True):
        if kind == "term":
            result.append(cast(KernelProofTermV1, value))
        elif kind == "terms":
            result.extend(cast(tuple[KernelProofTermV1, ...], value))
    logger.debug("_children exit count=%d", len(result))
    return result


def rebuild_direct_task(
    root: KernelProofTermV1,
    target: KernelProofTermV1,
    replacement: KernelProofTermV1,
    builder: Builder,
) -> WorkGenerator[KernelProofTermV1]:
    """Rebuild one parent by an exact direct-child replacement batch."""
    logger.debug("rebuild_direct_task entry")
    tag, raw = term_slot(root)
    if type(tag) is not KernelTermTagV1 or type(raw) is not tuple:
        logger.error("rebuild_direct_task error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    origin = builder.engine.begin()
    specs: list[tuple[str, object, tuple[int, ...], bool]] = []
    ordinal = 0
    matches = 0
    for kind, value in zip(KPT1_FIELD_KINDS[tag], raw, strict=True):
        if kind in {"term", "level"}:
            matched = kind == "term" and value is target
            matches += int(matched)
            specs.append((kind, replacement if matched else value, (ordinal,), matched))
            ordinal += 1
        elif kind == "terms":
            for item in cast(tuple[KernelProofTermV1, ...], value):
                matched = item is target
                matches += int(matched)
                specs.append(("term", replacement if matched else item, (ordinal,), matched))
                ordinal += 1
    if matches != 1:
        logger.error("rebuild_direct_task error target-count=%d", matches)
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    here = locus(origin, (), 4)

    def allocate() -> tuple[WorkFactory, ...]:
        logger.debug("rebuild_direct_task allocate children=%d", len(specs))
        factories: list[WorkFactory] = []
        for kind, child, path, _matched in specs:
            if kind == "term":
                factories.append(
                    lambda child=child, path=path: clone_term_task(  # type: ignore[misc]
                        cast(KernelProofTermV1, child), builder, origin, path
                    )
                )
            else:
                factories.append(
                    lambda child=child, path=path: clone_level_task(  # type: ignore[misc]
                        cast(KernelUniverseLevelV1, child), builder, origin, path
                    )
                )
        return tuple(factories)

    if specs:
        children = cast(tuple[object, ...], (yield work_request(len(specs), here, allocate)))
    else:
        logger.error("rebuild_direct_task error childless")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
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
    logger.debug("rebuild_direct_task exit")
    return result


def root_redex_task(
    node: KernelProofTermV1,
    prepared: PreparedInputs,
    builder: Builder,
) -> WorkGenerator[KernelProofTermV1 | None]:
    """Contract exactly one root redex after step gating."""
    logger.debug("root_redex_task entry")
    tag, raw = term_slot(node)
    if type(tag) is not KernelTermTagV1 or type(raw) is not tuple:
        logger.error("root_redex_task error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    where = _where(prepared, builder, node)
    reject_unsupported(tag, where)
    if tag is KernelTermTagV1.APP:
        function, argument = cast(tuple[KernelProofTermV1, KernelProofTermV1], raw)
        ftag, fraw = term_slot(function)
        if type(ftag) is not KernelTermTagV1 or type(fraw) is not tuple:
            logger.error("root_redex_task error function-shape")
            raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
        if ftag is KernelTermTagV1.LAM:
            builder.engine.contraction(where)
            origin = builder.engine.begin()
            result = yield from _single(
                lambda: subst0_task(cast(KernelProofTermV1, fraw[1]), argument, builder, origin, where),
                where,
            )
            logger.debug("root_redex_task exit beta")
            return cast(KernelProofTermV1, result)
    elif tag is KernelTermTagV1.LET:
        builder.engine.contraction(where)
        origin = builder.engine.begin()
        result = yield from _single(
            lambda: subst0_task(
                cast(KernelProofTermV1, raw[2]), cast(KernelProofTermV1, raw[1]), builder, origin, where
            ),
            where,
        )
        logger.debug("root_redex_task exit zeta")
        return cast(KernelProofTermV1, result)
    elif tag in (KernelTermTagV1.FST, KernelTermTagV1.SND):
        pair = cast(KernelProofTermV1, raw[0])
        ptag, praw = term_slot(pair)
        if type(ptag) is not KernelTermTagV1 or type(praw) is not tuple:
            logger.error("root_redex_task error pair-shape")
            raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
        if ptag is KernelTermTagV1.PAIR:
            builder.engine.contraction(where)
            chosen = cast(KernelProofTermV1, praw[0 if tag is KernelTermTagV1.FST else 1])
            origin = builder.engine.begin()
            result = yield from _single(lambda: clone_term_task(chosen, builder, origin), where)
            logger.debug("root_redex_task exit projection")
            return cast(KernelProofTermV1, result)
    logger.debug("root_redex_task exit none")
    return None


def reduce_one_task(
    node: KernelProofTermV1, prepared: PreparedInputs, builder: Builder
) -> WorkGenerator[tuple[bool, KernelProofTermV1]]:
    """Contract first root/preorder redex using only explicit work frames."""
    logger.debug("reduce_one_task entry")
    where = _where(prepared, builder, node)
    root = yield from _single(lambda: root_redex_task(node, prepared, builder), where)
    if root is not None:
        logger.debug("reduce_one_task exit root")
        return True, cast(KernelProofTermV1, root)
    tag, raw = term_slot(node)
    if type(tag) is not KernelTermTagV1 or type(raw) is not tuple:
        logger.error("reduce_one_task error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    for child in _children(tag, raw):
        outcome = cast(
            tuple[bool, KernelProofTermV1],
            (yield from _single(lambda child=child: reduce_one_task(child, prepared, builder), where)),  # type: ignore[misc]
        )
        changed, candidate = outcome
        if changed:
            rebuilt = yield from _single(
                lambda child=child, candidate=candidate: rebuild_direct_task(  # type: ignore[misc]
                    node, child, candidate, builder
                ),
                where,
            )
            logger.debug("reduce_one_task exit child")
            return True, cast(KernelProofTermV1, rebuilt)
    logger.debug("reduce_one_task exit normal")
    return False, node


def whnf_task(node: KernelProofTermV1, prepared: PreparedInputs, builder: Builder) -> WorkGenerator[KernelProofTermV1]:
    """Normalize only H using explicit root/head/rebuild work frames."""
    logger.debug("whnf_task entry")
    current = node
    while True:
        where = _where(prepared, builder, current)
        redex = yield from _single(
            lambda current=current: root_redex_task(current, prepared, builder),  # type: ignore[misc]
            where,
        )
        if redex is not None:
            current = cast(KernelProofTermV1, redex)
            logger.debug("whnf_task state contracted")
            continue
        tag, raw = term_slot(current)
        if type(tag) is not KernelTermTagV1 or type(raw) is not tuple:
            logger.error("whnf_task error shape")
            raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
        if tag not in (KernelTermTagV1.APP, KernelTermTagV1.FST, KernelTermTagV1.SND):
            logger.debug("whnf_task exit neutral")
            return current
        head = cast(KernelProofTermV1, raw[0])
        normalized = cast(
            KernelProofTermV1,
            (yield from _single(lambda: whnf_task(head, prepared, builder), where)),
        )
        if normalized is head:
            logger.debug("whnf_task exit neutral-head")
            return current
        current = cast(
            KernelProofTermV1,
            (yield from _single(lambda: rebuild_direct_task(current, head, normalized, builder), where)),
        )
        logger.debug("whnf_task state rebuilt-head")


def nf_task(node: KernelProofTermV1, prepared: PreparedInputs, builder: Builder) -> WorkGenerator[KernelProofTermV1]:
    """Repeat explicit ReduceOne until no redex remains."""
    logger.debug("nf_task entry")
    current = node
    while True:
        where = _where(prepared, builder, current)
        changed, candidate = cast(
            tuple[bool, KernelProofTermV1],
            (yield from _single(lambda current=current: reduce_one_task(current, prepared, builder), where)),  # type: ignore[misc]
        )
        if not changed:
            logger.debug("nf_task exit steps=%d", builder.engine.steps)
            return current
        current = candidate
        logger.debug("nf_task state reduced")
