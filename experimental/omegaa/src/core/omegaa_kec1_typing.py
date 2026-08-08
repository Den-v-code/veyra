"""Exact public KEC1 bidirectional judgments on an explicit LIFO machine."""

from __future__ import annotations

from hashlib import sha256
import logging
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Callable, cast
import unicodedata

from . import omegaa_kec1_builder as _builder_module
from . import omegaa_kec1_common as _common_module
from . import omegaa_kec1_context as _context_module
from . import omegaa_kec1_normalize as _normalize_module
from . import omegaa_kec1_shift as _shift_module
from . import omegaa_kec1_substitute as _substitute_module
from . import omegaa_kec1_types as _types_module
from .omegaa_kcc1_codec import kcc1_empty_config_id_v1, kcc1_source_root_v1
from .omegaa_kec1_builder import Builder, clone_term_task
from .omegaa_kec1_common import (
    Engine,
    Metrics,
    WorkFactory,
    WorkGenerator,
    WorkMachine,
    _Abort,
    _Integrity,
    _Resource,
    abort_result,
    encode_exact,
    locus,
    origin_v1,
    refuse,
    result_v1,
    term_slot,
    validate_integrity,
    work_request,
)
from .omegaa_kec1_context import PreparedInputs, prepare_inputs
from .omegaa_kec1_normalize import nf_task, reduce_one_task, whnf_task
from .omegaa_kec1_shift import quote_level_task, reject_unsupported, shift_task
from .omegaa_kec1_substitute import subst0_task
from .omegaa_kec1_types import (
    ContextV1,
    DEFAULT_KEC1_LIMITS_V1,
    KEC1ApiV1,
    KEC1_EQUATION_BYTES_V1,
    KEC1IntegrityCodeV1,
    KEC1LimitsV1,
    KEC1LocusV1,
    KEC1OriginTagV1,
    KEC1RefusalCodeV1,
    KEC1ResourceKindV1,
    KEC1ResultTagV1,
    KEC1ResultV1,
)
from .omegaa_kpt1_types import (
    KernelLevelTagV1,
    KernelProofTermV1,
    KernelTermTagV1,
    KernelUniverseLevelV1,
)

logger = logging.getLogger(__name__)
_KPT_SOURCE_ROOT = bytes.fromhex("55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a")
KEC1_SOURCE_PATHS_V1 = (
    "src/core/omegaa_kec1_builder.py",
    "src/core/omegaa_kec1_common.py",
    "src/core/omegaa_kec1_context.py",
    "src/core/omegaa_kec1_normalize.py",
    "src/core/omegaa_kec1_shift.py",
    "src/core/omegaa_kec1_substitute.py",
    "src/core/omegaa_kec1_types.py",
    "src/core/omegaa_kec1_typing.py",
)
_REPOSITORY_ROOT = Path(__file__).parents[2]
_SOURCE_PATHS_CAPTURE = KEC1_SOURCE_PATHS_V1
_REPOSITORY_ROOT_CAPTURE = _REPOSITORY_ROOT
_KPT_SOURCE_ROOT_CAPTURE = _KPT_SOURCE_ROOT
_EQUATION_BYTES_CAPTURE = KEC1_EQUATION_BYTES_V1
_OS_OPEN = os.open
_OS_CLOSE = os.close
_OS_READ = os.read
_OS_FSTAT = os.fstat
_STAT_ISREG = stat.S_ISREG


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


def _tag_fields(node: KernelProofTermV1) -> tuple[KernelTermTagV1, tuple[object, ...]]:
    logger.debug("_tag_fields entry")
    tag, raw = term_slot(node)
    if type(tag) is not KernelTermTagV1 or type(raw) is not tuple:
        logger.error("_tag_fields error shape")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    logger.debug("_tag_fields exit tag=%s", tag.name)
    return tag, raw


def _expect_sort(node: KernelProofTermV1, subject: KEC1LocusV1) -> KernelUniverseLevelV1:
    logger.debug("_expect_sort entry")
    tag, raw = _tag_fields(node)
    if tag is not KernelTermTagV1.SORT:
        logger.info("_expect_sort refusal")
        refuse(KEC1RefusalCodeV1.EXPECTED_SORT, subject)
    result = cast(KernelUniverseLevelV1, raw[0])
    logger.debug("_expect_sort exit")
    return result


def _build_sort_succ_task(level: KernelUniverseLevelV1, builder: Builder) -> WorkGenerator[KernelProofTermV1]:
    logger.debug("_build_sort_succ_task entry")
    origin = builder.engine.begin()
    root = locus(origin)
    quoted = cast(
        KernelUniverseLevelV1,
        (yield from _single(lambda: quote_level_task(level, builder, origin, (0, 0)), root)),
    )
    successor = builder.level(KernelLevelTagV1.SUCC, (quoted,), locus(origin, (0,), 0))
    result = builder.term(KernelTermTagV1.SORT, (successor,), root)
    logger.debug("_build_sort_succ_task exit")
    return result


