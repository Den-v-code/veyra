"""Hostile boundary, resource-cap and first-offset tests for KPT1."""

from __future__ import annotations

import pytest

from src.core.omegaa_kpt1_codec import (
    KPT1DecodeCodeV1,
    KPT1DecodeError,
    KPT1LimitsV1,
    KPT1ResourceLimit,
    codec_kernel_proof_term_v1,
)
from src.core.omegaa_kpt1_parser import parse_kernel_proof_term_v1
from src.core.omegaa_kpt1_types import (
    KPT1_ARITIES,
    KPT1_FIELD_KINDS,
    KPT1ValidationError,
    KernelProofTermV1,
    KernelTermTagV1,
    kernel_term_v1,
)


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "big")


def _frame(payload: bytes) -> bytes:
    return _u64(len(payload)) + payload


def _var(value: int = 0) -> KernelProofTermV1:
    return kernel_term_v1(KernelTermTagV1.VAR, value)


def _assert_decode(raw: bytes, code: KPT1DecodeCodeV1, offset: int) -> None:
    with pytest.raises(KPT1DecodeError) as caught:
        parse_kernel_proof_term_v1(raw)
    assert (caught.value.code, caught.value.offset) == (code, offset)


def test_rejects_bad_prefix_at_first_differing_offset_and_kca1_is_disjoint() -> None:
    raw = codec_kernel_proof_term_v1(_var())
    _assert_decode(b"KCA1" + raw[4:], KPT1DecodeCodeV1.BAD_VERSION, 1)
    _assert_decode(b"X" + raw[1:], KPT1DecodeCodeV1.BAD_VERSION, 0)


def test_rejects_unknown_tag_wrong_arity_and_short_prefix() -> None:
    raw = codec_kernel_proof_term_v1(_var())
    _assert_decode(raw[:4] + b"\xff" + raw[5:], KPT1DecodeCodeV1.BAD_TAG, 4)
    _assert_decode(b"KPT1\xff", KPT1DecodeCodeV1.BAD_TAG, 4)
    _assert_decode(raw[:5] + b"\x02" + raw[6:], KPT1DecodeCodeV1.BAD_ARITY, 5)
    _assert_decode(b"KPT", KPT1DecodeCodeV1.BAD_LENGTH, 3)


def test_rejects_bad_frame_nonminimal_nat_and_trailing_bytes() -> None:
    _assert_decode(b"KPT1\x00\x01\x00", KPT1DecodeCodeV1.BAD_LENGTH, 6)
    nonminimal = b"KPT1\x00\x01" + _frame(_frame(b"\x00"))
    _assert_decode(nonminimal, KPT1DecodeCodeV1.NONCANONICAL_NAT, 22)
    raw = codec_kernel_proof_term_v1(_var())
    _assert_decode(raw + b"\x00", KPT1DecodeCodeV1.TRAILING, len(raw))


def test_rejects_trailing_inside_framed_child() -> None:
    child = codec_kernel_proof_term_v1(_var())
    raw = b"KPT1\x07\x01" + _frame(child + b"\x00")
    _assert_decode(raw, KPT1DecodeCodeV1.TRAILING, 14 + len(child))


def test_first_child_failure_precedes_later_bad_frame_header() -> None:
    child = bytearray(codec_kernel_proof_term_v1(_var()))
    child[0] = ord("X")
    raw = b"KPT1\x02\x02" + _frame(bytes(child)) + _u64(999)
    _assert_decode(raw, KPT1DecodeCodeV1.BAD_VERSION, 14)


def test_digest_must_be_exactly_32_bytes() -> None:
    raw = b"KPT1\x0a\x01" + _frame(b"d" * 31)
    _assert_decode(raw, KPT1DecodeCodeV1.BAD_LENGTH, 14)


def test_parser_rejects_host_substitutions_before_wire_work() -> None:
    with pytest.raises(TypeError):
        parse_kernel_proof_term_v1(bytearray(codec_kernel_proof_term_v1(_var())))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="limits-host-shape"):
        parse_kernel_proof_term_v1(b"", object())  # type: ignore[arg-type]


