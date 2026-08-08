"""Hostile grammar, first-offset and immutable-boundary pressure for KCA1."""

from __future__ import annotations

import pytest

from src.core.omegaa_kca1_codec import codec_kernel_checker_ast_v1
from src.core.omegaa_kca1_common import (
    KCA1DecodeCodeV1,
    KCA1DecodeError,
    KCA1LimitsV1,
    KCA1ResourceLimit,
)
from src.core.omegaa_kca1_parser import parse_kernel_checker_ast_v1
from src.core.omegaa_kca1_types import (
    KCA1_ARITIES,
    KCA1_FIELD_KINDS,
    EqualityModeV1,
    KernelCheckerASTV1,
    KernelCheckerTagV1,
    ParseModeV1,
    QuoteModeV1,
    kernel_checker_ast_v1,
)
from src.core.omegaa_kpt1_codec import codec_kernel_proof_term_v1
from src.core.omegaa_kpt1_common import KPT1DecodeCodeV1, KPT1DecodeError
from src.core.omegaa_kpt1_parser import parse_kernel_proof_term_v1
from src.core.omegaa_kpt1_types import KernelTermTagV1, kernel_term_v1

_IN_PLACE_HOOK_CALLS: list[str] = []


def _in_place_post_init_bomb(self: object) -> None:
    _IN_PLACE_HOOK_CALLS.append(type(self).__name__)


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "big")


def _frame(payload: bytes) -> bytes:
    return _u64(len(payload)) + payload


def _leaf(payload: bytes = b"tags") -> KernelCheckerASTV1:
    return kernel_checker_ast_v1(
        KernelCheckerTagV1.PARSE_CANON, payload, ParseModeV1.CANON_FRAME_LTR_EXACT_END,
    )


def _assert_decode(raw: bytes, code: KCA1DecodeCodeV1, offset: int) -> None:
    with pytest.raises(KCA1DecodeError) as caught:
        parse_kernel_checker_ast_v1(raw)
    assert (caught.value.code, caught.value.offset) == (code, offset)


def test_kpt1_and_kca1_are_bidirectionally_prefix_disjoint() -> None:
    kca = codec_kernel_checker_ast_v1(_leaf())
    with pytest.raises(KPT1DecodeError) as kpt_error:
        parse_kernel_proof_term_v1(kca)
    assert (kpt_error.value.code, kpt_error.value.offset) == (KPT1DecodeCodeV1.BAD_VERSION, 1)
    kpt = codec_kernel_proof_term_v1(kernel_term_v1(KernelTermTagV1.VAR, 0))
    _assert_decode(kpt, KCA1DecodeCodeV1.BAD_VERSION, 1)


def test_unknown_tag_wrong_arity_short_frame_and_trailing_are_first_offset() -> None:
    raw = codec_kernel_checker_ast_v1(_leaf())
    _assert_decode(raw[:4] + b"\xff" + raw[5:], KCA1DecodeCodeV1.BAD_TAG, 4)
    _assert_decode(raw[:5] + b"\x03" + raw[6:], KCA1DecodeCodeV1.BAD_ARITY, 5)
    _assert_decode(b"KCA1\x01\x02\x00", KCA1DecodeCodeV1.BAD_LENGTH, 6)
    _assert_decode(raw + b"\x00", KCA1DecodeCodeV1.TRAILING, len(raw))


def test_child_failure_precedes_later_bad_frame_and_mode_is_closed() -> None:
    child = bytearray(codec_kernel_checker_ast_v1(_leaf()))
    child[0] = ord("X")
    parent = b"KCA1\x03\x04" + _frame(bytes(child)) + _u64(999)
    _assert_decode(parent, KCA1DecodeCodeV1.BAD_VERSION, 14)
    raw = bytearray(codec_kernel_checker_ast_v1(_leaf()))
    mode_offset = len(raw) - 1
    raw[mode_offset] = 1
    _assert_decode(bytes(raw), KCA1DecodeCodeV1.BAD_ORDER, mode_offset)


def test_noncanonical_nat_and_bad_utf8_rule_leaf_are_rejected() -> None:
    failed = b"KCA1\x07\x02" + _frame(b"\x09") + _frame(_frame(b"\x00"))
    _assert_decode(failed, KCA1DecodeCodeV1.NONCANONICAL_NAT, 31)
    raw = b"KCA1\x01\x02" + _frame(b"\xff") + _frame(b"\x00")
    _assert_decode(raw, KCA1DecodeCodeV1.BAD_ORDER, 14)


def test_nat_reports_earlier_noncanonical_byte_before_later_trailing_byte() -> None:
    compound = (
        b"KCA1\x07\x02" + _frame(b"\x09")
        + _frame(_frame(b"\x00") + b"\x00")
    )
    _assert_decode(compound, KCA1DecodeCodeV1.NONCANONICAL_NAT, 31)


