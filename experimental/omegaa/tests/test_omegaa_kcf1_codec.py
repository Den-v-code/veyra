"""Independent literal-wire and bounded parser tests for private KCF1 syntax."""

from __future__ import annotations

import pytest

import src.core.omegaa_kcf1_codec as codec_module
import src.core.omegaa_kcf1_common as common_module
import src.core.omegaa_kcf1_parser as parser_module
from src.core.omegaa_kca1_common import KCA1DecodeCodeV1
from src.core.omegaa_kcf1_codec import codec_kernel_continuation_frame_v1
from src.core.omegaa_kcf1_common import (
    KCF1DecodeCodeV1, KCF1DecodeError, KCF1LimitsV1,
    KCF1ResourceKindV1, KCF1ResourceLimit,
)
from src.core.omegaa_kcf1_parser import parse_kernel_continuation_frame_v1
from src.core.omegaa_kcf1_types import (
    KCF1_ARITIES, KCF1_FIELD_KINDS, KernelContinuationFrameV1,
    KernelContinuationTagV1, kernel_continuation_frame_v1,
)
from src.core.omegaa_kpt1_codec import codec_kernel_proof_term_v1
from src.core.omegaa_kpt1_common import KPT1DecodeCodeV1, KPT1DecodeError, KPT1ResourceLimit
from src.core.omegaa_kpt1_types import (
    KernelProofTermV1, KernelTermTagV1, kernel_term_v1, zero_level_v1,
)


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "big")


def _frame(payload: bytes) -> bytes:
    return _u64(len(payload)) + payload


def _wire(tag: int, *payloads: bytes) -> bytes:
    return b"KCF1" + bytes((tag, len(payloads))) + b"".join(_frame(item) for item in payloads)


def _var(index: int = 0) -> KernelProofTermV1:
    return kernel_term_v1(KernelTermTagV1.VAR, index)


def _samples() -> tuple[tuple[KernelContinuationTagV1, tuple[object, ...]], ...]:
    return (
        (KernelContinuationTagV1.PARSE_TERM, (b"opaque-not-kpt", _var(0))),
        (KernelContinuationTagV1.INFER_EXPECTED_SORT, (_var(1), _var(2))),
        (KernelContinuationTagV1.INFER_TERM, (_var(3), _var(4))),
        (KernelContinuationTagV1.NORMALIZE_EXPECTED, (_var(5), _var(6), _var(7))),
        (KernelContinuationTagV1.NORMALIZE_INFERRED, (_var(8), _var(9), _var(10))),
        (KernelContinuationTagV1.COMPARE_TYPES, (_var(11), _var(12), _var(13))),
        (KernelContinuationTagV1.NORMALIZE_VALUE, (bytes(range(32)),)),
        (KernelContinuationTagV1.RETURN_TYPED, (b"r" * 32,)),
    )


def _payload(value: object) -> bytes:
    return codec_kernel_proof_term_v1(value) if type(value) is KernelProofTermV1 else value  # type: ignore[return-value]


def _assert_decode(raw: bytes, code: KCF1DecodeCodeV1, offset: int) -> None:
    with pytest.raises(KCF1DecodeError) as caught:
        parse_kernel_continuation_frame_v1(raw)
    assert (caught.value.code, caught.value.offset) == (code, offset)


def test_exact_grammar_tables_and_distinct_envelope_enums() -> None:
    expected = (
        ("term_bytes", "term"), ("term", "term"), ("term", "term"),
        ("term", "term", "term"), ("term", "term", "term"),
        ("term", "term", "term"),
        ("kernel_type_id",), ("kernel_type_id",),
    )
    assert tuple(KCF1_FIELD_KINDS[tag] for tag in KernelContinuationTagV1) == expected
    assert tuple(KCF1_ARITIES[tag] for tag in KernelContinuationTagV1) == tuple(map(len, expected))
    assert tuple(item.value for item in KCF1DecodeCodeV1) == tuple(range(11))
    assert tuple(item.value for item in KCF1ResourceKindV1) == tuple(range(7))
    assert KCF1DecodeCodeV1 is not KPT1DecodeCodeV1
    assert KCF1DecodeCodeV1 is not KCA1DecodeCodeV1