def test_frozen_tag_tables_and_safe_recursive_depth_ceiling() -> None:
    with pytest.raises(TypeError):
        KPT1_FIELD_KINDS[KernelTermTagV1.VAR] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        KPT1_ARITIES[KernelTermTagV1.VAR] = 0  # type: ignore[index]
    with pytest.raises(ValueError, match="safe recursion depth"):
        KPT1LimitsV1(max_depth=129)


def test_public_table_rebinding_cannot_change_constructor_or_parser_semantics() -> None:
    import src.core.omegaa_kpt1_types as syntax

    raw = codec_kernel_proof_term_v1(_var())
    original_fields = syntax.KPT1_FIELD_KINDS
    original_arities = syntax.KPT1_ARITIES
    syntax.KPT1_FIELD_KINDS = {}  # type: ignore[assignment]
    syntax.KPT1_ARITIES = {}  # type: ignore[assignment]
    try:
        with pytest.raises(KPT1ValidationError, match="term-arity"):
            KernelProofTermV1(KernelTermTagV1.VAR, ())
        assert parse_kernel_proof_term_v1(raw) == _var()
    finally:
        syntax.KPT1_FIELD_KINDS = original_fields
        syntax.KPT1_ARITIES = original_arities


def test_live_enum_value_mutation_is_rejected_before_term_or_level_wire_use() -> None:
    term = _var()
    raw = codec_kernel_proof_term_v1(term)
    term_value = KernelTermTagV1.VAR.value
    object.__setattr__(KernelTermTagV1.VAR, "_value_", 7)
    try:
        with pytest.raises(KPT1ValidationError, match="enum-ordinal-integrity"):
            codec_kernel_proof_term_v1(term)
        with pytest.raises(KPT1ValidationError, match="enum-ordinal-integrity"):
            parse_kernel_proof_term_v1(raw)
    finally:
        object.__setattr__(KernelTermTagV1.VAR, "_value_", term_value)

    from src.core.omegaa_kpt1_types import KernelLevelTagV1, zero_level_v1

    level_value = KernelLevelTagV1.ZERO.value
    object.__setattr__(KernelLevelTagV1.ZERO, "_value_", 2)
    try:
        with pytest.raises(KPT1ValidationError, match="enum-ordinal-integrity"):
            zero_level_v1()
    finally:
        object.__setattr__(KernelLevelTagV1.ZERO, "_value_", level_value)


def test_constructor_and_encoder_reject_bool_mutation_partial_and_subclass() -> None:
    with pytest.raises(KPT1ValidationError):
        _var(True)  # type: ignore[arg-type]
    term = _var()
    object.__setattr__(term, "fields", (True,))
    with pytest.raises(ValueError, match="nat-host-shape"):
        codec_kernel_proof_term_v1(term)
    partial = object.__new__(KernelProofTermV1)
    with pytest.raises(ValueError, match="invalid-term-tag"):
        codec_kernel_proof_term_v1(partial)

    class TermSubclass(KernelProofTermV1):
        pass

    hostile = object.__new__(TermSubclass)
    with pytest.raises(ValueError, match="term-host-shape"):
        codec_kernel_proof_term_v1(hostile)


def test_encoder_rejects_cycles_without_recursing() -> None:
    term = kernel_term_v1(KernelTermTagV1.REFL, _var())
    object.__setattr__(term, "fields", (term,))
    with pytest.raises(ValueError, match="cyclic-host-graph"):
        codec_kernel_proof_term_v1(term)


def test_frozen_slot_descriptor_guard_does_not_execute_monkeypatch() -> None:
    term = _var()
    original = vars(KernelProofTermV1)["tag"]
    calls = 0

    class Bomb:
        def __get__(self, instance: object, owner: object) -> object:
            nonlocal calls
            calls += 1
            raise AssertionError("must not execute")

    setattr(KernelProofTermV1, "tag", Bomb())
    try:
        with pytest.raises(ValueError, match="descriptor integrity"):
            codec_kernel_proof_term_v1(term)
        assert calls == 0
    finally:
        setattr(KernelProofTermV1, "tag", original)