def test_public_grammar_rebinding_cannot_change_constructor_parser_or_encoder() -> None:
    import src.core.omegaa_kca1_types as syntax

    ast = _leaf()
    raw = codec_kernel_checker_ast_v1(ast)
    old_fields, old_arities = syntax.KCA1_FIELD_KINDS, syntax.KCA1_ARITIES
    syntax.KCA1_FIELD_KINDS, syntax.KCA1_ARITIES = {}, {}  # type: ignore[assignment]
    try:
        with pytest.raises(ValueError, match="ast-arity"):
            KernelCheckerASTV1(KernelCheckerTagV1.PARSE_CANON, ())
        assert codec_kernel_checker_ast_v1(ast) == raw
        assert parse_kernel_checker_ast_v1(raw) == ast
    finally:
        syntax.KCA1_FIELD_KINDS, syntax.KCA1_ARITIES = old_fields, old_arities


def test_mapping_proxies_and_slot_descriptor_guard_are_immutable() -> None:
    with pytest.raises(TypeError):
        KCA1_FIELD_KINDS[KernelCheckerTagV1.FAIL] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        KCA1_ARITIES[KernelCheckerTagV1.FAIL] = 0  # type: ignore[index]
    ast = _leaf()
    raw = codec_kernel_checker_ast_v1(ast)
    original = vars(KernelCheckerASTV1)["tag"]
    calls = 0

    class Bomb:
        def __get__(self, instance: object, owner: object) -> object:
            nonlocal calls
            calls += 1
            raise AssertionError("must not execute")

    setattr(KernelCheckerASTV1, "tag", Bomb())
    try:
        with pytest.raises(ValueError, match="descriptor-integrity"):
            codec_kernel_checker_ast_v1(ast)
        with pytest.raises(ValueError, match="ast-constructor-integrity"):
            parse_kernel_checker_ast_v1(raw)
        assert calls == 0
    finally:
        setattr(KernelCheckerASTV1, "tag", original)


