"""Captured hook-free builders for relation-valid inert KCS1 syntax."""

from __future__ import annotations

import logging
from enum import IntEnum
from types import MemberDescriptorType
from typing import NoReturn, Protocol, TypeVar, cast

from . import omegaa_kcs1_types as t
from .omegaa_kcc1_types import EMPTY_CHECKER_CONFIG_V1, EmptyCheckerConfigV1
from .omegaa_kcf1_types import KernelContinuationFrameV1
from .omegaa_kci1_types import CheckerInputSyntaxV1
from .omegaa_keb1_types import ExpectedBindingSyntaxV1
from .omegaa_kpt1_types import KernelProofTermV1

logger = logging.getLogger(__name__)
_OBJECT_NEW = object.__new__
_T = TypeVar("_T")


class _Setter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def _builder_error(reason: str) -> NoReturn:
    logger.debug("_builder_error entry reason=%s", reason)
    logger.error("KCS1 builder rejected reason=%s", reason)
    raise ValueError(reason)


_CLASSES: tuple[type[object], ...] = (
    t.KCS1EntryNodeV1,
    t.KCS1ParseNodeV1,
    t.KCS1InferNodeV1,
    t.KCS1ReduceNodeV1,
    t.KCS1CompareTypesNodeV1,
    t.KCS1ReturnTypedNodeV1,
    t.KCS1RunStateV1,
    t.KCS1AcceptStateV1,
    t.KCS1RejectStateV1,
    t.KCS1NFResultSyntaxV1,
    t.KCS1StepResultSyntaxV1,
    t.KCS1InputOffsetLocusV1,
    t.KCS1StateStepLocusV1,
    t.KCS1StructuralCountLocusV1,
    t.KCS1NoLocusV1,
    t.KCS1AttemptResourceSyntaxV1,
    t.KCS1TerminalAttemptV1,
    t.KCS1ResourceAttemptV1,
    t.KCS1InternalAttemptV1,
    t.KCS1CodecResourceV1,
    t.KCS1IntegrityV1,
    t.KCN1DecodeErrorV1,
    t.KCS1DecodeErrorV1,
    t.KRR1DecodeErrorV1,
    t.KRL1DecodeErrorV1,
    t.KRF1DecodeErrorV1,
    t.KAR1DecodeErrorV1,
    t.KCN1DecodedResultV1,
    t.KCS1DecodedResultV1,
    t.KRR1DecodedResultV1,
    t.KRL1DecodedResultV1,
    t.KRF1DecodedResultV1,
    t.KAR1DecodedResultV1,
    t.KCN1DecodeErrorResultV1,
    t.KCS1DecodeErrorResultV1,
    t.KRR1DecodeErrorResultV1,
    t.KRL1DecodeErrorResultV1,
    t.KRF1DecodeErrorResultV1,
    t.KAR1DecodeErrorResultV1,
    t.KCN1CodecResourceResultV1,
    t.KCS1CodecResourceResultV1,
    t.KRR1CodecResourceResultV1,
    t.KRL1CodecResourceResultV1,
    t.KRF1CodecResourceResultV1,
    t.KAR1CodecResourceResultV1,
    t.KCN1IntegrityResultV1,
    t.KCS1IntegrityResultV1,
    t.KRR1IntegrityResultV1,
    t.KRL1IntegrityResultV1,
    t.KRF1IntegrityResultV1,
    t.KAR1IntegrityResultV1,
    t.KCN1EncodedResultV1,
    t.KCS1EncodedResultV1,
    t.KRR1EncodedResultV1,
    t.KRL1EncodedResultV1,
    t.KRF1EncodedResultV1,
    t.KAR1EncodedResultV1,
)
_CLASS_NAMES = tuple(cls.__name__ for cls in _CLASSES)
_SLOTS = tuple(tuple(vars(cls)[name] for name in getattr(cls, "__slots__", ())) for cls in _CLASSES)
_INITS = tuple(vars(cls)["__init__"] for cls in _CLASSES)
_POSTS = tuple(vars(cls).get("__post_init__") for cls in _CLASSES)
_INIT_CODES = tuple(init.__code__ for init in _INITS)
_POST_CODES = tuple(post.__code__ if post is not None else None for post in _POSTS)
_ENUMS: tuple[type[IntEnum], ...] = (
    t.KCS1NodeTagV1,
    t.KCS1StateTagV1,
    t.KCS1ReductionTagV1,
    t.KCS1LocusTagV1,
    t.KCS1RejectCodeSyntaxV1,
    t.KCS1AttemptResourceKindV1,
    t.KCS1InternalCodeV1,
    t.KCS1CodecResourceKindV1,
    t.KCS1IntegrityCodeV1,
    t.KCN1DecodeCodeV1,
    t.KCS1DecodeCodeV1,
    t.KRR1DecodeCodeV1,
    t.KRL1DecodeCodeV1,
    t.KRF1DecodeCodeV1,
    t.KAR1DecodeCodeV1,
)
_ENUM_MEMBERS = tuple(tuple(enum_cls(index) for index in range(len(enum_cls))) for enum_cls in _ENUMS)


