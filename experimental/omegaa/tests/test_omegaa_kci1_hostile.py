"""Zero-callback drift and hostile-object pressure for independent KCI1."""

from __future__ import annotations

from pathlib import Path

import pytest

import src.core.omegaa_kci1_builder as builder_module
import src.core.omegaa_kci1_codec as codec_module
import src.core.omegaa_kci1_common as common_module
import src.core.omegaa_kci1_parser as parser_module
import src.core.omegaa_kci1_types as syntax_module
from src.core.omegaa_kci1_builder import build_checker_input_syntax_v1
from src.core.omegaa_kci1_codec import codec_checker_input_syntax_v1, kci1_source_root_v1
from src.core.omegaa_kci1_common import (
    DEFAULT_KCI1_LIMITS_V1,
    KCI1DecodeCodeV1,
    KCI1IntegrityError,
    KCI1LimitsV1,
    KCI1ResourceKindV1,
)
from src.core.omegaa_kci1_parser import parse_checker_input_syntax_v1
from src.core.omegaa_kci1_types import CheckerInputSyntaxV1, KCI1DecodedResultV1

WIRE = b"KCI1\x00\x02" + bytes(8) + bytes(8)
_HOOK_CALLS: list[str] = []


def _make_init_bomb() -> object:
    marker = object()

    def init_bomb(self: object, expected_bytes: bytes, term_bytes: bytes) -> None:
        del expected_bytes, term_bytes
        if marker is not None:
            _HOOK_CALLS.append(type(self).__name__)

    return init_bomb


_INIT_BOMB = _make_init_bomb()


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
    with pytest.raises(KCI1IntegrityError):
        operation()  # type: ignore[operator]
    assert _HOOK_CALLS == []


def test_builder_and_parser_create_fresh_dtos_without_calling_init_hooks() -> None:
    first = build_checker_input_syntax_v1(b"", b"")
    second = build_checker_input_syntax_v1(b"", b"")
    assert first == second and first is not second
    parsed = parse_checker_input_syntax_v1(WIRE)
    again = parse_checker_input_syntax_v1(WIRE)
    assert type(parsed) is KCI1DecodedResultV1
    assert type(again) is KCI1DecodedResultV1
    assert parsed is not again and parsed.value is not again.value
    source = Path(builder_module.__file__).read_text(encoding="utf-8")
    assert "_OBJECT_NEW_FROZEN(cls)" in source
    assert ".__init__(" not in source


def test_forged_subclass_and_invalid_exact_slot_fail_closed() -> None:
    forged = object.__new__(CheckerInputSyntaxV1)
    object.__setattr__(forged, "expected_bytes", bytearray())
    object.__setattr__(forged, "term_bytes", b"")
    with pytest.raises(KCI1IntegrityError, match="host-shape"):
        codec_checker_input_syntax_v1(forged)

    class Subclass(CheckerInputSyntaxV1):  # type: ignore[misc]
        pass

    subclass = object.__new__(Subclass)
    object.__setattr__(subclass, "expected_bytes", b"")
    object.__setattr__(subclass, "term_bytes", b"")
    with pytest.raises(KCI1IntegrityError, match="host-shape"):
        codec_checker_input_syntax_v1(subclass)


def test_generated_init_and_post_init_drift_execute_zero_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init = vars(CheckerInputSyntaxV1)["__init__"]
    old_code = init.__code__
    _HOOK_CALLS.clear()
    init.__code__ = _INIT_BOMB.__code__  # type: ignore[attr-defined]
    try:
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    finally:
        init.__code__ = old_code
    monkeypatch.setattr(CheckerInputSyntaxV1, "__post_init__", _Bomb())
    _assert_integrity(lambda: build_checker_input_syntax_v1(b"", b""))


def test_slot_and_result_class_drift_execute_zero_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(CheckerInputSyntaxV1, "expected_bytes", _Bomb())
    _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    monkeypatch.undo()
    monkeypatch.setattr(KCI1DecodedResultV1, "__post_init__", _Bomb())
    _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("module", "name"),
    (
        (syntax_module, "CheckerInputSyntaxV1"),
        (syntax_module, "logger"),
        (common_module, "KCI1DecodeCodeV1"),
        (common_module, "_integrity_error"),
        (parser_module, "build_checker_input_syntax_v1"),
        (parser_module, "_build_decode_error_v1"),
        (parser_module, "_build_resource_result_v1"),
        (parser_module, "codec_checker_input_syntax_v1"),
        (parser_module, "_scan_two_frames_v1"),
        (parser_module, "_least_candidate_v1"),
        (parser_module, "_validate_parser_integrity_v1"),
        (parser_module, "logger"),
        (codec_module, "validate_kci1_builder_integrity_v1"),
        (codec_module, "_slot"),
        (codec_module, "_snapshot_limits"),
        (codec_module, "_resource_exception_v1"),
        (codec_module, "_KCI1CodecResource"),
        (codec_module, "_validate_codec_integrity_v1"),
        (codec_module, "logger"),
        (builder_module, "validate_kci1_builder_integrity_v1"),
        (builder_module, "_syntax"),
        (builder_module, "_common"),
        (builder_module, "logger"),
    ),
)
def test_alias_rebinding_is_sanitized_before_callback(
    module: object,
    name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(module, name, _Bomb())
    _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))