def test_parser_never_executes_mutated_init_or_post_init() -> None:
    raw = codec_kernel_checker_ast_v1(_leaf())
    originals = (
        vars(KernelCheckerASTV1)["__init__"],
        vars(KernelCheckerASTV1)["__post_init__"],
    )
    calls = 0

    def bomb(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        raise AssertionError("must not execute")

    for name, original in zip(("__init__", "__post_init__"), originals, strict=True):
        setattr(KernelCheckerASTV1, name, bomb)
        try:
            with pytest.raises(ValueError, match="ast-constructor-integrity"):
                parse_kernel_checker_ast_v1(raw)
            assert calls == 0
        finally:
            setattr(KernelCheckerASTV1, name, original)


def test_parser_never_executes_in_place_mutated_post_init_code() -> None:
    raw = codec_kernel_checker_ast_v1(_leaf())
    hook = vars(KernelCheckerASTV1)["__post_init__"]
    original_code = hook.__code__
    _IN_PLACE_HOOK_CALLS.clear()
    hook.__code__ = _in_place_post_init_bomb.__code__
    try:
        parsed = parse_kernel_checker_ast_v1(raw)
        assert parsed.tag is KernelCheckerTagV1.PARSE_CANON
        assert parsed.fields[0] == b"tags"
        assert _IN_PLACE_HOOK_CALLS == []
    finally:
        hook.__code__ = original_code


def test_parser_rejects_live_class_rebinding_without_calling_replacement() -> None:
    import src.core.omegaa_kca1_parser as parser

    raw = codec_kernel_checker_ast_v1(_leaf())
    original = getattr(parser, "KernelCheckerASTV1")
    calls = 0

    def bomb(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("must not execute")

    setattr(parser, "KernelCheckerASTV1", bomb)
    try:
        with pytest.raises(ValueError, match="ast-constructor-integrity"):
            parse_kernel_checker_ast_v1(raw)
        assert calls == 0
    finally:
        setattr(parser, "KernelCheckerASTV1", original)


def test_tag_and_mode_enum_mutation_are_rejected() -> None:
    ast = _leaf()
    raw = codec_kernel_checker_ast_v1(ast)
    tag_value = KernelCheckerTagV1.PARSE_CANON.value
    object.__setattr__(KernelCheckerTagV1.PARSE_CANON, "_value_", 7)
    try:
        with pytest.raises(ValueError, match="tag-enum-ordinal-integrity"):
            codec_kernel_checker_ast_v1(ast)
    finally:
        object.__setattr__(KernelCheckerTagV1.PARSE_CANON, "_value_", tag_value)
    mode_value = ParseModeV1.CANON_FRAME_LTR_EXACT_END.value
    object.__setattr__(ParseModeV1.CANON_FRAME_LTR_EXACT_END, "_value_", 1)
    try:
        with pytest.raises(ValueError, match="mode-enum-ordinal-integrity"):
            parse_kernel_checker_ast_v1(raw)
    finally:
        object.__setattr__(ParseModeV1.CANON_FRAME_LTR_EXACT_END, "_value_", mode_value)


def test_partial_subclass_bool_cycle_and_shared_graph_are_rejected() -> None:
    with pytest.raises(ValueError):
        kernel_checker_ast_v1(KernelCheckerTagV1.RETURN, True, b"")
    partial = object.__new__(KernelCheckerASTV1)
    with pytest.raises(ValueError, match="invalid-ast-tag"):
        codec_kernel_checker_ast_v1(partial)

    class Subclass(KernelCheckerASTV1):
        pass

    with pytest.raises(ValueError, match="ast-host-shape"):
        codec_kernel_checker_ast_v1(object.__new__(Subclass))
    cyclic = _leaf()
    object.__setattr__(cyclic, "tag", KernelCheckerTagV1.PROGRAM)
    object.__setattr__(cyclic, "fields", (cyclic,) * 5)
    with pytest.raises(ValueError, match="cyclic-host-graph"):
        codec_kernel_checker_ast_v1(cyclic)
    child = _leaf()
    shared = kernel_checker_ast_v1(
        KernelCheckerTagV1.PROGRAM, child, child, child, child, child,
    )
    with pytest.raises(ValueError, match="shared-host-graph"):
        codec_kernel_checker_ast_v1(shared)


def test_limit_slot_mutation_and_resource_caps_fail_closed() -> None:
    limits = KCA1LimitsV1()
    original = vars(KCA1LimitsV1)["max_depth"]
    setattr(KCA1LimitsV1, "max_depth", property(lambda self: 999))
    try:
        with pytest.raises(ValueError, match="limits-host-shape"):
            codec_kernel_checker_ast_v1(_leaf(), limits)
    finally:
        setattr(KCA1LimitsV1, "max_depth", original)
    object.__setattr__(limits, "max_depth", 999)
    with pytest.raises(ValueError, match="limits-unsafe-depth"):
        codec_kernel_checker_ast_v1(_leaf(), limits)
    raw = codec_kernel_checker_ast_v1(_leaf())
    with pytest.raises(KCA1ResourceLimit, match="max_input_bytes"):
        parse_kernel_checker_ast_v1(raw, KCA1LimitsV1(max_input_bytes=len(raw) - 1))
    with pytest.raises(KCA1ResourceLimit, match="max_output_bytes"):
        parse_kernel_checker_ast_v1(raw, KCA1LimitsV1(max_output_bytes=len(raw) - 1))
    with pytest.raises(KCA1ResourceLimit, match="max_output_bytes"):
        codec_kernel_checker_ast_v1(_leaf(b"x" * 20), KCA1LimitsV1(max_output_bytes=20))
    failed = kernel_checker_ast_v1(KernelCheckerTagV1.FAIL, KCA1DecodeCodeV1.BAD_TAG, 256)
    with pytest.raises(KCA1ResourceLimit, match="max_nat_bytes"):
        codec_kernel_checker_ast_v1(failed, KCA1LimitsV1(max_nat_bytes=1))
    failed_raw = codec_kernel_checker_ast_v1(failed)
    with pytest.raises(KCA1ResourceLimit, match="max_nat_bytes"):
        parse_kernel_checker_ast_v1(failed_raw, KCA1LimitsV1(max_nat_bytes=1))


def test_ast_depth_and_node_bombs_are_bounded_before_encoding() -> None:
    inner = kernel_checker_ast_v1(
        KernelCheckerTagV1.CHECK, _leaf(), _leaf(),
        QuoteModeV1.ETA_LONG_DEBRUIJN_LEVEL, EqualityModeV1.UNSIGNED_EXACT_BYTES,
    )
    outer = kernel_checker_ast_v1(
        KernelCheckerTagV1.CHECK, inner, _leaf(),
        QuoteModeV1.ETA_LONG_DEBRUIJN_LEVEL, EqualityModeV1.UNSIGNED_EXACT_BYTES,
    )
    with pytest.raises(KCA1ResourceLimit, match="max_depth"):
        codec_kernel_checker_ast_v1(outer, KCA1LimitsV1(max_depth=1))
    many = kernel_checker_ast_v1(
        KernelCheckerTagV1.PROGRAM, _leaf(), _leaf(), _leaf(), _leaf(), _leaf(),
    )
    with pytest.raises(KCA1ResourceLimit, match="max_nodes"):
        codec_kernel_checker_ast_v1(many, KCA1LimitsV1(max_nodes=5))