def validate_kcs1_builder_integrity_v1() -> None:
    """Fail closed on class/slot/enum/constructor drift."""
    logger.debug("validate_kcs1_builder_integrity_v1 entry")
    namespace = vars(t)
    drift = any(namespace.get(name) is not cls for name, cls in zip(_CLASS_NAMES, _CLASSES, strict=True))
    for cls, slots, init, post, init_code, post_code in zip(
        _CLASSES,
        _SLOTS,
        _INITS,
        _POSTS,
        _INIT_CODES,
        _POST_CODES,
        strict=True,
    ):
        names = getattr(cls, "__slots__", ())
        drift = drift or vars(cls).get("__init__") is not init or init.__code__ is not init_code
        drift = drift or vars(cls).get("__post_init__") is not post
        drift = drift or (post is not None and post.__code__ is not post_code)
        drift = drift or any(
            vars(cls).get(name) is not slot or type(slot) is not MemberDescriptorType
            for name, slot in zip(names, slots, strict=True)
        )
    for enum_cls, members in zip(_ENUMS, _ENUM_MEMBERS, strict=True):
        drift = drift or namespace.get(enum_cls.__name__) is not enum_cls
        drift = drift or any(
            type(member) is not enum_cls or object.__getattribute__(member, "_value_") != index
            for index, member in enumerate(members)
        )
    if drift:
        logger.error("validate_kcs1_builder_integrity_v1 error drift")
        raise ValueError("kcs1-builder-integrity")
    logger.debug("validate_kcs1_builder_integrity_v1 exit")


def _new(cls: type[_T], values: tuple[object, ...]) -> _T:
    logger.debug("_new entry class=%s", cls.__name__)
    validate_kcs1_builder_integrity_v1()
    try:
        index = _CLASSES.index(cast(type[object], cls))
    except ValueError:
        logger.error("_new error unknown-class")
        raise ValueError("kcs1-builder-class") from None
    slots = _SLOTS[index]
    if len(slots) != len(values):
        logger.error("_new error arity")
        raise ValueError("kcs1-builder-arity")
    result = _OBJECT_NEW(cls)
    for slot, value in zip(slots, values, strict=True):
        cast(_Setter, slot).__set__(result, value)
    logger.debug("_new exit class=%s", cls.__name__)
    return result


_NODE_CLASSES = (
    t.KCS1EntryNodeV1,
    t.KCS1ParseNodeV1,
    t.KCS1InferNodeV1,
    t.KCS1ReduceNodeV1,
    t.KCS1CompareTypesNodeV1,
    t.KCS1ReturnTypedNodeV1,
)
_LOCUS_CLASSES = (
    t.KCS1InputOffsetLocusV1,
    t.KCS1StateStepLocusV1,
    t.KCS1StructuralCountLocusV1,
    t.KCS1NoLocusV1,
)