def _build_sort_max_task(
    left: KernelUniverseLevelV1, right: KernelUniverseLevelV1, builder: Builder
) -> WorkGenerator[KernelProofTermV1]:
    logger.debug("_build_sort_max_task entry")
    origin = builder.engine.begin()
    root = locus(origin)

    def allocate() -> tuple[WorkFactory, ...]:
        logger.debug("_build_sort_max_task allocate")
        return (
            lambda: quote_level_task(left, builder, origin, (0, 0)),
            lambda: quote_level_task(right, builder, origin, (0, 1)),
        )

    qleft, qright = cast(
        tuple[KernelUniverseLevelV1, KernelUniverseLevelV1],
        (yield work_request(2, root, allocate)),
    )
    maximum = builder.level(KernelLevelTagV1.MAX, (qleft, qright), locus(origin, (0,), 0))
    result = builder.term(KernelTermTagV1.SORT, (maximum,), root)
    logger.debug("_build_sort_max_task exit")
    return result


def _build_sort_zero(builder: Builder) -> KernelProofTermV1:
    logger.debug("_build_sort_zero entry")
    origin = builder.engine.begin()
    root = locus(origin)
    zero = builder.level(KernelLevelTagV1.ZERO, (), locus(origin, (0,), 0))
    result = builder.term(KernelTermTagV1.SORT, (zero,), root)
    logger.debug("_build_sort_zero exit")
    return result


def _build_term_task(
    tag: KernelTermTagV1, sources: tuple[KernelProofTermV1, ...], builder: Builder
) -> WorkGenerator[KernelProofTermV1]:
    logger.debug("_build_term_task entry tag=%s", tag.name)
    origin = builder.engine.begin()
    root = locus(origin)

    def allocate() -> tuple[WorkFactory, ...]:
        logger.debug("_build_term_task allocate count=%d", len(sources))
        return tuple(
            lambda source=source, path=(index,): clone_term_task(source, builder, origin, path)
            for index, source in enumerate(sources)
        )

    copies = cast(tuple[KernelProofTermV1, ...], (yield work_request(len(sources), root, allocate))) if sources else ()
    result = builder.term(tag, cast(tuple[object, ...], copies), root)
    logger.debug("_build_term_task exit tag=%s", tag.name)
    return result


