"""Literal wire, first-offset and resource precedence for standalone KCC1."""

from __future__ import annotations

import pytest

from src.core.omegaa_kcc1_codec import codec_empty_checker_config_v1
from src.core.omegaa_kcc1_common import (
    KCC1DecodeCodeV1,
    KCC1DecodeError,
    KCC1LimitsV1,
    KCC1ResourceKindV1,
    KCC1ResourceLimit,
)
from src.core.omegaa_kcc1_parser import parse_empty_checker_config_v1
from src.core.omegaa_kcc1_types import EMPTY_CHECKER_CONFIG_V1, EmptyCheckerConfigV1

WIRE = bytes.fromhex("4b4343310000")


def _assert_decode(raw: bytes, code: KCC1DecodeCodeV1, offset: int) -> None:
    with pytest.raises(KCC1DecodeError) as caught:
        parse_empty_checker_config_v1(raw)
    assert (caught.value.code, caught.value.absolute_offset) == (code, offset)


def test_exact_enums_and_zero_slot_singleton_shape() -> None:
    assert tuple(code.value for code in KCC1DecodeCodeV1) == tuple(range(11))
    assert tuple(kind.value for kind in KCC1ResourceKindV1) == (0, 1)
    namespace = vars(EmptyCheckerConfigV1)
    assert namespace["__slots__"] == ()
    assert "__init__" in namespace and "__post_init__" not in namespace
    assert not hasattr(EMPTY_CHECKER_CONFIG_V1, "__dict__")


def test_literal_wire_roundtrip_returns_captured_identity() -> None:
    assert codec_empty_checker_config_v1(EMPTY_CHECKER_CONFIG_V1) == WIRE
    parsed = parse_empty_checker_config_v1(WIRE)
    assert parsed is EMPTY_CHECKER_CONFIG_V1
    assert codec_empty_checker_config_v1(parsed) == WIRE


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("raw", "code", "offset"),
    (
        (b"XCC1\x00\x00", KCC1DecodeCodeV1.BAD_DOMAIN, 0),
        (b"KXC1\x00\x00", KCC1DecodeCodeV1.BAD_DOMAIN, 1),
        (b"KCP1\x00\x00", KCC1DecodeCodeV1.BAD_DOMAIN, 2),
        (b"KCC2\x00\x00", KCC1DecodeCodeV1.BAD_VERSION, 3),
        (b"KCC", KCC1DecodeCodeV1.BAD_LENGTH, 3),
        (b"KCC1", KCC1DecodeCodeV1.BAD_LENGTH, 4),
        (b"KCC1\x01\x00", KCC1DecodeCodeV1.BAD_TAG, 4),
        (b"KCC1\x00", KCC1DecodeCodeV1.BAD_LENGTH, 5),
        (b"KCC1\x00\x01", KCC1DecodeCodeV1.BAD_ARITY, 5),
        (WIRE + b"\x00", KCC1DecodeCodeV1.TRAILING, 6),
    ),
)
def test_exact_decode_precedence(raw: bytes, code: KCC1DecodeCodeV1, offset: int) -> None:
    _assert_decode(raw, code, offset)


def test_input_and_output_resource_envelopes_are_distinct_and_ordered() -> None:
    with pytest.raises(KCC1ResourceLimit) as input_error:
        parse_empty_checker_config_v1(WIRE, KCC1LimitsV1(max_input_bytes=5))
    assert (
        input_error.value.kind,
        input_error.value.allowed,
        input_error.value.required,
        input_error.value.absolute_offset,
    ) == (KCC1ResourceKindV1.INPUT_BYTES, 5, 6, 5)

    limits = KCC1LimitsV1(max_output_bytes=5)
    for operation in (
        lambda: parse_empty_checker_config_v1(WIRE, limits),
        lambda: codec_empty_checker_config_v1(EMPTY_CHECKER_CONFIG_V1, limits),
    ):
        with pytest.raises(KCC1ResourceLimit) as output_error:
            operation()
        assert (
            output_error.value.kind,
            output_error.value.allowed,
            output_error.value.required,
            output_error.value.absolute_offset,
        ) == (KCC1ResourceKindV1.OUTPUT_BYTES, 5, 6, 0)

    with pytest.raises(KCC1DecodeError, match="BAD_TAG@4"):
        parse_empty_checker_config_v1(b"KCC1\x01\x00", limits)


def test_exact_bytes_host_type_and_syntax_only_surface() -> None:
    with pytest.raises(TypeError, match="exact bytes"):
        parse_empty_checker_config_v1(bytearray(WIRE))  # type: ignore[arg-type]
    modules = (
        __import__("src.core.omegaa_kcc1_types", fromlist=["x"]),
        __import__("src.core.omegaa_kcc1_codec", fromlist=["x"]),
        __import__("src.core.omegaa_kcc1_parser", fromlist=["x"]),
    )
    forbidden = ("execute", "semantic", "admission", "registry", "certificate", "kci", "keb", "kie")
    assert not any(
        token in name.lower()
        for module in modules
        for name in vars(module)
        if not name.startswith("_")
        for token in forbidden
    )
