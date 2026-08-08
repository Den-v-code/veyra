from __future__ import annotations

from collections.abc import Callable

import pytest

from src.core.omegaa_kcc1_types import EMPTY_CHECKER_CONFIG_V1
from src.core.omegaa_kcf1_types import KernelContinuationTagV1, kernel_continuation_frame_v1
from src.core.omegaa_kci1_builder import build_checker_input_syntax_v1
from src.core.omegaa_keb1_builder import expected_binding_v1
from src.core.omegaa_kpt1_types import KernelTermTagV1, kernel_term_v1
from src.core.omegaa_kcs1_builder import (
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
from src.core.omegaa_kcs1_codec import (
    codec_kar1_v1,
    codec_kcn1_v1,
    codec_kcs1_v1,
    codec_krf1_v1,
    codec_krl1_v1,
    codec_krr1_v1,
)
from src.core.omegaa_kcs1_parser import (
    parse_kar1_v1,
    parse_kcn1_v1,
    parse_kcs1_v1,
    parse_krf1_v1,
    parse_krl1_v1,
    parse_krr1_v1,
)
from src.core.omegaa_kcs1_types import (
    DEFAULT_KCS1_CODEC_LIMITS_V1,
    KAR1DecodedResultV1,
    KAR1EncodedResultV1,
    KCN1DecodedResultV1,
    KCN1EncodedResultV1,
    KCS1AttemptResourceKindV1,
    KCS1DecodedResultV1,
    KCS1EncodedResultV1,
    KCS1InternalCodeV1,
    KCS1RejectCodeSyntaxV1,
    KRF1DecodedResultV1,
    KRF1EncodedResultV1,
    KRL1DecodedResultV1,
    KRL1EncodedResultV1,
    KRR1DecodedResultV1,
    KRR1EncodedResultV1,
)


def term(index: int):
    return kernel_term_v1(KernelTermTagV1.VAR, index)


def binding(index: int):
    return expected_binding_v1(term(index))


def roundtrip(
    value: object,
    codec: Callable[..., object],
    parser: Callable[..., object],
    encoded: type,
    decoded: type,
    prefix: bytes,
) -> None:
    first = codec(value)
    assert type(first) is encoded
    assert first.wire[:4] == prefix
    parsed = parser(first.wire)
    assert type(parsed) is decoded
    assert parsed.end == len(first.wire)
    second = codec(parsed.value)
    assert type(second) is encoded
    assert second.wire == first.wire


def test_all_six_node_tags_roundtrip() -> None:
    nodes = (
        build_kcs1_entry_node_v1(binding(1)),
        build_kcs1_parse_node_v1(b"payload"),
        build_kcs1_infer_node_v1(term(2)),
        build_kcs1_reduce_node_v1(term(3)),
        build_kcs1_compare_types_node_v1(term(4), term(5), term(6)),
        build_kcs1_return_typed_node_v1(b"r" * 32),
    )
    for node in nodes:
        roundtrip(node, codec_kcn1_v1, parse_kcn1_v1, KCN1EncodedResultV1, KCN1DecodedResultV1, b"KCN1")


def test_all_state_reduction_and_locus_tags_roundtrip() -> None:
    checker_input = build_checker_input_syntax_v1(b"expected", b"term")
    frame = kernel_continuation_frame_v1(KernelContinuationTagV1.PARSE_TERM, b"x", term(9))
    states = (
        build_kcs1_run_state_v1(
            build_kcs1_parse_node_v1(b"x"), EMPTY_CHECKER_CONFIG_V1, checker_input, (term(7),), (term(8),), (frame,), 17
        ),
        build_kcs1_accept_state_v1(term(10), b"a" * 32),
        build_kcs1_reject_state_v1(KCS1RejectCodeSyntaxV1.DEPENDENCY, 19),
    )
    for state in states:
        roundtrip(state, codec_kcs1_v1, parse_kcs1_v1, KCS1EncodedResultV1, KCS1DecodedResultV1, b"KCS1")
    for reduction in (build_kcs1_nf_result_v1(term(11)), build_kcs1_step_result_v1(term(12))):
        roundtrip(reduction, codec_krr1_v1, parse_krr1_v1, KRR1EncodedResultV1, KRR1DecodedResultV1, b"KRR1")
    loci = (
        build_kcs1_input_offset_locus_v1(3),
        build_kcs1_state_step_locus_v1(4),
        build_kcs1_structural_count_locus_v1(5),
        build_kcs1_no_locus_v1(),
    )
    for locus in loci:
        roundtrip(locus, codec_krl1_v1, parse_krl1_v1, KRL1EncodedResultV1, KRL1DecodedResultV1, b"KRL1")


def test_all_resource_kinds_and_attempt_tags_roundtrip() -> None:
    input_locus = build_kcs1_input_offset_locus_v1(2)
    no_locus = build_kcs1_no_locus_v1()
    structural = build_kcs1_structural_count_locus_v1(3)
    state_step = build_kcs1_state_step_locus_v1(4)
    loci = (
        input_locus,
        no_locus,
        structural,
        structural,
        structural,
        structural,
        structural,
        structural,
        state_step,
        state_step,
        structural,
    )
    resources = []
    for index, kind in enumerate(KCS1AttemptResourceKindV1):
        resource = build_kcs1_attempt_resource_v1(kind, index, index + 1, loci[index])
        resources.append(resource)
        roundtrip(resource, codec_krf1_v1, parse_krf1_v1, KRF1EncodedResultV1, KRF1DecodedResultV1, b"KRF1")
    attempts = (
        build_kcs1_terminal_attempt_v1(build_kcs1_reject_state_v1(KCS1RejectCodeSyntaxV1.BAD_TAG, 1)),
        build_kcs1_resource_attempt_v1(resources[0]),
        build_kcs1_internal_attempt_v1(KCS1InternalCodeV1.INVARIANT, no_locus),
    )
    for attempt in attempts:
        roundtrip(attempt, codec_kar1_v1, parse_kar1_v1, KAR1EncodedResultV1, KAR1DecodedResultV1, b"KAR1")


def test_every_public_default_is_same_captured_object() -> None:
    functions = (
        codec_kcn1_v1,
        codec_kcs1_v1,
        codec_krr1_v1,
        codec_krl1_v1,
        codec_krf1_v1,
        codec_kar1_v1,
        parse_kcn1_v1,
        parse_kcs1_v1,
        parse_krr1_v1,
        parse_krl1_v1,
        parse_krf1_v1,
        parse_kar1_v1,
    )
    assert all(function.__defaults__ == (DEFAULT_KCS1_CODEC_LIMITS_V1,) for function in functions)
    assert all(function.__defaults__[0] is DEFAULT_KCS1_CODEC_LIMITS_V1 for function in functions)


def test_builders_reject_bool_and_wrong_relation() -> None:
    with pytest.raises(ValueError):
        build_kcs1_input_offset_locus_v1(True)
    with pytest.raises(ValueError):
        build_kcs1_attempt_resource_v1(KCS1AttemptResourceKindV1.OUTPUT_BYTES, 1, 1, build_kcs1_no_locus_v1())
    with pytest.raises(ValueError):
        build_kcs1_attempt_resource_v1(KCS1AttemptResourceKindV1.OUTPUT_BYTES, 1, 2, build_kcs1_state_step_locus_v1(0))