def _infer_task(
    context: ContextV1, term: KernelProofTermV1, prepared: PreparedInputs, builder: Builder
) -> WorkGenerator[KernelProofTermV1]:
    logger.debug("_infer_task entry context=%d", len(context))
    where = _where(prepared, builder, term)
    tag, raw = _tag_fields(term)
    reject_unsupported(tag, where)
    if tag is KernelTermTagV1.VAR:
        index = cast(int, raw[0])
        if index >= len(context):
            logger.info("_infer_task refusal unscoped")
            refuse(KEC1RefusalCodeV1.UNSCOPED, where)
        origin = builder.engine.begin()
        result = yield from _single(lambda: shift_task(0, index + 1, context[index], builder, origin, where), where)
        logger.debug("_infer_task exit var")
        return cast(KernelProofTermV1, result)
    if tag is KernelTermTagV1.SORT:
        result = yield from _single(lambda: _build_sort_succ_task(cast(KernelUniverseLevelV1, raw[0]), builder), where)
        logger.debug("_infer_task exit sort")
        return cast(KernelProofTermV1, result)
    if tag in (KernelTermTagV1.PI, KernelTermTagV1.SIGMA):
        domain, body = cast(tuple[KernelProofTermV1, KernelProofTermV1], raw)
        domain_inferred = yield from _single(lambda: _infer_task(context, domain, prepared, builder), where)
        domain_type = yield from _single(
            lambda: whnf_task(cast(KernelProofTermV1, domain_inferred), prepared, builder), where
        )
        u = _expect_sort(cast(KernelProofTermV1, domain_type), _where(prepared, builder, domain))
        body_inferred = yield from _single(lambda: _infer_task((domain,) + context, body, prepared, builder), where)
        body_type = yield from _single(
            lambda: whnf_task(cast(KernelProofTermV1, body_inferred), prepared, builder), where
        )
        v = _expect_sort(cast(KernelProofTermV1, body_type), _where(prepared, builder, body))
        result = yield from _single(lambda: _build_sort_max_task(u, v, builder), where)
        logger.debug("_infer_task exit binder")
        return cast(KernelProofTermV1, result)
    if tag is KernelTermTagV1.LAM:
        annotation, body = cast(tuple[KernelProofTermV1, KernelProofTermV1], raw)
        annotation_inferred = yield from _single(lambda: _infer_task(context, annotation, prepared, builder), where)
        annotation_type = yield from _single(
            lambda: whnf_task(cast(KernelProofTermV1, annotation_inferred), prepared, builder), where
        )
        _expect_sort(cast(KernelProofTermV1, annotation_type), _where(prepared, builder, annotation))
        body_type = yield from _single(lambda: _infer_task((annotation,) + context, body, prepared, builder), where)
        result = yield from _single(
            lambda: _build_term_task(KernelTermTagV1.PI, (annotation, cast(KernelProofTermV1, body_type)), builder),
            where,
        )
        logger.debug("_infer_task exit lam")
        return cast(KernelProofTermV1, result)
    if tag is KernelTermTagV1.APP:
        function, argument = cast(tuple[KernelProofTermV1, KernelProofTermV1], raw)
        inferred = yield from _single(lambda: _infer_task(context, function, prepared, builder), where)
        function_type = yield from _single(
            lambda: whnf_task(cast(KernelProofTermV1, inferred), prepared, builder), where
        )
        ftag, fraw = _tag_fields(cast(KernelProofTermV1, function_type))
        if ftag is not KernelTermTagV1.PI:
            logger.info("_infer_task refusal expected-pi")
            refuse(KEC1RefusalCodeV1.EXPECTED_PI, where)
        domain, body = cast(tuple[KernelProofTermV1, KernelProofTermV1], fraw)
        yield from _single(lambda: _check_task(context, argument, domain, prepared, builder), where)
        origin = builder.engine.begin()
        result = yield from _single(lambda: subst0_task(body, argument, builder, origin, where), where)
        logger.debug("_infer_task exit app")
        return cast(KernelProofTermV1, result)
    if tag in (KernelTermTagV1.FST, KernelTermTagV1.SND):
        pair = cast(KernelProofTermV1, raw[0])
        inferred = yield from _single(lambda: _infer_task(context, pair, prepared, builder), where)
        pair_type = yield from _single(lambda: whnf_task(cast(KernelProofTermV1, inferred), prepared, builder), where)
        ptag, praw = _tag_fields(cast(KernelProofTermV1, pair_type))
        if ptag is not KernelTermTagV1.SIGMA:
            logger.info("_infer_task refusal expected-sigma")
            refuse(KEC1RefusalCodeV1.EXPECTED_SIGMA, where)
        domain, body = cast(tuple[KernelProofTermV1, KernelProofTermV1], praw)
        if tag is KernelTermTagV1.FST:
            origin = builder.engine.begin()
            result = yield from _single(lambda: clone_term_task(domain, builder, origin), where)
            logger.debug("_infer_task exit fst")
            return cast(KernelProofTermV1, result)
        fst = yield from _single(lambda: _build_term_task(KernelTermTagV1.FST, (pair,), builder), where)
        origin = builder.engine.begin()
        result = yield from _single(
            lambda: subst0_task(body, cast(KernelProofTermV1, fst), builder, origin, where), where
        )
        logger.debug("_infer_task exit snd")
        return cast(KernelProofTermV1, result)
    if tag is KernelTermTagV1.LET:
        annotation, value, body = cast(tuple[KernelProofTermV1, KernelProofTermV1, KernelProofTermV1], raw)
        inferred = yield from _single(lambda: _infer_task(context, annotation, prepared, builder), where)
        annotation_type = yield from _single(
            lambda: whnf_task(cast(KernelProofTermV1, inferred), prepared, builder), where
        )
        _expect_sort(cast(KernelProofTermV1, annotation_type), _where(prepared, builder, annotation))
        yield from _single(lambda: _check_task(context, value, annotation, prepared, builder), where)
        body_type = yield from _single(lambda: _infer_task((annotation,) + context, body, prepared, builder), where)
        origin = builder.engine.begin()
        result = yield from _single(
            lambda: subst0_task(cast(KernelProofTermV1, body_type), value, builder, origin, where), where
        )
        logger.debug("_infer_task exit let")
        return cast(KernelProofTermV1, result)
    if tag is KernelTermTagV1.EQ:
        annotation, left, right = cast(tuple[KernelProofTermV1, KernelProofTermV1, KernelProofTermV1], raw)
        inferred = yield from _single(lambda: _infer_task(context, annotation, prepared, builder), where)
        annotation_type = yield from _single(
            lambda: whnf_task(cast(KernelProofTermV1, inferred), prepared, builder), where
        )
        _expect_sort(cast(KernelProofTermV1, annotation_type), _where(prepared, builder, annotation))
        yield from _single(lambda: _check_task(context, left, annotation, prepared, builder), where)
        yield from _single(lambda: _check_task(context, right, annotation, prepared, builder), where)
        result = _build_sort_zero(builder)
        logger.debug("_infer_task exit eq")
        return result
    if tag is KernelTermTagV1.REFL:
        witness = cast(KernelProofTermV1, raw[0])
        inferred = yield from _single(lambda: _infer_task(context, witness, prepared, builder), where)
        result = yield from _single(
            lambda: _build_term_task(
                KernelTermTagV1.EQ,
                (cast(KernelProofTermV1, inferred), witness, witness),
                builder,
            ),
            where,
        )
        logger.debug("_infer_task exit refl")
        return cast(KernelProofTermV1, result)
    logger.info("_infer_task refusal cannot-infer")
    refuse(KEC1RefusalCodeV1.CANNOT_INFER, where)


def _defeq_task(
    left: KernelProofTermV1,
    right: KernelProofTermV1,
    prepared: PreparedInputs,
    builder: Builder,
) -> WorkGenerator[bool]:
    logger.debug("_defeq_task entry")
    where = _where(prepared, builder, left)
    left_nf = yield from _single(lambda: nf_task(left, prepared, builder), where)
    right_nf = yield from _single(lambda: nf_task(right, prepared, builder), where)
    result = encode_exact(cast(KernelProofTermV1, left_nf), builder.engine.values, "generated") == encode_exact(
        cast(KernelProofTermV1, right_nf), builder.engine.values, "generated"
    )
    logger.debug("_defeq_task exit equal=%s", result)
    return result


