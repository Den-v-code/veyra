from __future__ import annotations

from typing import cast

from src.core.omegaa_kpt1_types import KernelProofTermV1, KernelTermTagV1, kernel_term_v1
from src.core.omegaa_kcs1_builder import (
    build_kcs1_compare_types_node_v1,
    build_kcs1_parse_node_v1,
    build_kcs1_run_state_v1,
)
from src.core.omegaa_kcs1_codec import codec_kcn1_v1, codec_kcs1_v1
from src.core.omegaa_kcs1_parser import parse_kar1_v1, parse_kcn1_v1, parse_krl1_v1
from src.core.omegaa_kcs1_types import (
    KCN1CodecResourceResultV1,
    KCN1DecodeCodeV1,
    KCN1DecodeErrorResultV1,
    KCN1IntegrityResultV1,
    KCS1CodecLimitsV1,
    KCS1IntegrityCodeV1,
    KCS1IntegrityResultV1,
    KAR1DecodeCodeV1,
    KAR1DecodeErrorResultV1,
    KRL1DecodeCodeV1,
    KRL1DecodeErrorResultV1,
)
from src.core.omegaa_kcc1_types import EMPTY_CHECKER_CONFIG_V1
from src.core.omegaa_kci1_builder import build_checker_input_syntax_v1


def frame(payload: bytes) -> bytes:
    return len(payload).to_bytes(8, "big") + payload


def error(result: object) -> tuple[object, int]:
    item = object.__getattribute__(result, "error")
    return object.__getattribute__(item, "code"), object.__getattribute__(item, "absolute_offset")


def test_prefix_tag_arity_length_and_trailing_offsets() -> None:
    cases = (
        (b"X", KCN1DecodeCodeV1.BAD_DOMAIN, 0),
        (b"KCNX", KCN1DecodeCodeV1.BAD_VERSION, 3),
        (b"KCN", KCN1DecodeCodeV1.BAD_LENGTH, 3),
        (b"KCN1\xff", KCN1DecodeCodeV1.BAD_TAG, 4),
        (b"KCN1\x01", KCN1DecodeCodeV1.BAD_LENGTH, 5),
        (b"KCN1\x01\x00", KCN1DecodeCodeV1.BAD_ARITY, 5),
        (b"KCN1\x01\x01", KCN1DecodeCodeV1.BAD_LENGTH, 6),
        (b"KCN1\x01\x01" + frame(b"") + b"x", KCN1DecodeCodeV1.TRAILING, 14),
    )
    for raw, code, offset in cases:
        result = parse_kcn1_v1(raw)
        assert type(result) is KCN1DecodeErrorResultV1
        assert error(result) == (code, offset)


def test_nat_canonicality_and_relation_failures() -> None:
    short = b"KRL1\x01\x01" + frame(b"\0" * 7)
    result = parse_krl1_v1(short)
    assert type(result) is KRL1DecodeErrorResultV1
    assert error(result) == (KRL1DecodeCodeV1.BAD_LENGTH, len(short))
    leading = b"KRL1\x01\x01" + frame((1).to_bytes(8, "big") + b"\0")
    assert error(parse_krl1_v1(leading)) == (KRL1DecodeCodeV1.NONCANONICAL_NAT, 22)
    allowed = frame((0).to_bytes(8, "big"))
    required = frame((0).to_bytes(8, "big"))
    locus = frame(b"KRL1\x03\x00")
    krf = b"KRF1\x00\x04" + frame(b"\x01") + allowed + required + locus
    kar = b"KAR1\x01\x01" + frame(krf)
    result = parse_kar1_v1(kar)
    assert type(result) is KAR1DecodeErrorResultV1
    assert error(result)[0] is KAR1DecodeCodeV1.BAD_ORDER


def test_output_and_input_resources_are_typed_and_separate() -> None:
    value = build_kcs1_parse_node_v1(b"payload")
    limits = KCS1CodecLimitsV1(max_output_bytes=1)
    encoded = codec_kcn1_v1(value, limits)
    assert type(encoded) is KCN1CodecResourceResultV1
    assert encoded.resource.kind.name == "OUTPUT_BYTES"
    good = codec_kcn1_v1(value)
    parsed = parse_kcn1_v1(good.wire, KCS1CodecLimitsV1(max_input_bytes=1))
    assert type(parsed) is KCN1CodecResourceResultV1
    assert parsed.resource.kind.name == "INPUT_BYTES"
    assert parsed.resource.absolute_offset == 1


def test_shared_and_cyclic_semantic_graphs_refuse() -> None:
    shared = kernel_term_v1(KernelTermTagV1.VAR, 0)
    result = codec_kcn1_v1(build_kcs1_compare_types_node_v1(shared, shared, shared))
    assert type(result) is KCN1IntegrityResultV1
    assert result.error.code is KCS1IntegrityCodeV1.GRAPH_SHARED
    cyclic = object.__new__(KernelProofTermV1)
    cast(object, vars(KernelProofTermV1)["tag"]).__set__(cyclic, KernelTermTagV1.FST)
    cast(object, vars(KernelProofTermV1)["fields"]).__set__(cyclic, (cyclic,))
    result = codec_kcn1_v1(
        build_kcs1_compare_types_node_v1(
            cyclic, kernel_term_v1(KernelTermTagV1.VAR, 1), kernel_term_v1(KernelTermTagV1.VAR, 2)
        )
    )
    assert type(result) is KCN1IntegrityResultV1
    assert result.error.code is KCS1IntegrityCodeV1.GRAPH_CYCLE


def test_nominal_run_is_not_terminal_or_authority() -> None:
    run = build_kcs1_run_state_v1(
        build_kcs1_parse_node_v1(b"x"),
        EMPTY_CHECKER_CONFIG_V1,
        build_checker_input_syntax_v1(b"e", b"t"),
        (),
        (),
        (),
        0,
    )
    result = codec_kcs1_v1(run)
    assert type(result).__name__ == "KCS1EncodedResultV1"
    assert not hasattr(result, "authority")
    assert not hasattr(result, "soundness")
    forged = object.__new__(type(run))
    assert type(codec_kcs1_v1(forged)) is KCS1IntegrityResultV1