@pytest.mark.parametrize(("tag", "fields"), _samples())
def test_all_eight_tags_match_independent_literal_oracles_and_round_trip(
    tag: KernelContinuationTagV1, fields: tuple[object, ...],
) -> None:
    frame = kernel_continuation_frame_v1(tag, *fields)
    expected = _wire(tag.value, *(_payload(item) for item in fields))
    assert codec_kernel_continuation_frame_v1(frame) == expected
    parsed = parse_kernel_continuation_frame_v1(expected)
    assert type(parsed) is KernelContinuationFrameV1
    assert parsed.tag is tag
    assert codec_kernel_continuation_frame_v1(parsed) == expected


def test_opaque_term_bytes_and_arbitrary_digest_stay_syntax_only() -> None:
    opaque = b"KPT1\xff\xff definitely not parsed"
    raw = _wire(0, opaque, codec_kernel_proof_term_v1(_var()))
    parsed = parse_kernel_continuation_frame_v1(raw)
    assert parsed.fields[0] == opaque
    digest = bytes(reversed(range(32)))
    typed = parse_kernel_continuation_frame_v1(_wire(7, digest))
    assert typed.fields == (digest,)
    for module in (
        __import__("src.core.omegaa_kcf1_types", fromlist=["x"]),
        __import__("src.core.omegaa_kcf1_codec", fromlist=["x"]),
        __import__("src.core.omegaa_kcf1_parser", fromlist=["x"]),
    ):
        assert not any(
            token in name.lower() for name in vars(module) if not name.startswith("_")
            for token in ("accept", "reject", "registry", "admission", "certificate", "frameapply")
        )


@pytest.mark.parametrize(("prefix", "offset"), ((b"KPT1", 1), (b"KCA1", 2)))
def test_foreign_prefix_is_not_kcf1(prefix: bytes, offset: int) -> None:
    _assert_decode(prefix + b"\x07\x00", KCF1DecodeCodeV1.BAD_VERSION, offset)


def test_outer_tag_arity_length_trailing_and_digest_errors_are_absolute() -> None:
    _assert_decode(b"KCF1\x08\x00", KCF1DecodeCodeV1.BAD_TAG, 4)
    _assert_decode(b"KCF1\x07\x00", KCF1DecodeCodeV1.BAD_ARITY, 5)
    _assert_decode(b"KCF1\x07\x01\x00", KCF1DecodeCodeV1.BAD_LENGTH, 6)
    _assert_decode(_wire(7, b"x" * 31), KCF1DecodeCodeV1.BAD_LENGTH, 14)
    canonical = _wire(7, b"x" * 32)
    _assert_decode(canonical + b"x", KCF1DecodeCodeV1.TRAILING, len(canonical))


def test_nested_kpt_error_code_and_offset_are_mapped_absolutely() -> None:
    invalid_kpt = b"KPT1\x00\x01" + _frame(_frame(b"\x00"))
    with pytest.raises(KPT1DecodeError) as inner:
        from src.core.omegaa_kpt1_parser import parse_kernel_proof_term_v1
        parse_kernel_proof_term_v1(invalid_kpt)
    raw = _wire(0, b"opaque", invalid_kpt)
    nested_start = 6 + 8 + len(b"opaque") + 8
    _assert_decode(
        raw, KCF1DecodeCodeV1(inner.value.code.value),
        nested_start + inner.value.offset,
    )


def test_earlier_outer_length_error_precedes_later_nested_failure() -> None:
    invalid = b"KCF1\x00\x02" + (999).to_bytes(8, "big") + b"x"
    _assert_decode(invalid, KCF1DecodeCodeV1.BAD_LENGTH, 6)


def test_earlier_nested_failure_precedes_later_outer_length_error() -> None:
    invalid_kpt = b"KPT1\x00\x01" + _frame(_frame(b"\x00"))
    with pytest.raises(KPT1DecodeError) as inner:
        from src.core.omegaa_kpt1_parser import parse_kernel_proof_term_v1
        parse_kernel_proof_term_v1(invalid_kpt)
    suffixes = (_u64(999) + b"x", _frame(codec_kernel_proof_term_v1(_var())) + b"x")
    for suffix in suffixes:
        raw = b"KCF1\x02\x02" + _frame(invalid_kpt) + suffix
        _assert_decode(
            raw, KCF1DecodeCodeV1(inner.value.code.value), 14 + inner.value.offset,
        )