def _check_task(
    context: ContextV1,
    term: KernelProofTermV1,
    expected: KernelProofTermV1,
    prepared: PreparedInputs,
    builder: Builder,
) -> WorkGenerator[None]:
    logger.debug("_check_task entry context=%d", len(context))
    where = _where(prepared, builder, term)
    inferred_expected = yield from _single(lambda: _infer_task(context, expected, prepared, builder), where)
    expected_type = yield from _single(
        lambda: whnf_task(cast(KernelProofTermV1, inferred_expected), prepared, builder), where
    )
    _expect_sort(cast(KernelProofTermV1, expected_type), _where(prepared, builder, expected))
    normalized_expected = yield from _single(lambda: whnf_task(expected, prepared, builder), where)
    tag, raw = _tag_fields(term)
    reject_unsupported(tag, where)
    etag, eraw = _tag_fields(cast(KernelProofTermV1, normalized_expected))
    if tag is KernelTermTagV1.LAM:
        if etag is not KernelTermTagV1.PI:
            logger.info("_check_task refusal expected-pi")
            refuse(KEC1RefusalCodeV1.EXPECTED_PI, where)
        annotation, body = cast(tuple[KernelProofTermV1, KernelProofTermV1], raw)
        domain, codomain = cast(tuple[KernelProofTermV1, KernelProofTermV1], eraw)
        inferred = yield from _single(lambda: _infer_task(context, annotation, prepared, builder), where)
        annotation_type = yield from _single(
            lambda: whnf_task(cast(KernelProofTermV1, inferred), prepared, builder), where
        )
        _expect_sort(cast(KernelProofTermV1, annotation_type), _where(prepared, builder, annotation))
        equal = yield from _single(lambda: _defeq_task(annotation, domain, prepared, builder), where)
        if not equal:
            logger.info("_check_task refusal mismatch-lam")
            refuse(KEC1RefusalCodeV1.TYPE_MISMATCH, where)
        yield from _single(lambda: _check_task((annotation,) + context, body, codomain, prepared, builder), where)
        logger.debug("_check_task exit lam")
        return None
    if tag is KernelTermTagV1.PAIR:
        if etag is not KernelTermTagV1.SIGMA:
            logger.info("_check_task refusal expected-sigma")
            refuse(KEC1RefusalCodeV1.EXPECTED_SIGMA, where)
        first, second = cast(tuple[KernelProofTermV1, KernelProofTermV1], raw)
        domain, body = cast(tuple[KernelProofTermV1, KernelProofTermV1], eraw)
        yield from _single(lambda: _check_task(context, first, domain, prepared, builder), where)
        origin = builder.engine.begin()
        second_type = yield from _single(lambda: subst0_task(body, first, builder, origin, where), where)
        yield from _single(
            lambda: _check_task(context, second, cast(KernelProofTermV1, second_type), prepared, builder), where
        )
        logger.debug("_check_task exit pair")
        return None
    inferred = yield from _single(lambda: _infer_task(context, term, prepared, builder), where)
    equal = yield from _single(
        lambda: _defeq_task(cast(KernelProofTermV1, inferred), expected, prepared, builder), where
    )
    if not equal:
        logger.info("_check_task refusal mismatch")
        refuse(KEC1RefusalCodeV1.TYPE_MISMATCH, where)
    logger.debug("_check_task exit generic")
    return None


def _wf_item_task(context: ContextV1, index: int, prepared: PreparedInputs, builder: Builder) -> WorkGenerator[None]:
    """Validate one context row under its exact outer suffix."""
    logger.debug("_wf_item_task entry index=%d", index)
    subject = context[index]
    where = _where(prepared, builder, subject)
    inferred = yield from _single(lambda: _infer_task(context[index + 1 :], subject, prepared, builder), where)
    normalized = yield from _single(lambda: whnf_task(cast(KernelProofTermV1, inferred), prepared, builder), where)
    _expect_sort(cast(KernelProofTermV1, normalized), where)
    logger.debug("_wf_item_task exit index=%d", index)
    return None


def _wf_task(context: ContextV1, prepared: PreparedInputs, builder: Builder) -> WorkGenerator[None]:
    """Schedule all stored rows outermost-first as one reversed LIFO batch."""
    logger.debug("_wf_task entry context=%d", len(context))
    if context:
        order = tuple(range(len(context) - 1, -1, -1))
        where = _where(prepared, builder, context[order[0]])

        def allocate() -> tuple[WorkFactory, ...]:
            logger.debug("_wf_task allocate rows=%d", len(order))
            return tuple(
                lambda index=index: _wf_item_task(context, index, prepared, builder)
                for index in order
            )

        yield work_request(len(order), where, allocate)
    logger.debug("_wf_task exit")
    return None


