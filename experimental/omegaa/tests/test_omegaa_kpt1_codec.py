"""Focused byte-oracle and round-trip tests for the non-positive KPT1 slice."""

from __future__ import annotations

import pytest

from src.core.omegaa_kpt1_codec import KPT1_PREFIX, codec_kernel_proof_term_v1
from src.core.omegaa_kpt1_parser import parse_kernel_proof_term_v1
from src.core.omegaa_kpt1_types import (
    KernelProofTermV1,
    KernelTermTagV1,
    kernel_term_v1,
    max_level_v1,
    succ_level_v1,
    zero_level_v1,
)


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "big")


def _frame(payload: bytes) -> bytes:
    return _u64(len(payload)) + payload


def _all_terms() -> tuple[KernelProofTermV1, ...]:
    var = kernel_term_v1(KernelTermTagV1.VAR, 0)
    sort = kernel_term_v1(KernelTermTagV1.SORT, zero_level_v1())
    digest = bytes(range(32))
    return (
        var,
        sort,
        kernel_term_v1(KernelTermTagV1.PI, sort, sort),
        kernel_term_v1(KernelTermTagV1.LAM, sort, var),
        kernel_term_v1(KernelTermTagV1.APP, var, var),
        kernel_term_v1(KernelTermTagV1.SIGMA, sort, sort),
        kernel_term_v1(KernelTermTagV1.PAIR, var, var),
        kernel_term_v1(KernelTermTagV1.FST, var),
        kernel_term_v1(KernelTermTagV1.SND, var),
        kernel_term_v1(KernelTermTagV1.LET, sort, var, var),
        kernel_term_v1(KernelTermTagV1.CONST, digest),
        kernel_term_v1(KernelTermTagV1.CTOR, digest, 3, (var,)),
        kernel_term_v1(KernelTermTagV1.REC, digest, sort, (var, sort), var),
        kernel_term_v1(KernelTermTagV1.EQ, sort, var, var),
        kernel_term_v1(KernelTermTagV1.REFL, var),
        kernel_term_v1(KernelTermTagV1.J, sort, var, sort, var, var, var),
    )


def test_var_zero_has_exact_nested_nat_framing() -> None:
    term = kernel_term_v1(KernelTermTagV1.VAR, 0)
    expected = KPT1_PREFIX + b"\x00\x01" + _frame(_frame(b""))
    assert codec_kernel_proof_term_v1(term) == expected


def test_var_256_uses_minimal_unsigned_big_endian_magnitude() -> None:
    term = kernel_term_v1(KernelTermTagV1.VAR, 256)
    expected = KPT1_PREFIX + b"\x00\x01" + _frame(_frame(b"\x01\x00"))
    assert codec_kernel_proof_term_v1(term) == expected


def test_universe_level_zero_succ_max_has_exact_framing() -> None:
    zero = b"\x00"
    succ_zero = b"\x01" + _frame(zero)
    maximum = b"\x02" + _frame(zero) + _frame(succ_zero)
    term = kernel_term_v1(
        KernelTermTagV1.SORT,
        max_level_v1(zero_level_v1(), succ_level_v1(zero_level_v1())),
    )
    expected = KPT1_PREFIX + b"\x01\x01" + _frame(maximum)
    assert codec_kernel_proof_term_v1(term) == expected


@pytest.mark.parametrize("term", _all_terms())
def test_all_sixteen_exact_tags_round_trip_canonically(term: KernelProofTermV1) -> None:
    encoded = codec_kernel_proof_term_v1(term)
    assert encoded[:4] == KPT1_PREFIX
    assert encoded[4] == term.tag.value
    assert parse_kernel_proof_term_v1(encoded) == term
    assert codec_kernel_proof_term_v1(parse_kernel_proof_term_v1(encoded)) == encoded


def test_term_list_is_count_then_individually_framed_kpt1_nodes() -> None:
    child = kernel_term_v1(KernelTermTagV1.VAR, 0)
    digest = b"d" * 32
    term = kernel_term_v1(KernelTermTagV1.CTOR, digest, 1, (child, child))
    encoded = codec_kernel_proof_term_v1(term)
    child_bytes = codec_kernel_proof_term_v1(child)
    fields = _frame(digest) + _frame(_frame(b"\x01"))
    fields += _frame(_u64(2) + _frame(child_bytes) + _frame(child_bytes))
    assert encoded == KPT1_PREFIX + b"\x0b\x03" + fields