def test_limit_slot_guard_does_not_execute_monkeypatch() -> None:
    limits = KPT1LimitsV1()
    original = vars(KPT1LimitsV1)["max_depth"]
    calls = 0

    class Bomb:
        def __get__(self, instance: object, owner: object) -> object:
            nonlocal calls
            calls += 1
            raise AssertionError("must not execute")

    setattr(KPT1LimitsV1, "max_depth", Bomb())
    try:
        with pytest.raises(ValueError, match="limits-host-shape"):
            codec_kernel_proof_term_v1(_var(), limits)
        assert calls == 0
    finally:
        setattr(KPT1LimitsV1, "max_depth", original)


def test_mutated_limit_instance_cannot_bypass_safe_recursion_ceiling() -> None:
    limits = KPT1LimitsV1()
    object.__setattr__(limits, "max_depth", 2000)
    with pytest.raises(ValueError, match="limits-unsafe-depth"):
        codec_kernel_proof_term_v1(_var(), limits)


@pytest.mark.parametrize(
    ("limits", "term", "limit"),
    (
        (KPT1LimitsV1(max_output_bytes=21), _var(), "max_output_bytes"),
        (KPT1LimitsV1(max_nat_bytes=1), _var(256), "max_nat_bytes"),
        (KPT1LimitsV1(max_depth=1), kernel_term_v1(KernelTermTagV1.FST, kernel_term_v1(KernelTermTagV1.FST, _var())), "max_depth"),
        (KPT1LimitsV1(max_nodes=1), kernel_term_v1(KernelTermTagV1.FST, _var()), "max_nodes"),
        (KPT1LimitsV1(max_list_items=1), kernel_term_v1(KernelTermTagV1.CTOR, b"d" * 32, 0, (_var(), _var())), "max_list_items"),
    ),
)
def test_encoder_resource_caps_are_hard(
    limits: KPT1LimitsV1, term: KernelProofTermV1, limit: str,
) -> None:
    with pytest.raises(KPT1ResourceLimit) as caught:
        codec_kernel_proof_term_v1(term, limits)
    assert caught.value.limit == limit


def test_decoder_input_depth_list_and_nat_caps_are_hard() -> None:
    raw = codec_kernel_proof_term_v1(_var())
    with pytest.raises(KPT1ResourceLimit, match="max_input_bytes"):
        parse_kernel_proof_term_v1(raw, KPT1LimitsV1(max_input_bytes=len(raw) - 1))
    with pytest.raises(KPT1ResourceLimit, match="max_output_bytes"):
        parse_kernel_proof_term_v1(raw, KPT1LimitsV1(max_output_bytes=len(raw) - 1))
    deep = kernel_term_v1(KernelTermTagV1.FST, kernel_term_v1(KernelTermTagV1.FST, _var()))
    with pytest.raises(KPT1ResourceLimit, match="max_depth"):
        parse_kernel_proof_term_v1(codec_kernel_proof_term_v1(deep), KPT1LimitsV1(max_depth=1))
    list_payload = _u64(2) + _frame(raw) + _frame(raw)
    ctor = b"KPT1\x0b\x03" + _frame(b"d" * 32) + _frame(_frame(b"")) + _frame(list_payload)
    with pytest.raises(KPT1ResourceLimit, match="max_list_items"):
        parse_kernel_proof_term_v1(ctor, KPT1LimitsV1(max_list_items=1))
    with pytest.raises(KPT1ResourceLimit, match="max_nat_bytes"):
        parse_kernel_proof_term_v1(codec_kernel_proof_term_v1(_var(256)), KPT1LimitsV1(max_nat_bytes=1))


def test_slice_exposes_no_checker_admission_release_or_capability() -> None:
    import src.core.omegaa_kpt1_codec as codec
    import src.core.omegaa_kpt1_parser as parser

    public = {name.lower() for module in (codec, parser) for name in vars(module) if not name.startswith("_")}
    assert not any(token in name for name in public for token in ("admission", "release", "capability", "checker"))