def _output_task(
    api: KEC1ApiV1,
    tag: KEC1ResultTagV1,
    candidate: KernelProofTermV1,
    prepared: PreparedInputs,
    builder: Builder,
) -> WorkGenerator[KEC1ResultV1]:
    logger.debug("_output_task entry api=%s", api.name)
    metric = builder.metrics.get(id(candidate), prepared.metrics.get(id(candidate)))
    if type(metric) is not Metrics:
        logger.error("_output_task error candidate-metric")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    origin = builder.engine.begin()
    fresh = cast(
        KernelProofTermV1,
        (yield from _single(lambda: clone_term_task(candidate, builder, origin), locus(origin))),
    )
    fresh_metric = builder.metrics.get(id(fresh))
    if type(fresh_metric) is not Metrics or fresh_metric != metric:
        logger.error("_output_task error metric-drift")
        raise _Integrity(KEC1IntegrityCodeV1.MAPPING_DRIFT)
    output_origin = origin_v1(KEC1OriginTagV1.OUTPUT)
    where = locus(output_origin)
    checks = (
        (KEC1ResourceKindV1.OUTPUT_DEPTH, builder.engine.values[12], metric.depth),
        (KEC1ResourceKindV1.OUTPUT_NODES, builder.engine.values[13], metric.nodes),
        (KEC1ResourceKindV1.OUTPUT_BYTES, builder.engine.values[14], metric.wire_bytes),
        (KEC1ResourceKindV1.OUTPUT_LIST_ITEMS, builder.engine.values[15], metric.list_items),
        (KEC1ResourceKindV1.OUTPUT_NAT_BYTES, builder.engine.values[16], metric.nat_bytes),
    )
    for kind, allowed, current in checks:
        if current > allowed:
            logger.error("_output_task resource kind=%s", kind.name)
            raise _Resource(kind, allowed, current, where)
    encoded = encode_exact(fresh, builder.engine.values, "output")
    if len(encoded) != metric.wire_bytes:
        logger.error("_output_task error mapping")
        raise _Integrity(KEC1IntegrityCodeV1.MAPPING_DRIFT)
    result = result_v1(api, tag, fresh)
    logger.debug("_output_task exit api=%s", api.name)
    return result


def _checked_task(api: KEC1ApiV1) -> WorkGenerator[KEC1ResultV1]:
    logger.debug("_checked_task entry api=%s", api.name)
    if False:
        yield work_request(1, locus(origin_v1(KEC1OriginTagV1.OUTPUT)), lambda: ())
    result = result_v1(api, KEC1ResultTagV1.CHECKED, None)
    logger.debug("_checked_task exit api=%s", api.name)
    return result


def _public_infer_task(prepared: PreparedInputs, builder: Builder) -> WorkGenerator[KEC1ResultV1]:
    logger.debug("_public_infer_task entry")
    yield from _single(lambda: _wf_task(prepared.context, prepared, builder), _where(prepared, builder, prepared.term))
    candidate = yield from _single(
        lambda: _infer_task(prepared.context, prepared.term, prepared, builder),
        _where(prepared, builder, prepared.term),
    )
    result = yield from _single(
        lambda: _output_task(
            KEC1ApiV1.INFER, KEC1ResultTagV1.INFERRED, cast(KernelProofTermV1, candidate), prepared, builder
        ),
        _where(prepared, builder, prepared.term),
    )
    logger.debug("_public_infer_task exit")
    return cast(KEC1ResultV1, result)


def _public_check_task(prepared: PreparedInputs, builder: Builder) -> WorkGenerator[KEC1ResultV1]:
    logger.debug("_public_check_task entry")
    where = _where(prepared, builder, prepared.term)
    yield from _single(lambda: _wf_task(prepared.context, prepared, builder), where)
    yield from _single(
        lambda: _check_task(
            prepared.context, prepared.term, cast(KernelProofTermV1, prepared.expected), prepared, builder
        ),
        where,
    )
    result = yield from _single(lambda: _checked_task(KEC1ApiV1.CHECK), where)
    logger.debug("_public_check_task exit")
    return cast(KEC1ResultV1, result)


def _public_reduce_task(prepared: PreparedInputs, builder: Builder) -> WorkGenerator[KEC1ResultV1]:
    logger.debug("_public_reduce_task entry")
    where = _where(prepared, builder, prepared.term)
    changed, candidate = cast(
        tuple[bool, KernelProofTermV1],
        (yield from _single(lambda: reduce_one_task(prepared.term, prepared, builder), where)),
    )
    result = yield from _single(
        lambda: _output_task(
            KEC1ApiV1.REDUCE_ONE,
            KEC1ResultTagV1.STEP if changed else KEC1ResultTagV1.NORMAL,
            candidate,
            prepared,
            builder,
        ),
        where,
    )
    logger.debug("_public_reduce_task exit")
    return cast(KEC1ResultV1, result)


def _public_whnf_task(prepared: PreparedInputs, builder: Builder) -> WorkGenerator[KEC1ResultV1]:
    logger.debug("_public_whnf_task entry")
    where = _where(prepared, builder, prepared.term)
    candidate = yield from _single(lambda: whnf_task(prepared.term, prepared, builder), where)
    result = yield from _single(
        lambda: _output_task(
            KEC1ApiV1.WHNF, KEC1ResultTagV1.NORMAL, cast(KernelProofTermV1, candidate), prepared, builder
        ),
        where,
    )
    logger.debug("_public_whnf_task exit")
    return cast(KEC1ResultV1, result)


def _public_nf_task(prepared: PreparedInputs, builder: Builder) -> WorkGenerator[KEC1ResultV1]:
    logger.debug("_public_nf_task entry")
    where = _where(prepared, builder, prepared.term)
    candidate = yield from _single(lambda: nf_task(prepared.term, prepared, builder), where)
    result = yield from _single(
        lambda: _output_task(
            KEC1ApiV1.NF, KEC1ResultTagV1.NORMAL, cast(KernelProofTermV1, candidate), prepared, builder
        ),
        where,
    )
    logger.debug("_public_nf_task exit")
    return cast(KEC1ResultV1, result)


