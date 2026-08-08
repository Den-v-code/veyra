"""Focused KIE1 binding, inspection, byte-difference, and coordinate tests."""

from __future__ import annotations

from itertools import product
import random
from typing import Callable, cast

import pytest

from src.core.omegaa_kci1_builder import build_checker_input_syntax_v1
from src.core.omegaa_kci1_types import CheckerInputSyntaxV1
from src.core.omegaa_keb1_builder import expected_binding_v1
from src.core.omegaa_keb1_common import FirstUnsignedDifferenceV1 as keb_first_diff
from src.core.omegaa_keb1_types import ExpectedBindingSyntaxV1
from src.core.omegaa_kie1_binding import BindExpectedInputV1
from src.core.omegaa_kie1_common import (
    KIE1IntegrityErrorV1,
    KIEPayloadOriginV1,
    KIEPrepareCodeV1,
)
from src.core.omegaa_kie1_offsets import (
    FirstUnsignedDifferenceV1,
    RebaseKPTV1,
    RebaseSuppliedSemanticOriginV1,
)
from src.core.omegaa_kie1_prepare import InspectKIEPrepareResultV1
from src.core.omegaa_kie1_types import (
    BoundExpectedInputV1,
    KIEKPTDecodeAtInputV1,
    KIEPrepareErrorV1,
    _KIEBoundResultV1,
    _KIEBoundViewV1,
    _KIEErrorViewV1,
    _KIEInitErrorResultV1,
)
from src.core.omegaa_kpt1_common import KPT1DecodeCodeV1
from src.core.omegaa_kpt1_types import KernelTermTagV1, kernel_term_v1


def _binding() -> ExpectedBindingSyntaxV1:
    return expected_binding_v1(kernel_term_v1(KernelTermTagV1.VAR, 0))


def _input(expected: bytes, term: bytes = b"opaque-term") -> CheckerInputSyntaxV1:
    return build_checker_input_syntax_v1(expected, term)


def _oracle(left: bytes, right: bytes) -> int | None:
    stop = min(len(left), len(right))
    for index in range(stop):
        if left[index] != right[index]:
            return index
    if len(left) != len(right):
        return stop
    return None


def test_equal_prepare_and_inspect_are_fresh_inert_shapes() -> None:
    binding = _binding()
    input_value = _input(binding.expected_wire)
    first = BindExpectedInputV1(input_value, binding)
    second = BindExpectedInputV1(input_value, binding)
    assert type(first) is type(second) is _KIEBoundResultV1
    first_bound = first
    second_bound = second
    assert first_bound is not second_bound and first_bound.bound is not second_bound.bound
    assert type(first_bound.bound) is BoundExpectedInputV1
    assert first_bound.bound.input is input_value and first_bound.bound.binding is binding
    first_view = InspectKIEPrepareResultV1(first)
    second_view = InspectKIEPrepareResultV1(first)
    assert type(first_view) is type(second_view) is _KIEBoundViewV1
    assert first_view is not second_view
    bound_view = first_view
    assert bound_view.input is input_value and bound_view.binding is binding


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("mutator", "difference"),
    (
        (lambda wire: bytes((wire[0] ^ 1,)) + wire[1:], 0),
        (lambda wire: wire[:5] + bytes((wire[5] ^ 1,)) + wire[6:], 5),
        (lambda wire: wire + b"x", None),
        (lambda wire: wire[:-1], None),
    ),
)
def test_mismatch_is_normal_and_has_exact_kci_offset(
    mutator: Callable[[bytes], bytes], difference: int | None,
) -> None:
    binding = _binding()
    changed = mutator(binding.expected_wire)
    actual_difference = _oracle(changed, binding.expected_wire)
    assert actual_difference is not None
    if difference is not None:
        assert actual_difference == difference
    result = BindExpectedInputV1(_input(changed), binding)
    assert type(result) is _KIEInitErrorResultV1
    error_result = result
    assert type(error_result.error) is KIEPrepareErrorV1
    assert error_result.error.code is KIEPrepareCodeV1.EXPECTED_WIRE_MISMATCH
    assert error_result.error.absolute_kci_offset == 14 + actual_difference
    view = InspectKIEPrepareResultV1(error_result)
    assert type(view) is _KIEErrorViewV1
    assert view.original_error is error_result.error