def _exact_tuple(value: object, item_class: type[object]) -> bool:
    logger.debug("_exact_tuple entry item_class=%s", item_class.__name__)
    result = type(value) is tuple and all(type(item) is item_class for item in cast(tuple[object, ...], value))
    logger.debug("_exact_tuple exit valid=%s", result)
    return result


def build_kcs1_entry_node_v1(binding: ExpectedBindingSyntaxV1) -> t.KCS1EntryNodeV1:
    logger.debug("build_kcs1_entry_node_v1 entry")
    if type(binding) is not ExpectedBindingSyntaxV1:
        _builder_error("entry-binding")
    result = _new(t.KCS1EntryNodeV1, (binding,))
    logger.debug("build_kcs1_entry_node_v1 exit")
    return result


def build_kcs1_parse_node_v1(payload: bytes) -> t.KCS1ParseNodeV1:
    logger.debug("build_kcs1_parse_node_v1 entry")
    if type(payload) is not bytes:
        _builder_error("parse-payload")
    result = _new(t.KCS1ParseNodeV1, (payload,))
    logger.debug("build_kcs1_parse_node_v1 exit")
    return result


def build_kcs1_infer_node_v1(term: KernelProofTermV1) -> t.KCS1InferNodeV1:
    logger.debug("build_kcs1_infer_node_v1 entry")
    if type(term) is not KernelProofTermV1:
        _builder_error("infer-term")
    result = _new(t.KCS1InferNodeV1, (term,))
    logger.debug("build_kcs1_infer_node_v1 exit")
    return result


def build_kcs1_reduce_node_v1(term: KernelProofTermV1) -> t.KCS1ReduceNodeV1:
    logger.debug("build_kcs1_reduce_node_v1 entry")
    if type(term) is not KernelProofTermV1:
        _builder_error("reduce-term")
    result = _new(t.KCS1ReduceNodeV1, (term,))
    logger.debug("build_kcs1_reduce_node_v1 exit")
    return result


def build_kcs1_compare_types_node_v1(
    term: KernelProofTermV1, expected_nf: KernelProofTermV1, inferred_nf: KernelProofTermV1
) -> t.KCS1CompareTypesNodeV1:
    logger.debug("build_kcs1_compare_types_node_v1 entry")
    if any(type(value) is not KernelProofTermV1 for value in (term, expected_nf, inferred_nf)):
        _builder_error("compare-terms")
    result = _new(t.KCS1CompareTypesNodeV1, (term, expected_nf, inferred_nf))
    logger.debug("build_kcs1_compare_types_node_v1 exit")
    return result


def build_kcs1_return_typed_node_v1(kernel_type_id: bytes) -> t.KCS1ReturnTypedNodeV1:
    logger.debug("build_kcs1_return_typed_node_v1 entry")
    if type(kernel_type_id) is not bytes or len(kernel_type_id) != 32:
        _builder_error("return-type-id")
    result = _new(t.KCS1ReturnTypedNodeV1, (kernel_type_id,))
    logger.debug("build_kcs1_return_typed_node_v1 exit")
    return result


def build_kcs1_run_state_v1(
    node: t.CheckerNodeSyntaxV1,
    config: EmptyCheckerConfigV1,
    input: CheckerInputSyntaxV1,
    ctx: tuple[KernelProofTermV1, ...],
    value_stack: tuple[KernelProofTermV1, ...],
    continuation: tuple[KernelContinuationFrameV1, ...],
    offset: int,
) -> t.KCS1RunStateV1:
    logger.debug("build_kcs1_run_state_v1 entry")
    valid = (
        type(node) in _NODE_CLASSES
        and config is EMPTY_CHECKER_CONFIG_V1
        and type(input) is CheckerInputSyntaxV1
        and _exact_tuple(ctx, KernelProofTermV1)
        and _exact_tuple(value_stack, KernelProofTermV1)
        and _exact_tuple(continuation, KernelContinuationFrameV1)
        and type(offset) is int
        and 0 <= offset < 2**64
    )
    if not valid:
        logger.error("build_kcs1_run_state_v1 error host-shape")
        raise ValueError("run-state")
    result = _new(t.KCS1RunStateV1, (node, config, input, ctx, value_stack, continuation, offset))
    logger.debug("build_kcs1_run_state_v1 exit")
    return result