def _public_require_task(prepared: PreparedInputs, builder: Builder) -> WorkGenerator[KEC1ResultV1]:
    logger.debug("_public_require_task entry")
    where = _where(prepared, builder, prepared.term)
    normal = cast(
        KernelProofTermV1,
        (yield from _single(lambda: nf_task(prepared.term, prepared, builder), where)),
    )
    left = encode_exact(prepared.term, builder.engine.values, "input")
    right = encode_exact(normal, builder.engine.values, "generated")
    if left != right:
        bound = min(len(left), len(right))
        difference = next((index for index in range(bound) if left[index] != right[index]), bound)
        logger.info("_public_require_task refusal not-normal offset=%d", difference)
        refuse(
            KEC1RefusalCodeV1.NOT_NORMAL,
            locus(origin_v1(KEC1OriginTagV1.TERM), (), difference),
        )
    result = yield from _single(lambda: _checked_task(KEC1ApiV1.REQUIRE_NORMAL), where)
    logger.debug("_public_require_task exit")
    return cast(KEC1ResultV1, result)


_Operation = Callable[[PreparedInputs, Builder], WorkGenerator[KEC1ResultV1]]


def _run(
    api: KEC1ApiV1,
    context: object,
    term: object,
    expected: object,
    limits: object,
    operation: _Operation,
) -> KEC1ResultV1:
    logger.debug("_run entry api=%s", api.name)
    try:
        _validate_all_bindings()
        values = validate_integrity(limits, _PUBLICS)
        prepared = prepare_inputs(api, context, term, expected, values)
        engine = Engine(values)
        builder = Builder(engine)
        machine: WorkMachine[KEC1ResultV1] = WorkMachine(engine)
        result = machine.run(lambda: operation(prepared, builder), prepared.where(prepared.term))
        logger.debug("_run exit api=%s tag=%s", api.name, result.tag.name)
        return result
    except _Abort as exc:
        logger.info("_run abort api=%s", api.name)
        return abort_result(api, exc)
    except MemoryError:
        logger.error("_run memory-error api=%s", api.name)
        raise
    except Exception:
        logger.exception("_run internal-error api=%s", api.name)
        return abort_result(api, _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT))


def InferV1(context: ContextV1, term: KernelProofTermV1, limits: KEC1LimitsV1 = DEFAULT_KEC1_LIMITS_V1) -> KEC1ResultV1:
    logger.debug("InferV1 entry")
    result = _run(KEC1ApiV1.INFER, context, term, None, limits, _public_infer_task)
    logger.debug("InferV1 exit tag=%s", result.tag.name)
    return result


def CheckV1(
    context: ContextV1,
    term: KernelProofTermV1,
    expected: KernelProofTermV1,
    limits: KEC1LimitsV1 = DEFAULT_KEC1_LIMITS_V1,
) -> KEC1ResultV1:
    logger.debug("CheckV1 entry")
    result = _run(KEC1ApiV1.CHECK, context, term, expected, limits, _public_check_task)
    logger.debug("CheckV1 exit tag=%s", result.tag.name)
    return result


def ReduceOneβ0V1(term: KernelProofTermV1, limits: KEC1LimitsV1 = DEFAULT_KEC1_LIMITS_V1) -> KEC1ResultV1:
    logger.debug("ReduceOneβ0V1 entry")
    result = _run(KEC1ApiV1.REDUCE_ONE, (), term, None, limits, _public_reduce_task)
    logger.debug("ReduceOneβ0V1 exit tag=%s", result.tag.name)
    return result


def WHNFβ0V1(term: KernelProofTermV1, limits: KEC1LimitsV1 = DEFAULT_KEC1_LIMITS_V1) -> KEC1ResultV1:
    logger.debug("WHNFβ0V1 entry")
    result = _run(KEC1ApiV1.WHNF, (), term, None, limits, _public_whnf_task)
    logger.debug("WHNFβ0V1 exit tag=%s", result.tag.name)
    return result


def NFβ0V1(term: KernelProofTermV1, limits: KEC1LimitsV1 = DEFAULT_KEC1_LIMITS_V1) -> KEC1ResultV1:
    logger.debug("NFβ0V1 entry")
    result = _run(KEC1ApiV1.NF, (), term, None, limits, _public_nf_task)
    logger.debug("NFβ0V1 exit tag=%s", result.tag.name)
    return result


def RequireNormalβ0V1(term: KernelProofTermV1, limits: KEC1LimitsV1 = DEFAULT_KEC1_LIMITS_V1) -> KEC1ResultV1:
    logger.debug("RequireNormalβ0V1 entry")
    result = _run(KEC1ApiV1.REQUIRE_NORMAL, (), term, None, limits, _public_require_task)
    logger.debug("RequireNormalβ0V1 exit tag=%s", result.tag.name)
    return result


_PUBLICS = (InferV1, CheckV1, ReduceOneβ0V1, WHNFβ0V1, NFβ0V1, RequireNormalβ0V1)
_BINDING_MODULES = (
    _types_module,
    _common_module,
    _builder_module,
    _context_module,
    _shift_module,
    _substitute_module,
    _normalize_module,
)


def _capture_bindings() -> tuple[tuple[object, tuple[tuple[str, object, object | None], ...]], ...]:
    logger.debug("_capture_bindings entry")
    captured: list[tuple[object, tuple[tuple[str, object, object | None], ...]]] = []
    for module in (*_BINDING_MODULES,):
        rows: list[tuple[str, object, object | None]] = []
        for name, value in vars(module).items():
            if name.startswith("__"):
                continue
            code = getattr(value, "__code__", None)
            if (
                callable(value)
                or (module is _types_module and name == "KPT1_MAX_SAFE_DEPTH")
                or (module is not _types_module and name != "logger")
            ):
                rows.append((name, value, code))
        captured.append((module, tuple(rows)))
    logger.debug("_capture_bindings exit modules=%d", len(captured))
    return tuple(captured)


