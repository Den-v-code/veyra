"""Zero-callback hostile pressure for the captured KCC1 singleton boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

import src.core.omegaa_kcc1_builder as builder_module
import src.core.omegaa_kcc1_codec as codec_module
import src.core.omegaa_kcc1_common as common_module
import src.core.omegaa_kcc1_parser as parser_module
import src.core.omegaa_kcc1_types as syntax_module
from src.core.omegaa_kcc1_builder import build_empty_checker_config_v1
from src.core.omegaa_kcc1_codec import codec_empty_checker_config_v1, kcc1_source_root_v1
from src.core.omegaa_kcc1_common import (
    DEFAULT_KCC1_LIMITS_V1,
    KCC1DecodeCodeV1,
    KCC1DecodeError,
    KCC1IntegrityError,
    KCC1LimitsV1,
)
from src.core.omegaa_kcc1_parser import parse_empty_checker_config_v1
from src.core.omegaa_kcc1_types import EMPTY_CHECKER_CONFIG_V1, EmptyCheckerConfigV1

WIRE = b"KCC1\x00\x00"
_HOOK_CALLS: list[str] = []


def _init_bomb(self: object) -> None:
    _HOOK_CALLS.append(type(self).__name__)


class _Bomb:
    def __call__(self, *args: object, **kwargs: object) -> object:
        _HOOK_CALLS.append("call")
        raise AssertionError("must not call")

    def __get__(self, instance: object, owner: object) -> object:
        _HOOK_CALLS.append("get")
        raise AssertionError("must not get")

    def __set__(self, instance: object, value: object) -> None:
        _HOOK_CALLS.append("set")
        raise AssertionError("must not set")


def _assert_integrity(operation: object) -> None:
    with pytest.raises(KCC1IntegrityError):
        operation()  # type: ignore[operator]
    assert _HOOK_CALLS == []


def test_builder_returns_only_captured_identity_without_allocation() -> None:
    assert build_empty_checker_config_v1() is EMPTY_CHECKER_CONFIG_V1
    source = Path(builder_module.__file__).read_text(encoding="utf-8")
    assert "object.__new__" not in source


def test_forged_equal_instances_and_subclasses_fail_closed() -> None:
    forged = EmptyCheckerConfigV1()
    assert forged == EMPTY_CHECKER_CONFIG_V1 and forged is not EMPTY_CHECKER_CONFIG_V1
    with pytest.raises(KCC1IntegrityError, match="singleton-identity"):
        codec_empty_checker_config_v1(forged)
    allocated = object.__new__(EmptyCheckerConfigV1)
    with pytest.raises(KCC1IntegrityError, match="singleton-identity"):
        codec_empty_checker_config_v1(allocated)

    class Subclass(EmptyCheckerConfigV1):  # type: ignore[misc]
        pass

    with pytest.raises(KCC1IntegrityError, match="singleton-identity"):
        codec_empty_checker_config_v1(object.__new__(Subclass))
    with pytest.raises((AttributeError, TypeError)):
        object.__setattr__(EMPTY_CHECKER_CONFIG_V1, "extra", 1)


def test_in_place_generated_init_code_drift_runs_zero_callbacks() -> None:
    init = vars(EmptyCheckerConfigV1)["__init__"]
    old_code = init.__code__
    _HOOK_CALLS.clear()
    init.__code__ = _init_bomb.__code__
    try:
        _assert_integrity(lambda: parse_empty_checker_config_v1(WIRE))
    finally:
        init.__code__ = old_code


def test_added_post_init_and_slots_drift_run_zero_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(EmptyCheckerConfigV1, "__post_init__", _Bomb(), raising=False)
    _assert_integrity(build_empty_checker_config_v1)
    monkeypatch.undo()
    monkeypatch.setattr(EmptyCheckerConfigV1, "__slots__", _Bomb())
    _assert_integrity(lambda: codec_empty_checker_config_v1(EMPTY_CHECKER_CONFIG_V1))


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("module", "name"),
    (
        (syntax_module, "EMPTY_CHECKER_CONFIG_V1"),
        (syntax_module, "EmptyCheckerConfigV1"),
        (parser_module, "build_empty_checker_config_v1"),
        (parser_module, "codec_empty_checker_config_v1"),
        (parser_module, "_syntax"),
        (parser_module, "_integrity_error"),
        (parser_module, "KCC1DecodeCodeV1"),
        (parser_module, "KCC1ResourceKindV1"),
        (parser_module, "_decode_error"),
        (parser_module, "_resource"),
        (parser_module, "_snapshot_limits"),
        (parser_module, "_validate_parser_integrity_v1"),
        (parser_module, "_check_prefix_v1"),
        (parser_module, "MAX_INPUT"),
        (parser_module, "MAX_OUTPUT"),
        (parser_module, "logger"),
        (codec_module, "build_empty_checker_config_v1"),
        (codec_module, "_syntax"),
        (codec_module, "_common"),
        (codec_module, "_integrity_error"),
        (codec_module, "_resource"),
        (codec_module, "_snapshot_limits"),
        (codec_module, "_source_manifest_v1"),
        (codec_module, "KCC1ResourceKindV1"),
        (codec_module, "_validate_codec_integrity_v1"),
        (codec_module, "MAX_OUTPUT"),
        (codec_module, "logger"),
        (builder_module, "_syntax"),
        (builder_module, "_common"),
        (builder_module, "logger"),
        (builder_module, "validate_kcc1_builder_integrity_v1"),
        (common_module, "_integrity_error"),
    ),
)
def test_alias_rebinding_is_sanitized_before_callback(
    module: object, name: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(module, name, _Bomb())
    _assert_integrity(lambda: parse_empty_checker_config_v1(WIRE))


def test_enum_and_limit_descriptor_drift_runs_zero_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    _HOOK_CALLS.clear()
    old_value = object.__getattribute__(KCC1DecodeCodeV1.BAD_VERSION, "_value_")
    object.__setattr__(KCC1DecodeCodeV1.BAD_VERSION, "_value_", 9)
    try:
        _assert_integrity(lambda: parse_empty_checker_config_v1(WIRE))
    finally:
        object.__setattr__(KCC1DecodeCodeV1.BAD_VERSION, "_value_", old_value)
    descriptor = vars(KCC1LimitsV1)["max_input_bytes"]
    monkeypatch.setattr(KCC1LimitsV1, "max_input_bytes", _Bomb())
    _assert_integrity(lambda: parse_empty_checker_config_v1(WIRE))
    assert descriptor is not None


def test_common_enum_vector_and_singleton_private_alias_drift_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(common_module, "_DECODE_CODES_FROZEN", ())
    _assert_integrity(lambda: parse_empty_checker_config_v1(WIRE))
    monkeypatch.undo()
    monkeypatch.setattr(builder_module, "_SINGLETON", _Bomb())
    _assert_integrity(build_empty_checker_config_v1)


def test_wire_and_integrity_exception_alias_drift_fail_before_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(codec_module, "_WIRE_FROZEN", b"EVIL")
    _assert_integrity(lambda: codec_empty_checker_config_v1(EMPTY_CHECKER_CONFIG_V1))
    monkeypatch.undo()
    monkeypatch.setattr(common_module, "KCC1IntegrityError", _Bomb())
    _assert_integrity(lambda: parse_empty_checker_config_v1(WIRE))


def test_mutated_captured_default_limits_refuse_without_callback() -> None:
    _HOOK_CALLS.clear()
    original = DEFAULT_KCC1_LIMITS_V1.max_output_bytes
    object.__setattr__(DEFAULT_KCC1_LIMITS_V1, "max_output_bytes", 5)
    try:
        _assert_integrity(lambda: codec_empty_checker_config_v1(EMPTY_CHECKER_CONFIG_V1))
    finally:
        object.__setattr__(DEFAULT_KCC1_LIMITS_V1, "max_output_bytes", original)


def test_hostile_enum_value_and_default_slot_never_run_equality_callbacks() -> None:
    _HOOK_CALLS.clear()
    old_value = object.__getattribute__(KCC1DecodeCodeV1.BAD_VERSION, "_value_")
    object.__setattr__(KCC1DecodeCodeV1.BAD_VERSION, "_value_", _Bomb())
    try:
        _assert_integrity(lambda: parse_empty_checker_config_v1(WIRE))
    finally:
        object.__setattr__(KCC1DecodeCodeV1.BAD_VERSION, "_value_", old_value)
    original = DEFAULT_KCC1_LIMITS_V1.max_output_bytes
    object.__setattr__(DEFAULT_KCC1_LIMITS_V1, "max_output_bytes", _Bomb())
    try:
        _assert_integrity(lambda: codec_empty_checker_config_v1(EMPTY_CHECKER_CONFIG_V1))
    finally:
        object.__setattr__(DEFAULT_KCC1_LIMITS_V1, "max_output_bytes", original)


def test_decode_error_offset_is_a_natural_number() -> None:
    with pytest.raises(TypeError, match="invalid KCC1 decode error"):
        KCC1DecodeError(KCC1DecodeCodeV1.BAD_LENGTH, -1)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "name",
    ("_root_v1", "_frame", "_validate_manifest_path_v1", "_read_manifest_file_v1"),
)
def test_source_helper_rebinding_is_sanitized_before_callback(
    name: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(codec_module, name, _Bomb())
    _assert_integrity(kcc1_source_root_v1)
