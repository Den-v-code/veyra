"""Literal KCI1 wire, offsets, U64 gates, and decode/resource precedence."""

from __future__ import annotations

import pytest

from src.core.omegaa_kci1_builder import build_checker_input_syntax_v1
from src.core.omegaa_kci1_codec import _KCI1CodecResource, codec_checker_input_syntax_v1
from src.core.omegaa_kci1_common import (
    KCI1DecodeCodeV1,
    KCI1LimitsV1,
    KCI1ResourceKindV1,
)
from src.core.omegaa_kci1_parser import parse_checker_input_syntax_v1
from src.core.omegaa_kci1_types import (
    CheckerInputSyntaxV1,
    KCI1DecodeErrorResultV1,
    KCI1DecodedResultV1,
    KCI1ResourceParseResultV1,
)


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "big")


def _wire(expected: bytes, term: bytes) -> bytes:
    return b"KCI1\x00\x02" + _u64(len(expected)) + expected + _u64(len(term)) + term


def _assert_decode(raw: bytes, code: KCI1DecodeCodeV1, offset: int) -> None:
    result = parse_checker_input_syntax_v1(raw)
    assert type(result) is KCI1DecodeErrorResultV1
    assert (result.error.code, result.error.absolute_offset) == (code, offset)


def _assert_resource(
    raw: bytes,
    limits: KCI1LimitsV1,
    kind: KCI1ResourceKindV1,
    allowed: int,
    required: int,
    offset: int,
) -> None:
    result = parse_checker_input_syntax_v1(raw, limits)
    assert type(result) is KCI1ResourceParseResultV1
    resource = result.resource
    assert (resource.kind, resource.allowed, resource.required, resource.absolute_offset) == (
        kind,
        allowed,
        required,
        offset,
    )


def test_exact_enums_builder_freshness_and_literal_roundtrip() -> None:
    assert tuple(code.value for code in KCI1DecodeCodeV1) == tuple(range(11))
    assert tuple(kind.value for kind in KCI1ResourceKindV1) == tuple(range(4))
    first = build_checker_input_syntax_v1(b"E", b"term")
    second = build_checker_input_syntax_v1(b"E", b"term")
    assert type(first) is CheckerInputSyntaxV1
    assert first == second and first is not second
    expected = bytes.fromhex(
        "4b4349310002"
        "000000000000000145"
        "00000000000000047465726d"
    )
    assert codec_checker_input_syntax_v1(first) == expected == _wire(b"E", b"term")
    parsed = parse_checker_input_syntax_v1(expected)
    again = parse_checker_input_syntax_v1(expected)
    assert type(parsed) is KCI1DecodedResultV1
    assert type(again) is KCI1DecodedResultV1
    assert parsed.end == len(expected)
    assert parsed.value == first
    assert parsed is not again and parsed.value is not again.value
    assert codec_checker_input_syntax_v1(parsed.value) == expected


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("raw", "code", "offset"),
    (
        (b"", KCI1DecodeCodeV1.BAD_LENGTH, 0),
        (b"XCI1\x00\x02", KCI1DecodeCodeV1.BAD_DOMAIN, 0),
        (b"KXI1\x00\x02", KCI1DecodeCodeV1.BAD_DOMAIN, 1),
        (b"KCX1\x00\x02", KCI1DecodeCodeV1.BAD_DOMAIN, 2),
        (b"KCI2\x00\x02", KCI1DecodeCodeV1.BAD_VERSION, 3),
        (b"KCI", KCI1DecodeCodeV1.BAD_LENGTH, 3),
        (b"KCI1", KCI1DecodeCodeV1.BAD_LENGTH, 4),
        (b"KCI1\x01", KCI1DecodeCodeV1.BAD_TAG, 4),
        (b"KCI1\x00", KCI1DecodeCodeV1.BAD_LENGTH, 5),
        (b"KCI1\x00\x01", KCI1DecodeCodeV1.BAD_ARITY, 5),
        (b"KCI1\x00\x02", KCI1DecodeCodeV1.BAD_LENGTH, 6),
        (b"KCI1\x00\x02" + _u64(3) + b"x", KCI1DecodeCodeV1.BAD_LENGTH, 6),
        (_wire(b"E", b"")[:-8], KCI1DecodeCodeV1.BAD_LENGTH, 15),
        (b"KCI1\x00\x02" + _u64(1) + b"E" + _u64(3) + b"x", KCI1DecodeCodeV1.BAD_LENGTH, 15),
        (_wire(b"E", b"T") + b"x", KCI1DecodeCodeV1.TRAILING, 24),
    ),
)
def test_exact_outer_first_offsets(raw: bytes, code: KCI1DecodeCodeV1, offset: int) -> None:
    _assert_decode(raw, code, offset)


def test_input_resource_precedes_bad_prefix_and_header() -> None:
    raw = b"EVIL" + bytes(40)
    _assert_resource(
        raw,
        KCI1LimitsV1(max_input_bytes=8),
        KCI1ResourceKindV1.INPUT_BYTES,
        8,
        len(raw),
        8,
    )
    boundary = b"EVIL!!"
    _assert_resource(
        boundary,
        KCI1LimitsV1(max_input_bytes=5),
        KCI1ResourceKindV1.INPUT_BYTES,
        5,
        6,
        5,
    )
    _assert_decode(boundary, KCI1DecodeCodeV1.BAD_DOMAIN, 0)