_ALL_BINDINGS: tuple[tuple[object, tuple[tuple[str, object, object | None], ...]], ...] = ()
_CLASS_BINDINGS: tuple[tuple[type[object], tuple[tuple[str, object, object | None], ...]], ...] = ()
_SELF_BINDINGS: tuple[tuple[str, object, object | None], ...] = ()


def _capture_class_bindings() -> tuple[tuple[type[object], tuple[tuple[str, object, object | None], ...]], ...]:
    """Capture method descriptors/codes for every local class in the eight modules."""
    logger.debug("_capture_class_bindings entry")
    rows: list[tuple[type[object], tuple[tuple[str, object, object | None], ...]]] = []
    module_names = frozenset(cast(str, getattr(module, "__name__")) for module in _BINDING_MODULES)
    for module in _BINDING_MODULES:
        for value in vars(module).values():
            if type(value) is not type or getattr(value, "__module__", None) not in module_names:
                continue
            methods = tuple(
                (name, member, getattr(member, "__code__", None))
                for name, member in vars(value).items()
                if callable(member)
            )
            rows.append((cast(type[object], value), methods))
    logger.debug("_capture_class_bindings exit classes=%d", len(rows))
    return tuple(rows)


def _validate_all_bindings() -> None:
    logger.debug("_validate_all_bindings entry")
    for module, rows in _ALL_BINDINGS:
        namespace = vars(module)
        for name, value, code in rows:
            current = namespace.get(name)
            if current is not value or (code is not None and getattr(value, "__code__", None) is not code):
                logger.error("_validate_all_bindings error imported=%s", name)
                raise _Integrity(KEC1IntegrityCodeV1.CODE_DRIFT)
    for cls, rows in _CLASS_BINDINGS:
        class_namespace = vars(cls)
        for name, value, code in rows:
            current = class_namespace.get(name)
            if current is not value or (code is not None and getattr(value, "__code__", None) is not code):
                logger.error("_validate_all_bindings error method=%s.%s", cls.__name__, name)
                raise _Integrity(KEC1IntegrityCodeV1.CODE_DRIFT)
    namespace = globals()
    for name, value, code in _SELF_BINDINGS:
        current = namespace.get(name)
        if current is not value or (code is not None and getattr(value, "__code__", None) is not code):
            logger.error("_validate_all_bindings error local=%s", name)
            raise _Integrity(KEC1IntegrityCodeV1.CODE_DRIFT)
    logger.debug("_validate_all_bindings exit")


def _make_binding_validator(
    all_bindings: tuple[tuple[object, tuple[tuple[str, object, object | None], ...]], ...],
    class_bindings: tuple[tuple[type[object], tuple[tuple[str, object, object | None], ...]], ...],
    self_bindings: tuple[tuple[str, object, object | None], ...],
) -> Callable[[], None]:
    """Close immutable binding sets so rebinding their public globals cannot bypass validation."""
    logger.debug("_make_binding_validator entry")

    def validate() -> None:
        logger.debug("sealed_validate entry")
        if (
            globals().get("_ALL_BINDINGS") is not all_bindings
            or globals().get("_CLASS_BINDINGS") is not class_bindings
            or globals().get("_SELF_BINDINGS") is not self_bindings
            or globals().get("_validate_all_bindings") is not validate
        ):
            logger.error("sealed_validate error seal-binding")
            raise _Integrity(KEC1IntegrityCodeV1.CODE_DRIFT)
        for module, rows in all_bindings:
            namespace = vars(module)
            for name, value, code in rows:
                current = namespace.get(name)
                if current is not value or (code is not None and getattr(value, "__code__", None) is not code):
                    logger.error("sealed_validate error imported=%s", name)
                    raise _Integrity(KEC1IntegrityCodeV1.CODE_DRIFT)
        for cls, rows in class_bindings:
            class_namespace = vars(cls)
            for name, value, code in rows:
                current = class_namespace.get(name)
                if current is not value or (code is not None and getattr(value, "__code__", None) is not code):
                    logger.error("sealed_validate error method=%s.%s", cls.__name__, name)
                    raise _Integrity(KEC1IntegrityCodeV1.CODE_DRIFT)
        namespace = globals()
        for name, value, code in self_bindings:
            current = namespace.get(name)
            if current is not value or (code is not None and getattr(value, "__code__", None) is not code):
                logger.error("sealed_validate error local=%s", name)
                raise _Integrity(KEC1IntegrityCodeV1.CODE_DRIFT)
        logger.debug("sealed_validate exit")

    logger.debug("_make_binding_validator exit")
    return validate


def _frame(value: bytes) -> bytes:
    logger.debug("_frame entry bytes=%d", len(value))
    result = len(value).to_bytes(8, "big") + value
    logger.debug("_frame exit")
    return result


def _root(label: str, fields: tuple[bytes, ...]) -> bytes:
    logger.debug("_root entry fields=%d", len(fields))
    if type(label) is not str or unicodedata.normalize("NFC", label) != label:
        logger.error("_root error label")
        raise ValueError("KEC1 root label")
    logger.debug("_root external sha256")
    result = sha256(_frame(label.encode()) + b"".join(_frame(x) for x in fields)).digest()
    logger.debug("_root exit")
    return result


