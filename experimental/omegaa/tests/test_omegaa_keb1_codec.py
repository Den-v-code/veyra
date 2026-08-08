"""Focused canonical wire, inverse and exact KEB1 resource tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.omegaa_keb1_builder import expected_binding_v1
from src.core.omegaa_keb1_codec import codec_expected_binding_v1
from src.core.omegaa_keb1_common import (
    FirstUnsignedDifferenceV1, KEB1DecodeCodeV1, KEB1DecodeError, KEB1LimitsV1,
    KEB1ResourceKindV1, KEB1ResourceLimit,
)
from src.core.omegaa_keb1_parser import parse_expected_binding_v1
from src.core.omegaa_keb1_types import (
    ExpectedBindingSyntaxV1, KEB1DecodedResultV1, KEB1ResourceParseResultV1,
)
from src.core.omegaa_kpt1_codec import codec_kernel_proof_term_v1
from src.core.omegaa_kpt1_types import (
    KernelTermTagV1, kernel_term_v1, succ_level_v1, zero_level_v1,
)


def _frame(value: bytes) -> bytes:
    return len(value).to_bytes(8, "big") + value


def _var(value: int = 0):
    return kernel_term_v1(KernelTermTagV1.VAR, value)


def _wire(term, second: bytes | None = None) -> bytes:
    payload = codec_kernel_proof_term_v1(term)
    return b"KEB1\x00\x02" + _frame(payload) + _frame(payload if second is None else second)


def _limits(**changes: int) -> KEB1LimitsV1:
    return replace(KEB1LimitsV1(), **changes)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    (
        (b"abc", b"abc", None),
        (b"abc", b"xbc", 0),
        (b"abc", b"axc", 1),
        (b"abc", b"ab", 2),
        (b"ab", b"abc", 2),
        (b"", b"", None),
    ),
)
def test_first_unsigned_difference_exact_total_contract(
    left: bytes, right: bytes, expected: int | None,
) -> None:
    assert FirstUnsignedDifferenceV1(left, right) == expected


def test_exact_wire_and_fresh_roundtrip() -> None:
    term = _var(0)
    binding = expected_binding_v1(term)
    raw = codec_expected_binding_v1(binding)
    payload = codec_kernel_proof_term_v1(term)
    assert raw == b"KEB1\x00\x02" + _frame(payload) + _frame(payload)
    parsed = parse_expected_binding_v1(raw)
    assert type(parsed) is KEB1DecodedResultV1
    assert parsed.value == binding
    assert parsed.value is not binding
    assert parsed.value.expected_term is not term
    assert parsed.value.expected_wire == payload
    assert parsed.end == len(raw)


@pytest.mark.parametrize("value", (0, 1, 255, 256, 2**511 - 1))
def test_var_nat_roundtrip(value: int) -> None:
    binding = expected_binding_v1(_var(value))
    result = parse_expected_binding_v1(codec_expected_binding_v1(binding))
    assert type(result) is KEB1DecodedResultV1
    assert result.value == binding


def test_level_and_nested_term_roundtrip() -> None:
    sort = kernel_term_v1(KernelTermTagV1.SORT, succ_level_v1(zero_level_v1()))
    term = kernel_term_v1(KernelTermTagV1.APP, kernel_term_v1(KernelTermTagV1.LAM, sort, _var()), _var(1))
    binding = expected_binding_v1(term)
    result = parse_expected_binding_v1(codec_expected_binding_v1(binding))
    assert type(result) is KEB1DecodedResultV1
    assert result.value == binding


def test_list_roundtrip() -> None:
    term = kernel_term_v1(KernelTermTagV1.CTOR, b"d" * 32, 3, (_var(1), _var(2)))
    binding = expected_binding_v1(term)
    result = parse_expected_binding_v1(codec_expected_binding_v1(binding))
    assert type(result) is KEB1DecodedResultV1
    assert result.value == binding


def test_forged_expected_wire_is_dependency_not_authority() -> None:
    term = _var()
    forged = ExpectedBindingSyntaxV1(term, b"X")
    payload = codec_kernel_proof_term_v1(term)
    with pytest.raises(KEB1DecodeError) as info:
        codec_expected_binding_v1(forged)
    assert (info.value.code, info.value.absolute_offset) == (
        KEB1DecodeCodeV1.DEPENDENCY, 22 + len(payload),
    )


@pytest.mark.parametrize(
    ("changes", "kind", "allowed", "required", "offset"),
    (
        ({"max_output_bytes": 65}, KEB1ResourceKindV1.OUTPUT_BYTES, 65, 66, 0),
        ({"max_nested_kpt_bytes": 21}, KEB1ResourceKindV1.NESTED_KPT_BYTES, 21, 22, 14),
        ({"max_expected_wire_bytes": 21}, KEB1ResourceKindV1.EXPECTED_WIRE_BYTES, 21, 22, 44),
        ({"max_composite_nodes": 1}, KEB1ResourceKindV1.COMPOSITE_NODES, 1, 2, 14),
    ),
)
def test_exact_local_and_node_resources(changes, kind, allowed, required, offset) -> None:
    binding = expected_binding_v1(_var())
    with pytest.raises(KEB1ResourceLimit) as info:
        codec_expected_binding_v1(binding, _limits(**changes))
    assert (info.value.kind, info.value.allowed, info.value.required, info.value.absolute_offset) == (kind, allowed, required, offset)


def test_exact_composite_depth_plus_one() -> None:
    child = _var()
    term = kernel_term_v1(KernelTermTagV1.FST, child)
    raw = _wire(term)
    payload = codec_kernel_proof_term_v1(term)
    child_start = 6 + 8
    result = parse_expected_binding_v1(raw, _limits(max_composite_depth=1))
    assert type(result) is KEB1ResourceParseResultV1
    assert result.resource.kind is KEB1ResourceKindV1.COMPOSITE_DEPTH
    assert (result.resource.allowed, result.resource.required, result.resource.absolute_offset) == (1, 2, 14 + child_start)
    assert len(payload) > child_start


def test_exact_list_count_resource_locus() -> None:
    term = kernel_term_v1(KernelTermTagV1.CTOR, b"d" * 32, 0, (_var(), _var(1)))
    payload = codec_kernel_proof_term_v1(term)
    list_lp = 6 + (8 + 32) + (8 + 8)
    list_start = list_lp + 8
    result = parse_expected_binding_v1(_wire(term), _limits(max_kpt_list_items=1))
    assert type(result) is KEB1ResourceParseResultV1
    assert (result.resource.kind, result.resource.allowed, result.resource.required, result.resource.absolute_offset) == (
        KEB1ResourceKindV1.KPT_LIST_ITEMS, 1, 2, 14 + list_start,
    )
    assert int.from_bytes(payload[list_start:list_start + 8], "big") == 2


def test_exact_nat_magnitude_resource_locus() -> None:
    term = _var(256)
    payload = codec_kernel_proof_term_v1(term)
    magnitude_start = 6 + 8 + 8
    result = parse_expected_binding_v1(_wire(term), _limits(max_kpt_nat_bytes=1))
    assert type(result) is KEB1ResourceParseResultV1
    assert (result.resource.kind, result.resource.allowed, result.resource.required, result.resource.absolute_offset) == (
        KEB1ResourceKindV1.KPT_NAT_BYTES, 1, 2, 14 + magnitude_start,
    )
    assert payload[magnitude_start:] == b"\x01\x00"


def test_input_cap_is_first_and_has_exact_boundary_locus() -> None:
    raw = _wire(_var())
    result = parse_expected_binding_v1(raw, _limits(max_input_bytes=len(raw) - 1))
    assert type(result) is KEB1ResourceParseResultV1
    assert (result.resource.kind, result.resource.allowed, result.resource.required, result.resource.absolute_offset) == (
        KEB1ResourceKindV1.INPUT_BYTES, len(raw) - 1, len(raw), len(raw) - 1,
    )