def test_enum_and_default_limit_drift_execute_zero_callbacks() -> None:
    _HOOK_CALLS.clear()
    old_value = object.__getattribute__(KCI1DecodeCodeV1.BAD_VERSION, "_value_")
    object.__setattr__(KCI1DecodeCodeV1.BAD_VERSION, "_value_", _Bomb())
    try:
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    finally:
        object.__setattr__(KCI1DecodeCodeV1.BAD_VERSION, "_value_", old_value)
    original = DEFAULT_KCI1_LIMITS_V1.max_output_bytes
    object.__setattr__(DEFAULT_KCI1_LIMITS_V1, "max_output_bytes", _Bomb())
    try:
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    finally:
        object.__setattr__(DEFAULT_KCI1_LIMITS_V1, "max_output_bytes", original)


def test_limit_descriptor_drift_executes_zero_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(KCI1LimitsV1, "max_input_bytes", _Bomb())
    _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("name", "operation"),
    (
        ("_OBJECT_NEW", lambda: build_checker_input_syntax_v1(b"", b"")),
        ("_OBJECT_NEW_FROZEN", lambda: build_checker_input_syntax_v1(b"", b"")),
        ("_BYTES_CLASS", lambda: build_checker_input_syntax_v1(b"", b"")),
        ("_BYTES_CLASS_FROZEN", lambda: build_checker_input_syntax_v1(b"", b"")),
    ),
)
def test_allocator_and_bytes_builtin_drift_executes_zero_callbacks(
    name: str,
    operation: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(builder_module, name, _Bomb())
    _assert_integrity(operation)


def test_every_builder_arm_prechecks_guard_before_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = build_checker_input_syntax_v1(b"", b"")
    error = builder_module._build_decode_error_v1(KCI1DecodeCodeV1.BAD_LENGTH, 0)
    resource = builder_module._build_resource_result_v1(
        KCI1ResourceKindV1.INPUT_BYTES,
        1,
        2,
        1,
    )
    operations = (
        lambda: build_checker_input_syntax_v1(b"", b""),
        lambda: builder_module._build_decode_error_v1(KCI1DecodeCodeV1.BAD_LENGTH, 0),
        lambda: builder_module._build_resource_result_v1(
            KCI1ResourceKindV1.INPUT_BYTES,
            1,
            2,
            1,
        ),
        lambda: builder_module._build_decoded_result_v1(value, 22),
        lambda: builder_module._build_decode_error_result_v1(error),
        lambda: builder_module._build_resource_parse_result_v1(resource),
    )
    for operation in operations:
        _HOOK_CALLS.clear()
        with monkeypatch.context() as patch:
            patch.setattr(builder_module, "_GUARD", _Bomb())
            _assert_integrity(operation)


def test_guard_alias_and_code_drift_executes_zero_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    with monkeypatch.context() as patch:
        patch.setattr(builder_module, "_guard_builder_v1", _Bomb())
        _assert_integrity(lambda: build_checker_input_syntax_v1(b"", b""))
    guard = builder_module._GUARD
    old_code = guard.__code__
    guard.__code__ = _Bomb.__call__.__code__
    try:
        _assert_integrity(lambda: build_checker_input_syntax_v1(b"", b""))
    finally:
        guard.__code__ = old_code


def test_public_builder_and_source_root_alias_or_code_drift_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    with monkeypatch.context() as patch:
        patch.setattr(builder_module, "build_checker_input_syntax_v1", _Bomb())
        _assert_integrity(lambda: build_checker_input_syntax_v1(b"", b""))
    with monkeypatch.context() as patch:
        patch.setattr(codec_module, "kci1_source_root_v1", _Bomb())
        _assert_integrity(kci1_source_root_v1)

    build_public = builder_module._BUILD_PUBLIC
    build_code = build_public.__code__
    build_public.__code__ = _Bomb.__call__.__code__
    try:
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    finally:
        build_public.__code__ = build_code

    source_public = codec_module._SOURCE_ROOT_PUBLIC
    source_code = source_public.__code__
    source_public.__code__ = _Bomb.__call__.__code__
    value = build_checker_input_syntax_v1(b"", b"")
    try:
        _assert_integrity(lambda: codec_checker_input_syntax_v1(value))
    finally:
        source_public.__code__ = source_code


def test_u64_limit_alias_drift_and_literal_constructor_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    with monkeypatch.context() as patch:
        patch.setattr(common_module, "U64_LIMIT", _Bomb())
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    with monkeypatch.context() as patch:
        patch.setattr(parser_module, "_U64_LIMIT", _Bomb())
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    with monkeypatch.context() as patch:
        patch.setattr(common_module, "_U64_LIMIT_FROZEN", _Bomb())
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    with monkeypatch.context() as patch:
        patch.setattr(parser_module, "_U64_LIMIT_FROZEN", _Bomb())
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    with monkeypatch.context() as patch:
        patch.setattr(common_module, "U64_LIMIT", 18_446_744_073_709_551_617)
        with pytest.raises(ValueError, match="positive U64"):
            KCI1LimitsV1(max_input_bytes=18_446_744_073_709_551_616)
    assert _HOOK_CALLS == []


def test_public_and_source_manifest_default_drift_is_sanitized(
    tmp_path: Path,
) -> None:
    _HOOK_CALLS.clear()
    parse_defaults = parser_module.parse_checker_input_syntax_v1.__defaults__
    codec_defaults = codec_module.codec_checker_input_syntax_v1.__defaults__
    source_defaults = codec_module._source_manifest_v1.__defaults__
    assert parse_defaults is not None
    assert codec_defaults is not None
    assert source_defaults is not None
    try:
        parser_module.parse_checker_input_syntax_v1.__defaults__ = (KCI1LimitsV1(max_input_bytes=1),)
        _assert_integrity(lambda: parse_checker_input_syntax_v1(WIRE))
    finally:
        parser_module.parse_checker_input_syntax_v1.__defaults__ = parse_defaults
    try:
        codec_module.codec_checker_input_syntax_v1.__defaults__ = (
            KCI1LimitsV1(max_output_bytes=1),
        )
        value = build_checker_input_syntax_v1(b"", b"")
        _assert_integrity(lambda: codec_checker_input_syntax_v1(value))
    finally:
        codec_module.codec_checker_input_syntax_v1.__defaults__ = codec_defaults
    try:
        codec_module._source_manifest_v1.__defaults__ = (
            codec_module.KCI1_SOURCE_PATHS_V1,
            tmp_path,
        )
        _assert_integrity(kci1_source_root_v1)
    finally:
        codec_module._source_manifest_v1.__defaults__ = source_defaults


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("module", "name"),
    (
        (codec_module, "sha256"),
        (codec_module._HASHLIB_MODULE, "sha256"),
        (codec_module._OS_MODULE, "open"),
        (codec_module._OS_MODULE, "read"),
        (codec_module._OS_MODULE, "fstat"),
        (codec_module._OS_MODULE, "close"),
        (codec_module._STAT_MODULE, "S_ISREG"),
        (codec_module._UNICODE_MODULE, "normalize"),
        (codec_module, "Path"),
        (codec_module._PATHLIB_MODULE, "Path"),
        (codec_module, "_REPOSITORY_ROOT"),
    ),
)
def test_source_external_primitive_drift_executes_zero_callbacks(
    module: object,
    name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    with monkeypatch.context() as patch:
        patch.setattr(module, name, _Bomb())
        _assert_integrity(kci1_source_root_v1)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("module", "name", "replacement"),
    (
        (codec_module._OS_MODULE, "O_RDONLY", 1),
        (codec_module._OS_MODULE, "O_CLOEXEC", 0),
        (codec_module._OS_MODULE, "O_NOFOLLOW", 0),
        (codec_module._OS_MODULE, "O_DIRECTORY", 0),
        (codec_module, "_O_RDONLY_FROZEN", 1),
        (codec_module, "_O_CLOEXEC_FROZEN", 0),
        (codec_module, "_O_NOFOLLOW_FROZEN", 0),
        (codec_module, "_O_DIRECTORY_FROZEN", 0),
        (codec_module, "_OPEN_FLAGS_FROZEN", 524_288),
        (codec_module, "_DIRECTORY_FLAG_FROZEN", 0),
    ),
)
def test_open_flag_semantic_drift_is_sanitized_before_filesystem_use(
    module: object,
    name: str,
    replacement: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    with monkeypatch.context() as patch:
        patch.setattr(module, name, replacement)
        _assert_integrity(kci1_source_root_v1)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "name",
    (
        "_root_v1",
        "_frame",
        "_validate_source_runtime_v1",
        "_validate_manifest_path_v1",
        "_open_repository_root_v1",
        "_close_fd_v1",
        "_read_manifest_file_v1",
    ),
)
def test_source_helper_rebinding_is_sanitized_before_callback(
    name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _HOOK_CALLS.clear()
    monkeypatch.setattr(codec_module, name, _Bomb())
    _assert_integrity(kci1_source_root_v1)


def test_no_forbidden_dependency_or_authority_surface() -> None:
    paths_list: list[Path] = []
    for module in (syntax_module, common_module, builder_module, codec_module, parser_module):
        module_file = module.__file__
        assert module_file is not None
        paths_list.append(Path(module_file))
    paths = tuple(paths_list)
    source = b"".join(path.read_bytes() for path in paths).lower()
    for forbidden in (
        b"omegaa_kpt",
        b"omegaa_kcc",
        b"omegaa_kca",
        b"omegaa_kcf",
        b"omegaa_keb",
        b"omegaa_kie",
        b"registry",
        b"admission",
        b"certificate",
    ):
        assert forbidden not in source