def _manifest_from(paths: tuple[str, ...], repository_root: Path) -> bytes:
    """Lexically capture regular source bytes with componentwise no-follow."""
    logger.debug("_manifest_from entry files=%d", len(paths))
    if type(paths) is not tuple or not isinstance(repository_root, Path):
        logger.error("_manifest_from error arguments")
        raise ValueError("KEC1 source arguments")
    chunks: list[bytes] = []
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    for name in paths:
        pure = PurePosixPath(name)
        if pure.is_absolute() or str(pure) != name or any(x in {"", ".", ".."} for x in pure.parts):
            logger.error("_manifest_from error path")
            raise ValueError("KEC1 source path")
        logger.debug("_manifest_from external open-root")
        dfd = _OS_OPEN(repository_root, flags | os.O_DIRECTORY)
        ffd = -1
        try:
            for part in pure.parts[:-1]:
                logger.debug("_manifest_from external open-directory")
                nextfd = _OS_OPEN(part, flags | os.O_DIRECTORY, dir_fd=dfd)
                _OS_CLOSE(dfd)
                dfd = nextfd
            logger.debug("_manifest_from external open-file")
            ffd = _OS_OPEN(pure.parts[-1], flags, dir_fd=dfd)
            before = _OS_FSTAT(ffd)
            if not _STAT_ISREG(before.st_mode):
                logger.error("_manifest_from error nonregular")
                raise ValueError("KEC1 source regular")
            parts: list[bytes] = []
            while True:
                chunk = _OS_READ(ffd, 131072)
                if not chunk:
                    break
                parts.append(chunk)
            after = _OS_FSTAT(ffd)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                logger.error("_manifest_from error drift")
                raise ValueError("KEC1 source drift")
            chunks.append(_frame(name.encode()) + _frame(b"".join(parts)))
        finally:
            if ffd >= 0:
                _OS_CLOSE(ffd)
            _OS_CLOSE(dfd)
    result = len(paths).to_bytes(8, "big") + b"".join(chunks)
    logger.debug("_manifest_from exit bytes=%d", len(result))
    return result


def _validate_root_constants() -> None:
    """Reject replacement of any exact source-root scalar/table binding."""
    logger.debug("_validate_root_constants entry")
    if (
        globals().get("KEC1_SOURCE_PATHS_V1") is not _SOURCE_PATHS_CAPTURE
        or globals().get("_REPOSITORY_ROOT") is not _REPOSITORY_ROOT_CAPTURE
        or globals().get("_KPT_SOURCE_ROOT") is not _KPT_SOURCE_ROOT_CAPTURE
        or globals().get("KEC1_EQUATION_BYTES_V1") is not _EQUATION_BYTES_CAPTURE
        or os.open is not _OS_OPEN
        or os.close is not _OS_CLOSE
        or os.read is not _OS_READ
        or os.fstat is not _OS_FSTAT
        or stat.S_ISREG is not _STAT_ISREG
    ):
        logger.error("_validate_root_constants error drift")
        raise RuntimeError("KEC1 root binding drift")
    logger.debug("_validate_root_constants exit")


def _manifest() -> bytes:
    """Capture only the exact immutable eight-file manifest."""
    logger.debug("_manifest entry")
    _validate_root_constants()
    result = _manifest_from(_SOURCE_PATHS_CAPTURE, _REPOSITORY_ROOT_CAPTURE)
    logger.debug("_manifest exit bytes=%d", len(result))
    return result


def empty_core_calculus_source_root_v1() -> bytes:
    """Recompute the exact KPT/KCC/eight-file KEC1 source root."""
    logger.debug("empty_core_calculus_source_root_v1 entry")
    _validate_all_bindings()
    _validate_root_constants()
    result = _root(
        "omegaa.empty-core-calculus-source.v1",
        (_KPT_SOURCE_ROOT_CAPTURE, kcc1_source_root_v1(), _manifest()),
    )
    logger.debug("empty_core_calculus_source_root_v1 exit")
    return result


def empty_core_calculus_id_v1() -> bytes:
    """Bind the source root, empty KCC configuration and 43 exact equations."""
    logger.debug("empty_core_calculus_id_v1 entry")
    _validate_all_bindings()
    _validate_root_constants()
    result = _root(
        "omegaa.empty-core-calculus.v1",
        (empty_core_calculus_source_root_v1(), kcc1_empty_config_id_v1(), _EQUATION_BYTES_CAPTURE),
    )
    logger.debug("empty_core_calculus_id_v1 exit")
    return result


# Seal every imported/local helper only after the complete eight-module surface,
# including both root functions, exists.  The two seal variables are excluded
# from their own fixed point and are separately referenced by validated code.
_ALL_BINDINGS = _capture_bindings()
_CLASS_BINDINGS = _capture_class_bindings()
_SELF_BINDINGS = tuple(
    (name, value, getattr(value, "__code__", None))
    for name, value in globals().items()
    if name not in {"_SELF_BINDINGS", "_validate_all_bindings"} and not name.startswith("__") and callable(value)
)
_validate_all_bindings = _make_binding_validator(_ALL_BINDINGS, _CLASS_BINDINGS, _SELF_BINDINGS)