def test_exhaustive_and_seeded_first_difference_oracles_match_both_implementations() -> None:
    values = tuple(
        bytes(items)
        for length in range(3)
        for items in product((0, 1, 255), repeat=length)
    )
    for left in values:
        for right in values:
            expected = _oracle(left, right)
            assert FirstUnsignedDifferenceV1(left, right) == expected
            assert keb_first_diff(left, right) == expected
    generator = random.Random(0x4B494531)
    for _ in range(512):
        left = generator.randbytes(generator.randrange(0, 65))
        right = generator.randbytes(generator.randrange(0, 65))
        expected = _oracle(left, right)
        assert FirstUnsignedDifferenceV1(left, right) == expected
        assert keb_first_diff(left, right) == expected


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "code", tuple(KPT1DecodeCodeV1(index) for index in range(11)),
)
def test_kpt_decode_identity_and_exact_coordinate_rebase(code: KPT1DecodeCodeV1) -> None:
    expected = b"abcde"
    expected_result = RebaseKPTV1(KIEPayloadOriginV1.EXPECTED, (code, 7), expected)
    term_result = RebaseKPTV1(KIEPayloadOriginV1.TERM, (code, 7), expected)
    assert type(expected_result) is type(term_result) is KIEKPTDecodeAtInputV1
    assert expected_result.code is term_result.code is code
    assert expected_result.absolute_kci_offset == 14 + 7
    assert term_result.absolute_kci_offset == 22 + len(expected) + 7
    assert expected_result is not RebaseKPTV1(KIEPayloadOriginV1.EXPECTED, (code, 7), expected)


def test_supplied_semantic_origin_is_only_checked_arithmetic() -> None:
    expected = b"abcd"
    assert RebaseSuppliedSemanticOriginV1(KIEPayloadOriginV1.EXPECTED, 4, expected) == 18
    assert RebaseSuppliedSemanticOriginV1(KIEPayloadOriginV1.TERM, 4, expected) == 30
    with pytest.raises(KIE1IntegrityErrorV1, match="overflow"):
        RebaseSuppliedSemanticOriginV1(KIEPayloadOriginV1.TERM, 2**64 - 1, expected)


def test_exact_host_types_and_tuple_are_required_for_offsets() -> None:
    with pytest.raises(KIE1IntegrityErrorV1):
        FirstUnsignedDifferenceV1(bytearray(), b"")  # type: ignore[arg-type]
    with pytest.raises(KIE1IntegrityErrorV1):
        RebaseKPTV1(KIEPayloadOriginV1.EXPECTED, [KPT1DecodeCodeV1.BAD_TAG, 0], b"")  # type: ignore[arg-type]
    with pytest.raises(KIE1IntegrityErrorV1):
        RebaseKPTV1(KIEPayloadOriginV1.EXPECTED, (KPT1DecodeCodeV1.BAD_TAG, True), b"")
    with pytest.raises(KIE1IntegrityErrorV1):
        RebaseSuppliedSemanticOriginV1(0, 0, b"")  # type: ignore[arg-type]


def test_prepare_and_views_make_no_provenance_or_authority_claim() -> None:
    binding = _binding()
    result = BindExpectedInputV1(_input(binding.expected_wire), binding)
    view = InspectKIEPrepareResultV1(result)
    assert type(view) is _KIEBoundViewV1
    bound_result = cast(_KIEBoundResultV1, result)
    for value in (result, bound_result.bound, view):
        assert not hasattr(value, "proof")
        assert not hasattr(value, "authority")
        assert not hasattr(value, "run")
        assert not hasattr(value, "provenance")
