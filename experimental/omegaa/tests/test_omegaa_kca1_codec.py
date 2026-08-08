"""Exact-byte and round-trip tests for non-executing KCA1 Slice A."""

from __future__ import annotations

import pytest

from src.core.omegaa_kca1_codec import codec_kernel_checker_ast_v1
from src.core.omegaa_kca1_common import KCA1DecodeCodeV1
from src.core.omegaa_kca1_parser import parse_kernel_checker_ast_v1
from src.core.omegaa_kca1_types import (
    ChildOrderV1,
    ContextModeV1,
    DeltaOrderV1,
    EqualityModeV1,
    FamilyOrderV1,
    FunctionObligationModeV1,
    KernelCheckerASTV1,
    KernelCheckerTagV1,
    ParseModeV1,
    ParseOrderV1,
    QuoteModeV1,
    RedexOrderV1,
    TerminalModeV1,
    TypeCheckModeV1,
    kernel_checker_ast_v1,
)


def _frame(payload: bytes) -> bytes:
    return len(payload).to_bytes(8, "big") + payload


def _wire(tag: int, *payloads: bytes) -> bytes:
    return b"KCA1" + bytes((tag, len(payloads))) + b"".join(_frame(item) for item in payloads)


def _parse() -> KernelCheckerASTV1:
    return kernel_checker_ast_v1(
        KernelCheckerTagV1.PARSE_CANON, b"term-tags", ParseModeV1.CANON_FRAME_LTR_EXACT_END,
    )


def _infer() -> KernelCheckerASTV1:
    return kernel_checker_ast_v1(
        KernelCheckerTagV1.INFER_MATCH, b"typing-rules",
        ChildOrderV1.PROPER_CHILDREN_LTR, DeltaOrderV1.STRICT_LOWER_FINITE_RANK,
        FamilyOrderV1.STRICT_POSITIVE_STRUCTURAL_REC,
    )


def _normalize() -> KernelCheckerASTV1:
    return kernel_checker_ast_v1(
        KernelCheckerTagV1.NORMALIZE_STEP, b"reduction-rules", b"substitution-rules",
        RedexOrderV1.LEFTMOST_OUTERMOST_BETA_ZETA_FST_SND_IOTA_DELTA_ETA,
    )


def _check() -> KernelCheckerASTV1:
    return kernel_checker_ast_v1(
        KernelCheckerTagV1.CHECK, _infer(), _normalize(),
        QuoteModeV1.ETA_LONG_DEBRUIJN_LEVEL, EqualityModeV1.UNSIGNED_EXACT_BYTES,
    )


def _entry() -> KernelCheckerASTV1:
    return kernel_checker_ast_v1(
        KernelCheckerTagV1.ENTRY, ParseOrderV1.EXPECTED_THEN_TERM,
        ContextModeV1.CLOSED, TypeCheckModeV1.INFERRED_TYPE_ID_EQUALS_EXPECTED_TYPE_ID,
        FunctionObligationModeV1.EXACT_TOTALITY_AND_EXTENSIONALITY_APPS,
        TerminalModeV1.ACCEPT_OR_FIRST_FAIL,
    )


def _program() -> KernelCheckerASTV1:
    return kernel_checker_ast_v1(
        KernelCheckerTagV1.PROGRAM, _parse(), _infer(), _check(), _normalize(), _entry(),
    )


def _all_tags() -> tuple[KernelCheckerASTV1, ...]:
    return (
        _program(), _parse(), _infer(), _check(), _normalize(), _entry(),
        kernel_checker_ast_v1(KernelCheckerTagV1.RETURN, 7, b"\xff\x00"),
        kernel_checker_ast_v1(KernelCheckerTagV1.FAIL, KCA1DecodeCodeV1.DEPENDENCY, 256),
    )


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "ast", _all_tags(), ids=lambda ast: ast.tag.name,
)
def test_all_eight_tags_roundtrip_and_reencode_exactly(ast: KernelCheckerASTV1) -> None:
    raw = codec_kernel_checker_ast_v1(ast)
    assert raw[:4] == b"KCA1"
    assert raw[4:6] == bytes((ast.tag.value, len(ast.fields)))
    parsed = parse_kernel_checker_ast_v1(raw)
    assert parsed == ast
    assert codec_kernel_checker_ast_v1(parsed) == raw


def test_return_and_fail_have_literal_exact_byte_oracles() -> None:
    returned = kernel_checker_ast_v1(KernelCheckerTagV1.RETURN, 7, b"\xff\x00")
    assert codec_kernel_checker_ast_v1(returned) == (
        b"KCA1\x06\x02" + _frame(b"\x07") + _frame(b"\xff\x00")
    )
    failed = kernel_checker_ast_v1(
        KernelCheckerTagV1.FAIL, KCA1DecodeCodeV1.DEPENDENCY, 256,
    )
    assert codec_kernel_checker_ast_v1(failed) == (
        b"KCA1\x07\x02" + _frame(b"\x09") + _frame(_frame(b"\x01\x00"))
    )


def test_all_six_structural_tags_have_independent_literal_wire_oracles() -> None:
    parse_wire = _wire(1, b"term-tags", b"\x00")
    infer_wire = _wire(2, b"typing-rules", b"\x00", b"\x00", b"\x00")
    normalize_wire = _wire(
        4, b"reduction-rules", b"substitution-rules", b"\x00",
    )
    check_wire = _wire(3, infer_wire, normalize_wire, b"\x00", b"\x00")
    entry_wire = _wire(5, b"\x00", b"\x00", b"\x00", b"\x00", b"\x00")
    program_wire = _wire(
        0, parse_wire, infer_wire, check_wire, normalize_wire, entry_wire,
    )
    rows = (
        (_program(), program_wire), (_parse(), parse_wire), (_infer(), infer_wire),
        (_check(), check_wire), (_normalize(), normalize_wire), (_entry(), entry_wire),
    )
    assert all(codec_kernel_checker_ast_v1(ast) == expected for ast, expected in rows)


def test_closed_mode_families_are_type_distinct_singletons() -> None:
    families = (
        ParseModeV1, ChildOrderV1, DeltaOrderV1, FamilyOrderV1, QuoteModeV1,
        EqualityModeV1, RedexOrderV1, ParseOrderV1, ContextModeV1,
        TypeCheckModeV1, FunctionObligationModeV1, TerminalModeV1,
    )
    assert all(len(family) == 1 and tuple(family)[0].value == 0 for family in families)
    assert len(set(families)) == len(families)


def test_utf8_rule_leaves_are_canonical_but_return_payload_is_opaque() -> None:
    with pytest.raises(ValueError, match="field-0-literal"):
        kernel_checker_ast_v1(
            KernelCheckerTagV1.PARSE_CANON, b"\xff", ParseModeV1.CANON_FRAME_LTR_EXACT_END,
        )
    returned = kernel_checker_ast_v1(KernelCheckerTagV1.RETURN, 1, b"\xff")
    assert parse_kernel_checker_ast_v1(codec_kernel_checker_ast_v1(returned)) == returned


def test_slice_exposes_syntax_but_no_execution_or_positive_authority() -> None:
    import src.core.omegaa_kca1_codec as codec
    import src.core.omegaa_kca1_parser as parser
    import src.core.omegaa_kca1_types as syntax

    public = {name.lower() for module in (codec, parser, syntax) for name in vars(module) if not name.startswith("_")}
    forbidden = ("execute", "runner", "admission", "registry", "capability", "certificate")
    assert not any(token in name for name in public for token in forbidden)
