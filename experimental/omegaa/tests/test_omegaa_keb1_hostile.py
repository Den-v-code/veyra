"""Hostile offsets, decode-before-resource and KPT differential tests for KEB1."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.omegaa_keb1_builder import expected_binding_v1
from src.core.omegaa_keb1_codec import codec_expected_binding_v1
from src.core.omegaa_keb1_common import (
    KEB1DecodeCodeV1, KEB1IntegrityError, KEB1LimitsV1,
)
from src.core.omegaa_keb1_parser import parse_expected_binding_v1
from src.core.omegaa_keb1_preflight import preflight_kpt_wire_v1
from src.core.omegaa_keb1_types import (
    ExpectedBindingSyntaxV1, KEB1DecodeErrorResultV1, KEB1DecodedResultV1,
    KEB1ResourceParseResultV1,
)
from src.core.omegaa_kpt1_codec import codec_kernel_proof_term_v1
from src.core.omegaa_kpt1_common import KPT1DecodeError, KPT1LimitsV1
from src.core.omegaa_kpt1_parser import parse_kernel_proof_term_v1
from src.core.omegaa_kpt1_types import KernelTermTagV1, kernel_term_v1


def _frame(value: bytes) -> bytes:
    return len(value).to_bytes(8, "big") + value


def _var():
    return kernel_term_v1(KernelTermTagV1.VAR, 0)


def _outer(payload: bytes, wire: bytes | None = None, suffix: bytes = b"") -> bytes:
    return b"KEB1\x00\x02" + _frame(payload) + _frame(payload if wire is None else wire) + suffix


@pytest.mark.parametrize(
    ("raw", "code", "offset"),
    (
        (b"", KEB1DecodeCodeV1.BAD_LENGTH, 0),
        (b"X", KEB1DecodeCodeV1.BAD_DOMAIN, 0),
        (b"KXB1", KEB1DecodeCodeV1.BAD_DOMAIN, 1),
        (b"KEX1", KEB1DecodeCodeV1.BAD_DOMAIN, 2),
        (b"KEBX", KEB1DecodeCodeV1.BAD_VERSION, 3),
        (b"KEB1", KEB1DecodeCodeV1.BAD_LENGTH, 4),
        (b"KEB1\x01", KEB1DecodeCodeV1.BAD_TAG, 4),
        (b"KEB1\x00", KEB1DecodeCodeV1.BAD_LENGTH, 5),
        (b"KEB1\x00\x01", KEB1DecodeCodeV1.BAD_ARITY, 5),
        (b"KEB1\x00\x02", KEB1DecodeCodeV1.BAD_LENGTH, 6),
        (b"KEB1\x00\x02" + (99).to_bytes(8, "big"), KEB1DecodeCodeV1.BAD_LENGTH, 6),
    ),
)
def test_exact_early_outer_table(raw: bytes, code: KEB1DecodeCodeV1, offset: int) -> None:
    result = parse_expected_binding_v1(raw)
    assert type(result) is KEB1DecodeErrorResultV1
    assert (result.error.code, result.error.absolute_offset) == (code, offset)


def test_dependency_beats_later_trailing() -> None:
    payload = codec_kernel_proof_term_v1(_var())
    raw = _outer(payload, b"X" + payload[1:], b"tail")
    result = parse_expected_binding_v1(raw)
    assert type(result) is KEB1DecodeErrorResultV1
    assert (result.error.code, result.error.absolute_offset) == (
        KEB1DecodeCodeV1.DEPENDENCY, 22 + len(payload),
    )


def test_dependency_wins_equal_end_tie_by_ordinal() -> None:
    payload = codec_kernel_proof_term_v1(_var())
    wire = payload + b"X"
    raw = _outer(payload, wire, b"tail")
    result = parse_expected_binding_v1(raw)
    assert type(result) is KEB1DecodeErrorResultV1
    assert result.error.code is KEB1DecodeCodeV1.DEPENDENCY
    assert result.error.absolute_offset == 22 + 2 * len(payload)


def test_decode_precedes_every_non_input_resource() -> None:
    payload = bytearray(codec_kernel_proof_term_v1(_var()))
    payload[4] = 255
    raw = _outer(bytes(payload))
    limits = replace(KEB1LimitsV1(), max_output_bytes=1, max_nested_kpt_bytes=1, max_expected_wire_bytes=1)
    result = parse_expected_binding_v1(raw, limits)
    assert type(result) is KEB1DecodeErrorResultV1
    assert (result.error.code, result.error.absolute_offset) == (KEB1DecodeCodeV1.BAD_TAG, 18)


@pytest.mark.parametrize("mutation", (0, 1, 2, 3, 4, 5, 6, 13, 21))
def test_owned_preflight_matches_frozen_kpt_first_error(mutation: int) -> None:
    canonical = codec_kernel_proof_term_v1(_var())
    raw = bytearray(canonical)
    if mutation < len(raw):
        raw[mutation] ^= 0xFF
    damaged = bytes(raw)
    report = preflight_kpt_wire_v1(damaged)
    with pytest.raises(KPT1DecodeError) as info:
        parse_kernel_proof_term_v1(damaged, KPT1LimitsV1(max_input_bytes=1000, max_output_bytes=1000))
    assert report.decode_candidates
    assert report.decode_candidates[0] == (KEB1DecodeCodeV1(info.value.code.value), info.value.offset)


def test_wrong_raw_and_limit_host_types_refused() -> None:
    with pytest.raises(KEB1IntegrityError):
        parse_expected_binding_v1(bytearray())  # type: ignore[arg-type]
    with pytest.raises(KEB1IntegrityError):
        parse_expected_binding_v1(_outer(codec_kernel_proof_term_v1(_var())), object())  # type: ignore[arg-type]


def test_subclass_and_forged_term_shape_refused() -> None:
    class BindingSubclass(ExpectedBindingSyntaxV1):
        pass

    valid = expected_binding_v1(_var())
    forged = object.__new__(BindingSubclass)
    object.__setattr__(forged, "expected_term", valid.expected_term)
    object.__setattr__(forged, "expected_wire", valid.expected_wire)
    with pytest.raises(KEB1IntegrityError):
        codec_expected_binding_v1(forged)


def test_parser_rejects_kpt_parser_monkeypatch(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.omegaa_kpt1_parser as dependency

    raw = codec_expected_binding_v1(expected_binding_v1(_var()))
    monkeypatch.setattr(dependency, "parse_kernel_proof_term_v1", lambda *_: _var())
    with pytest.raises(KEB1IntegrityError, match="parser-integrity"):
        parse_expected_binding_v1(raw)


def test_nested_parser_helper_monkeypatch_is_zero_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.omegaa_kpt1_parser as dependency

    called = 0

    def hostile(*_args: object) -> object:
        nonlocal called
        called += 1
        return _var()

    raw = codec_expected_binding_v1(expected_binding_v1(_var()))
    monkeypatch.setattr(dependency, "_parse_term", hostile)
    with pytest.raises(KEB1IntegrityError, match="parser-integrity"):
        parse_expected_binding_v1(raw)
    assert called == 0


def test_nested_codec_helper_monkeypatch_is_zero_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.omegaa_kpt1_codec as dependency

    called = 0

    def hostile(*_args: object) -> object:
        nonlocal called
        called += 1
        return object()

    monkeypatch.setattr(dependency, "_preflight", hostile)
    with pytest.raises(KEB1IntegrityError, match="builder-integrity"):
        expected_binding_v1(_var())
    assert called == 0


def test_builder_allocator_alias_drift_is_zero_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.omegaa_keb1_builder as builder

    called = 0

    def hostile(*_args: object) -> object:
        nonlocal called
        called += 1
        return object()

    monkeypatch.setattr(builder, "_OBJECT_NEW", hostile)
    with pytest.raises(KEB1IntegrityError, match="builder-integrity"):
        expected_binding_v1(_var())
    assert called == 0


def test_parser_and_codec_default_drift_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.omegaa_keb1_codec as codec_module
    import src.core.omegaa_keb1_parser as parser_module

    binding = expected_binding_v1(_var())
    monkeypatch.setattr(codec_module.codec_expected_binding_v1, "__defaults__", (object(),))
    with pytest.raises(KEB1IntegrityError, match="codec-integrity"):
        codec_module.codec_expected_binding_v1(binding, KEB1LimitsV1())
    monkeypatch.undo()
    raw = codec_expected_binding_v1(binding)
    monkeypatch.setattr(parser_module.parse_expected_binding_v1, "__defaults__", (object(),))
    with pytest.raises(KEB1IntegrityError, match="parser-integrity"):
        parser_module.parse_expected_binding_v1(raw, KEB1LimitsV1())


def test_u64_max_claims_are_typed_wire_faults() -> None:
    maximum = (2**64 - 1).to_bytes(8, "big")
    first = parse_expected_binding_v1(b"KEB1\x00\x02" + maximum)
    assert type(first) is KEB1DecodeErrorResultV1
    assert (first.error.code, first.error.absolute_offset) == (KEB1DecodeCodeV1.BAD_LENGTH, 6)
    payload = codec_kernel_proof_term_v1(_var())
    second = parse_expected_binding_v1(b"KEB1\x00\x02" + _frame(payload) + maximum)
    assert type(second) is KEB1DecodeErrorResultV1
    assert (second.error.code, second.error.absolute_offset) == (KEB1DecodeCodeV1.BAD_LENGTH, 14 + len(payload))


def test_public_parse_results_are_fresh_exact_dtos() -> None:
    raw = codec_expected_binding_v1(expected_binding_v1(_var()))
    first = parse_expected_binding_v1(raw)
    second = parse_expected_binding_v1(raw)
    assert type(first) is KEB1DecodedResultV1 and type(second) is KEB1DecodedResultV1
    assert first is not second and first.value is not second.value
    bad_first = parse_expected_binding_v1(b"")
    bad_second = parse_expected_binding_v1(b"")
    assert type(bad_first) is KEB1DecodeErrorResultV1 and type(bad_second) is KEB1DecodeErrorResultV1
    assert bad_first is not bad_second and bad_first.error is not bad_second.error
    limited_first = parse_expected_binding_v1(raw, replace(KEB1LimitsV1(), max_input_bytes=1))
    limited_second = parse_expected_binding_v1(raw, replace(KEB1LimitsV1(), max_input_bytes=1))
    assert type(limited_first) is KEB1ResourceParseResultV1 and type(limited_second) is KEB1ResourceParseResultV1
    assert limited_first is not limited_second and limited_first.resource is not limited_second.resource