def build_kcs1_accept_state_v1(kernel_nf: KernelProofTermV1, kernel_type_id: bytes) -> t.KCS1AcceptStateV1:
    logger.debug("build_kcs1_accept_state_v1 entry")
    if type(kernel_nf) is not KernelProofTermV1 or type(kernel_type_id) is not bytes or len(kernel_type_id) != 32:
        _builder_error("accept-state")
    result = _new(t.KCS1AcceptStateV1, (kernel_nf, kernel_type_id))
    logger.debug("build_kcs1_accept_state_v1 exit")
    return result


def build_kcs1_reject_state_v1(code: t.KCS1RejectCodeSyntaxV1, input_offset: int) -> t.KCS1RejectStateV1:
    logger.debug("build_kcs1_reject_state_v1 entry")
    if type(code) is not t.KCS1RejectCodeSyntaxV1 or type(input_offset) is not int or not 0 <= input_offset < 2**64:
        _builder_error("reject-state")
    result = _new(t.KCS1RejectStateV1, (code, input_offset))
    logger.debug("build_kcs1_reject_state_v1 exit")
    return result


def build_kcs1_nf_result_v1(term: KernelProofTermV1) -> t.KCS1NFResultSyntaxV1:
    logger.debug("build_kcs1_nf_result_v1 entry")
    if type(term) is not KernelProofTermV1:
        _builder_error("nf-term")
    result = _new(t.KCS1NFResultSyntaxV1, (term,))
    logger.debug("build_kcs1_nf_result_v1 exit")
    return result


def build_kcs1_step_result_v1(term: KernelProofTermV1) -> t.KCS1StepResultSyntaxV1:
    logger.debug("build_kcs1_step_result_v1 entry")
    if type(term) is not KernelProofTermV1:
        _builder_error("step-term")
    result = _new(t.KCS1StepResultSyntaxV1, (term,))
    logger.debug("build_kcs1_step_result_v1 exit")
    return result


def build_kcs1_input_offset_locus_v1(offset: int) -> t.KCS1InputOffsetLocusV1:
    logger.debug("build_kcs1_input_offset_locus_v1 entry")
    if type(offset) is not int or not 0 <= offset < 2**64:
        _builder_error("input-offset-locus")
    result = _new(t.KCS1InputOffsetLocusV1, (offset,))
    logger.debug("build_kcs1_input_offset_locus_v1 exit")
    return result


def build_kcs1_state_step_locus_v1(step: int) -> t.KCS1StateStepLocusV1:
    logger.debug("build_kcs1_state_step_locus_v1 entry")
    if type(step) is not int or step < 0:
        _builder_error("state-step-locus")
    result = _new(t.KCS1StateStepLocusV1, (step,))
    logger.debug("build_kcs1_state_step_locus_v1 exit")
    return result


def build_kcs1_structural_count_locus_v1(count: int) -> t.KCS1StructuralCountLocusV1:
    logger.debug("build_kcs1_structural_count_locus_v1 entry")
    if type(count) is not int or count < 0:
        _builder_error("structural-count-locus")
    result = _new(t.KCS1StructuralCountLocusV1, (count,))
    logger.debug("build_kcs1_structural_count_locus_v1 exit")
    return result


def build_kcs1_no_locus_v1() -> t.KCS1NoLocusV1:
    logger.debug("build_kcs1_no_locus_v1 entry")
    result = _new(t.KCS1NoLocusV1, ())
    logger.debug("build_kcs1_no_locus_v1 exit")
    return result


