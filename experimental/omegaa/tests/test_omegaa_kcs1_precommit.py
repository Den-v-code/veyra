"""Allocation-order and exact prospective-locus gates for KCS1."""

from __future__ import annotations

from src.core import omegaa_kcs1_codec as codec_module
from src.core import omegaa_kcs1_parser as parser_module
from src.core.omegaa_kcs1_builder import build_kcs1_infer_node_v1, build_kcs1_parse_node_v1
from src.core.omegaa_kcs1_codec import codec_kcn1_v1
from src.core.omegaa_kcs1_parser import parse_kcn1_v1
from src.core.omegaa_kcs1_types import (
    KCN1CodecResourceResultV1,
    KCN1EncodedResultV1,
    KCS1CodecLimitsV1,
    KCS1CodecResourceKindV1,
)
from src.core.omegaa_kpt1_types import KernelTermTagV1, kernel_term_v1


def limits(*, output: int = 1_048_576, nodes: int = 20_000, nested: int = 1_048_576) -> KCS1CodecLimitsV1:
    return KCS1CodecLimitsV1(1_048_576, output, 132, nodes, 4096, nested, 4096, 64)


def wire_of(value: object) -> bytes:
    encoded = codec_kcn1_v1(value)  # type: ignore[arg-type]
    assert type(encoded) is KCN1EncodedResultV1
    return encoded.wire


def test_parser_output_refusal_precedes_owned_builder(monkeypatch) -> None:
    wire = wire_of(build_kcs1_parse_node_v1(b"payload"))
    calls = 0

    def forbidden(_: bytes) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("builder ran before OUTPUT")

    monkeypatch.setattr(parser_module, "build_kcs1_parse_node_v1", forbidden)
    result = parse_kcn1_v1(wire, limits(output=len(wire) - 1))
    assert type(result) is KCN1CodecResourceResultV1
    assert result.resource.kind is KCS1CodecResourceKindV1.OUTPUT_BYTES
    assert result.resource.absolute_offset == 0
    assert calls == 0


def test_parser_structural_refusal_precedes_dependency_parse(monkeypatch) -> None:
    wire = wire_of(build_kcs1_infer_node_v1(kernel_term_v1(KernelTermTagV1.VAR, 1)))
    calls = 0

    def forbidden(*_: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("dependency parser ran before resource gate")

    monkeypatch.setattr(parser_module, "parse_kernel_proof_term_v1", forbidden)
    result = parse_kcn1_v1(wire, limits(nodes=1))
    assert type(result) is KCN1CodecResourceResultV1
    assert result.resource.kind is KCS1CodecResourceKindV1.COMPOSITE_NODES
    assert result.resource.absolute_offset == 14
    assert calls == 0


def test_encoder_output_refusal_precedes_dependency_codec(monkeypatch) -> None:
    value = build_kcs1_infer_node_v1(kernel_term_v1(KernelTermTagV1.VAR, 2))
    expected = wire_of(value)
    calls = 0

    def forbidden(*_: object) -> bytes:
        nonlocal calls
        calls += 1
        raise AssertionError("dependency codec ran before OUTPUT")

    monkeypatch.setattr(codec_module, "codec_kernel_proof_term_v1", forbidden)
    result = codec_kcn1_v1(value, limits(output=len(expected) - 1))
    assert type(result) is KCN1CodecResourceResultV1
    assert result.resource.kind is KCS1CodecResourceKindV1.OUTPUT_BYTES
    assert calls == 0


def test_resource_tie_uses_kind_ordinal_at_same_owned_locus() -> None:
    wire = wire_of(build_kcs1_infer_node_v1(kernel_term_v1(KernelTermTagV1.VAR, 3)))
    result = parse_kcn1_v1(wire, limits(nodes=1, nested=1))
    assert type(result) is KCN1CodecResourceResultV1
    assert result.resource.absolute_offset == 14
    assert result.resource.kind is KCS1CodecResourceKindV1.COMPOSITE_NODES