@pytest.mark.parametrize("module", (codec_module, parser_module))
def test_local_grammar_alias_rebinding_refuses(
    module: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module, "_FIELD_KINDS", {KernelContinuationTagV1.RETURN_TYPED: ("term_bytes",)})
    frame = kernel_continuation_frame_v1(KernelContinuationTagV1.RETURN_TYPED, b"x" * 32)
    with pytest.raises(ValueError, match="alias-integrity"):
        (codec_kernel_continuation_frame_v1(frame) if module is codec_module
         else parse_kernel_continuation_frame_v1(_wire(7, b"x" * 32)))


def test_empty_enum_vectors_and_mutable_resource_map_refuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(common_module, "_DECODE_CODES", ())
    with pytest.raises(ValueError, match="enum-integrity"):
        parse_kernel_continuation_frame_v1(_wire(7, b"x" * 32))
    monkeypatch.setattr(common_module, "_DECODE_CODES", common_module._DECODE_CODES_FROZEN)
    monkeypatch.setattr(common_module, "_RESOURCE_KINDS", ())
    with pytest.raises(ValueError, match="enum-integrity"):
        common_module.validate_kcf1_error_enum_integrity_v1()
    monkeypatch.setattr(common_module, "_RESOURCE_KINDS", common_module._RESOURCE_KINDS_FROZEN)
    monkeypatch.setattr(parser_module, "_KPT_CODES", ())
    with pytest.raises(ValueError, match="decode-enum-integrity"):
        parse_kernel_continuation_frame_v1(_wire(7, b"x" * 32))
    monkeypatch.setattr(parser_module, "_KPT_CODES", parser_module._KPT_CODES_FROZEN)
    monkeypatch.setattr(common_module, "_KPT_RESOURCE_MAP", {"max_nodes": KCF1ResourceKindV1.OUTPUT_BYTES})
    with pytest.raises(ValueError, match="resource-integrity"):
        common_module._map_kpt_resource_v1(KPT1ResourceLimit("max_nodes", 0), 0, KPT1ResourceLimit)


def test_depth_is_refused_before_build_and_zero_remainder_is_resource() -> None:
    deep = kernel_term_v1(KernelTermTagV1.FST, _var())
    raw = _wire(2, codec_kernel_proof_term_v1(deep), codec_kernel_proof_term_v1(_var(1)))
    with pytest.raises(KCF1ResourceLimit) as caught:
        parse_kernel_continuation_frame_v1(raw, KCF1LimitsV1(max_depth=2))
    assert (caught.value.kind, caught.value.offset) == (KCF1ResourceKindV1.COMPOSITE_DEPTH, 28)
    first = codec_kernel_proof_term_v1(_var())
    zero_raw = _wire(2, first, b"")
    with pytest.raises(KCF1ResourceLimit) as caught_zero:
        parse_kernel_continuation_frame_v1(
            zero_raw, KCF1LimitsV1(max_nested_kpt_bytes=len(first)),
        )
    assert (caught_zero.value.kind, caught_zero.value.offset) == (
        KCF1ResourceKindV1.NESTED_KPT_BYTES, 22 + len(first),
    )


def test_canonical_empty_tuple_is_explicit_zero_edge_scalar() -> None:
    left = kernel_term_v1(KernelTermTagV1.SORT, zero_level_v1())
    right = kernel_term_v1(KernelTermTagV1.SORT, zero_level_v1())
    assert left.fields[0].fields is right.fields[0].fields  # type: ignore[union-attr]
    frame = kernel_continuation_frame_v1(KernelContinuationTagV1.INFER_TERM, left, right)
    assert codec_kernel_continuation_frame_v1(
        parse_kernel_continuation_frame_v1(codec_kernel_continuation_frame_v1(frame)),
    ) == codec_kernel_continuation_frame_v1(frame)