_LOCUS_FOR_KIND = {
    t.KCS1AttemptResourceKindV1.INPUT_BYTES: t.KCS1InputOffsetLocusV1,
    t.KCS1AttemptResourceKindV1.OUTPUT_BYTES: t.KCS1NoLocusV1,
    t.KCS1AttemptResourceKindV1.COMPOSITE_DEPTH: t.KCS1StructuralCountLocusV1,
    t.KCS1AttemptResourceKindV1.COMPOSITE_NODES: t.KCS1StructuralCountLocusV1,
    t.KCS1AttemptResourceKindV1.VECTOR_ITEMS: t.KCS1StructuralCountLocusV1,
    t.KCS1AttemptResourceKindV1.NESTED_KPT_BYTES: t.KCS1StructuralCountLocusV1,
    t.KCS1AttemptResourceKindV1.KPT_LIST_ITEMS: t.KCS1StructuralCountLocusV1,
    t.KCS1AttemptResourceKindV1.KPT_NAT_BYTES: t.KCS1StructuralCountLocusV1,
    t.KCS1AttemptResourceKindV1.STEPS: t.KCS1StateStepLocusV1,
    t.KCS1AttemptResourceKindV1.DEADLINE_NS: t.KCS1StateStepLocusV1,
    t.KCS1AttemptResourceKindV1.MEMORY_BYTES: t.KCS1StructuralCountLocusV1,
}


def build_kcs1_attempt_resource_v1(
    kind: t.KCS1AttemptResourceKindV1, allowed: int, required: int, locus: t.ResourceLocusSyntaxV1
) -> t.KCS1AttemptResourceSyntaxV1:
    logger.debug("build_kcs1_attempt_resource_v1 entry")
    valid = (
        type(kind) is t.KCS1AttemptResourceKindV1
        and type(allowed) is int
        and type(required) is int
        and allowed >= 0
        and required > allowed
        and type(locus) is _LOCUS_FOR_KIND.get(kind)
    )
    if not valid:
        logger.error("build_kcs1_attempt_resource_v1 error relation")
        _builder_error("attempt-resource")
    result = _new(t.KCS1AttemptResourceSyntaxV1, (kind, allowed, required, locus))
    logger.debug("build_kcs1_attempt_resource_v1 exit")
    return result


def build_kcs1_terminal_attempt_v1(state: t.KCS1AcceptStateV1 | t.KCS1RejectStateV1) -> t.KCS1TerminalAttemptV1:
    logger.debug("build_kcs1_terminal_attempt_v1 entry")
    if type(state) not in (t.KCS1AcceptStateV1, t.KCS1RejectStateV1):
        _builder_error("terminal-attempt")
    result = _new(t.KCS1TerminalAttemptV1, (state,))
    logger.debug("build_kcs1_terminal_attempt_v1 exit")
    return result


def build_kcs1_resource_attempt_v1(resource: t.KCS1AttemptResourceSyntaxV1) -> t.KCS1ResourceAttemptV1:
    logger.debug("build_kcs1_resource_attempt_v1 entry")
    if type(resource) is not t.KCS1AttemptResourceSyntaxV1:
        _builder_error("resource-attempt")
    result = _new(t.KCS1ResourceAttemptV1, (resource,))
    logger.debug("build_kcs1_resource_attempt_v1 exit")
    return result


def build_kcs1_internal_attempt_v1(
    code: t.KCS1InternalCodeV1, locus: t.ResourceLocusSyntaxV1
) -> t.KCS1InternalAttemptV1:
    logger.debug("build_kcs1_internal_attempt_v1 entry")
    if type(code) is not t.KCS1InternalCodeV1 or type(locus) not in _LOCUS_CLASSES:
        _builder_error("internal-attempt")
    result = _new(t.KCS1InternalAttemptV1, (code, locus))
    logger.debug("build_kcs1_internal_attempt_v1 exit")
    return result


def _build_result_v1(cls: type[_T], values: tuple[object, ...]) -> _T:
    """Private hook-free result allocator used only after complete validation."""
    logger.debug("_build_result_v1 entry class=%s", cls.__name__)
    result = _new(cls, values)
    logger.debug("_build_result_v1 exit class=%s", cls.__name__)
    return result