def test_expected_resource_precedes_later_term_frame_fault() -> None:
    raw = b"KCI1\x00\x02" + _u64(2) + b"AB" + _u64(5) + b"x"
    _assert_resource(
        raw,
        KCI1LimitsV1(max_expected_bytes=1),
        KCI1ResourceKindV1.EXPECTED_BYTES,
        1,
        2,
        14,
    )


def test_unsafe_expected_boundary_is_decode_not_field_resource() -> None:
    raw = b"KCI1\x00\x02" + _u64(100) + b"x"
    _assert_decode(raw, KCI1DecodeCodeV1.BAD_LENGTH, 6)


def test_term_resource_precedes_trailing_then_trailing_precedes_output() -> None:
    raw = _wire(b"E", b"TT") + b"x"
    _assert_resource(
        raw,
        KCI1LimitsV1(max_term_bytes=1),
        KCI1ResourceKindV1.TERM_BYTES,
        1,
        2,
        23,
    )
    _assert_decode(raw, KCI1DecodeCodeV1.TRAILING, 25)


def test_output_resource_is_after_all_outer_decode_candidates() -> None:
    raw = _wire(b"E", b"T")
    _assert_resource(
        raw,
        KCI1LimitsV1(max_output_bytes=23),
        KCI1ResourceKindV1.OUTPUT_BYTES,
        23,
        24,
        0,
    )
    _assert_decode(b"KCI1\x01\x02" + raw[6:], KCI1DecodeCodeV1.BAD_TAG, 4)


def test_codec_enforces_field_then_output_caps_at_normative_offsets() -> None:
    value = build_checker_input_syntax_v1(b"EE", b"TT")
    cases = (
        (
            KCI1LimitsV1(max_expected_bytes=1),
            KCI1ResourceKindV1.EXPECTED_BYTES,
            1,
            2,
            14,
        ),
        (
            KCI1LimitsV1(max_term_bytes=1),
            KCI1ResourceKindV1.TERM_BYTES,
            1,
            2,
            24,
        ),
        (
            KCI1LimitsV1(max_output_bytes=25),
            KCI1ResourceKindV1.OUTPUT_BYTES,
            25,
            26,
            0,
        ),
    )
    for limits, kind, allowed, required, offset in cases:
        with pytest.raises(_KCI1CodecResource) as caught:
            codec_checker_input_syntax_v1(value, limits)
        assert (
            caught.value.kind,
            caught.value.allowed,
            caught.value.required,
            caught.value.absolute_offset,
        ) == (kind, allowed, required, offset)


def test_exact_host_types_and_positive_u64_limits() -> None:
    with pytest.raises(Exception, match="payload-type"):
        build_checker_input_syntax_v1(bytearray(), b"")  # type: ignore[arg-type]
    with pytest.raises(Exception, match="raw-type"):
        parse_checker_input_syntax_v1(bytearray())  # type: ignore[arg-type]
    for value in (True, 0, -1, 2**64):
        with pytest.raises(ValueError, match="positive U64"):
            KCI1LimitsV1(max_input_bytes=value)


def test_u64_max_frame_lengths_fail_at_exact_prefix_offsets() -> None:
    maximum = 18_446_744_073_709_551_615
    _assert_decode(
        b"KCI1\x00\x02" + _u64(maximum),
        KCI1DecodeCodeV1.BAD_LENGTH,
        6,
    )
    _assert_decode(
        b"KCI1\x00\x02" + _u64(0) + _u64(maximum),
        KCI1DecodeCodeV1.BAD_LENGTH,
        14,
    )


def test_every_parse_result_arm_and_nested_payload_is_fresh() -> None:
    decoded_first = parse_checker_input_syntax_v1(_wire(b"", b""))
    decoded_second = parse_checker_input_syntax_v1(_wire(b"", b""))
    assert type(decoded_first) is KCI1DecodedResultV1
    assert type(decoded_second) is KCI1DecodedResultV1
    assert decoded_first is not decoded_second
    assert decoded_first.value is not decoded_second.value

    error_first = parse_checker_input_syntax_v1(b"")
    error_second = parse_checker_input_syntax_v1(b"")
    assert type(error_first) is KCI1DecodeErrorResultV1
    assert type(error_second) is KCI1DecodeErrorResultV1
    assert error_first is not error_second
    assert error_first.error is not error_second.error

    limits = KCI1LimitsV1(max_input_bytes=1)
    resource_first = parse_checker_input_syntax_v1(b"XX", limits)
    resource_second = parse_checker_input_syntax_v1(b"XX", limits)
    assert type(resource_first) is KCI1ResourceParseResultV1
    assert type(resource_second) is KCI1ResourceParseResultV1
    assert resource_first is not resource_second
    assert resource_first.resource is not resource_second.resource


def test_codec_resource_exceptions_are_fresh() -> None:
    value = build_checker_input_syntax_v1(b"EE", b"")
    limits = KCI1LimitsV1(max_expected_bytes=1)
    caught: list[_KCI1CodecResource] = []
    for _ in range(2):
        with pytest.raises(_KCI1CodecResource) as current:
            codec_checker_input_syntax_v1(value, limits)
        caught.append(current.value)
    assert caught[0] is not caught[1]
