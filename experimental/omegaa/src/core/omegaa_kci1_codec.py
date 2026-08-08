"""Canonical KCI1 codec and exact five-file manifest-only source root."""

from __future__ import annotations

import hashlib
import logging
import os
import pathlib
from pathlib import Path
import stat
from typing import Callable, cast
import unicodedata

from . import omegaa_kci1_common as _common
from . import omegaa_kci1_types as _syntax
from .omegaa_kci1_builder import validate_kci1_builder_integrity_v1
from .omegaa_kci1_common import (
    DEFAULT_KCI1_LIMITS_V1,
    KCI1_PREFIX,
    MAX_EXPECTED,
    MAX_OUTPUT,
    MAX_TERM,
    KCI1LimitsV1,
    KCI1ResourceKindV1,
    _checked_add_u64,
    _checked_u64,
    _integrity_error,
    _slot,
    _snapshot_limits,
    validate_kci1_common_integrity_v1,
)
from .omegaa_kci1_types import CheckerInputSyntaxV1

sha256 = hashlib.sha256
logger = logging.getLogger(__name__)
_LOGGER = logger
_COMMON_MODULE = _common
_SYNTAX_MODULE = _syntax
_INPUT_CLASS = CheckerInputSyntaxV1
_DEFAULT_LIMITS = DEFAULT_KCI1_LIMITS_V1
_EXPECTED_SLOT = vars(_INPUT_CLASS)["expected_bytes"]
_TERM_SLOT = vars(_INPUT_CLASS)["term_bytes"]
_PREFIX_FROZEN = KCI1_PREFIX
_VALIDATE_BUILDER = validate_kci1_builder_integrity_v1
_VALIDATE_BUILDER_CODE = _VALIDATE_BUILDER.__code__
_VALIDATE_COMMON = validate_kci1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON.__code__
_INTEGRITY_ERROR = _integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__
_SLOT = _slot
_SLOT_CODE = _SLOT.__code__
_SNAPSHOT_LIMITS = _snapshot_limits
_SNAPSHOT_LIMITS_CODE = _SNAPSHOT_LIMITS.__code__
_CHECKED_U64 = _checked_u64
_CHECKED_U64_CODE = _CHECKED_U64.__code__
_CHECKED_ADD = _checked_add_u64
_CHECKED_ADD_CODE = _CHECKED_ADD.__code__
_RESOURCE_CLASS = KCI1ResourceKindV1
_MAX_OUTPUT = MAX_OUTPUT
_MAX_EXPECTED = MAX_EXPECTED
_MAX_TERM = MAX_TERM
_REPOSITORY_ROOT = Path(__file__).parents[2]
_REPOSITORY_ROOT_FROZEN = _REPOSITORY_ROOT
_REPOSITORY_ROOT_TYPE = type(_REPOSITORY_ROOT_FROZEN)
_PATH_PARTS_OWNER = next(
    owner for owner in _REPOSITORY_ROOT_TYPE.__mro__ if "parts" in vars(owner)
)
_PATH_PARTS_DESCRIPTOR = vars(_PATH_PARTS_OWNER)["parts"]
_PATH_PARTS_GETTER = cast(
    Callable[[Path], tuple[str, ...]],
    _PATH_PARTS_DESCRIPTOR.fget,
)
_HASHLIB_MODULE = hashlib
_OS_MODULE = os
_PATHLIB_MODULE = pathlib
_STAT_MODULE = stat
_UNICODE_MODULE = unicodedata
_SHA256_FROZEN = hashlib.sha256
_OS_OPEN_FROZEN = os.open
_OS_READ_FROZEN = os.read
_OS_FSTAT_FROZEN = os.fstat
_OS_CLOSE_FROZEN = os.close
_STAT_ISREG_FROZEN = stat.S_ISREG
_PATH_FACTORY_FROZEN = Path
_UNICODE_NORMALIZE_FROZEN = unicodedata.normalize
_O_RDONLY_FROZEN = os.O_RDONLY
_O_CLOEXEC_FROZEN = os.O_CLOEXEC
_O_NOFOLLOW_FROZEN = os.O_NOFOLLOW
_O_DIRECTORY_FROZEN = os.O_DIRECTORY
_OPEN_FLAGS_FROZEN = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
_DIRECTORY_FLAG_FROZEN = os.O_DIRECTORY
_SEPARATOR_FROZEN = os.sep
KCI1_SOURCE_PATHS_V1 = (
    "src/core/omegaa_kci1_builder.py",
    "src/core/omegaa_kci1_codec.py",
    "src/core/omegaa_kci1_common.py",
    "src/core/omegaa_kci1_parser.py",
    "src/core/omegaa_kci1_types.py",
)
_SOURCE_PATHS_FROZEN = KCI1_SOURCE_PATHS_V1


def _validate_source_runtime_v1() -> None:
    """Refuse external primitive, path factory, or captured-root drift."""
    _LOGGER.debug("_validate_source_runtime_v1 entry")
    hashlib_namespace = vars(_HASHLIB_MODULE)
    os_namespace = vars(_OS_MODULE)
    pathlib_namespace = vars(_PATHLIB_MODULE)
    stat_namespace = vars(_STAT_MODULE)
    unicode_namespace = vars(_UNICODE_MODULE)
    drift = (
        globals().get("hashlib") is not _HASHLIB_MODULE
        or globals().get("os") is not _OS_MODULE
        or globals().get("pathlib") is not _PATHLIB_MODULE
        or globals().get("stat") is not _STAT_MODULE
        or globals().get("unicodedata") is not _UNICODE_MODULE
        or globals().get("sha256") is not _SHA256_FROZEN
        or hashlib_namespace.get("sha256") is not _SHA256_FROZEN
        or os_namespace.get("open") is not _OS_OPEN_FROZEN
        or os_namespace.get("read") is not _OS_READ_FROZEN
        or os_namespace.get("fstat") is not _OS_FSTAT_FROZEN
        or os_namespace.get("close") is not _OS_CLOSE_FROZEN
        or stat_namespace.get("S_ISREG") is not _STAT_ISREG_FROZEN
        or globals().get("Path") is not _PATH_FACTORY_FROZEN
        or pathlib_namespace.get("Path") is not _PATH_FACTORY_FROZEN
        or unicode_namespace.get("normalize") is not _UNICODE_NORMALIZE_FROZEN
        or type(os_namespace.get("O_RDONLY")) is not int
        or os_namespace.get("O_RDONLY") != 0
        or type(os_namespace.get("O_CLOEXEC")) is not int
        or os_namespace.get("O_CLOEXEC") != 524_288
        or type(os_namespace.get("O_NOFOLLOW")) is not int
        or os_namespace.get("O_NOFOLLOW") != 131_072
        or type(os_namespace.get("O_DIRECTORY")) is not int
        or os_namespace.get("O_DIRECTORY") != 65_536
        or type(_O_RDONLY_FROZEN) is not int
        or _O_RDONLY_FROZEN != 0
        or type(_O_CLOEXEC_FROZEN) is not int
        or _O_CLOEXEC_FROZEN != 524_288
        or type(_O_NOFOLLOW_FROZEN) is not int
        or _O_NOFOLLOW_FROZEN != 131_072
        or type(_O_DIRECTORY_FROZEN) is not int
        or _O_DIRECTORY_FROZEN != 65_536
        or type(_OPEN_FLAGS_FROZEN) is not int
        or _OPEN_FLAGS_FROZEN != 655_360
        or _OPEN_FLAGS_FROZEN
        != (_O_RDONLY_FROZEN | _O_CLOEXEC_FROZEN | _O_NOFOLLOW_FROZEN)
        or (_OPEN_FLAGS_FROZEN & _O_CLOEXEC_FROZEN) != _O_CLOEXEC_FROZEN
        or (_OPEN_FLAGS_FROZEN & _O_NOFOLLOW_FROZEN) != _O_NOFOLLOW_FROZEN
        or type(_DIRECTORY_FLAG_FROZEN) is not int
        or _DIRECTORY_FLAG_FROZEN != 65_536
        or _DIRECTORY_FLAG_FROZEN != _O_DIRECTORY_FROZEN
        or type(_SEPARATOR_FROZEN) is not str
        or _SEPARATOR_FROZEN != "/"
        or type(_REPOSITORY_ROOT_FROZEN) is not _REPOSITORY_ROOT_TYPE
        or globals().get("_REPOSITORY_ROOT") is not _REPOSITORY_ROOT_FROZEN
        or vars(_PATH_PARTS_OWNER).get("parts") is not _PATH_PARTS_DESCRIPTOR
        or _PATH_PARTS_DESCRIPTOR.fget is not _PATH_PARTS_GETTER
    )
    if drift:
        _LOGGER.error("_validate_source_runtime_v1 error drift")
        _INTEGRITY_ERROR("kci1-source-runtime-integrity")
    _LOGGER.debug("_validate_source_runtime_v1 exit")


_VALIDATE_SOURCE_RUNTIME = _validate_source_runtime_v1
_VALIDATE_SOURCE_RUNTIME_CODE = _VALIDATE_SOURCE_RUNTIME.__code__


def _validate_codec_integrity_v1() -> None:
    _LOGGER.debug("_validate_codec_integrity_v1 entry")
    syntax = vars(_SYNTAX_MODULE)
    common = vars(_COMMON_MODULE)
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("_syntax") is not _SYNTAX_MODULE
        or globals().get("_common") is not _COMMON_MODULE
        or syntax.get("CheckerInputSyntaxV1") is not _INPUT_CLASS
        or globals().get("CheckerInputSyntaxV1") is not _INPUT_CLASS
        or globals().get("DEFAULT_KCI1_LIMITS_V1") is not _DEFAULT_LIMITS
        or vars(_INPUT_CLASS).get("expected_bytes") is not _EXPECTED_SLOT
        or vars(_INPUT_CLASS).get("term_bytes") is not _TERM_SLOT
        or globals().get("validate_kci1_builder_integrity_v1") is not _VALIDATE_BUILDER
        or _VALIDATE_BUILDER.__code__ is not _VALIDATE_BUILDER_CODE
        or globals().get("validate_kci1_common_integrity_v1") is not _VALIDATE_COMMON
        or _VALIDATE_COMMON.__code__ is not _VALIDATE_COMMON_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or globals().get("_slot") is not _SLOT
        or _SLOT.__code__ is not _SLOT_CODE
        or globals().get("_snapshot_limits") is not _SNAPSHOT_LIMITS
        or _SNAPSHOT_LIMITS.__code__ is not _SNAPSHOT_LIMITS_CODE
        or globals().get("_checked_u64") is not _CHECKED_U64
        or _CHECKED_U64.__code__ is not _CHECKED_U64_CODE
        or globals().get("_checked_add_u64") is not _CHECKED_ADD
        or _CHECKED_ADD.__code__ is not _CHECKED_ADD_CODE
        or globals().get("KCI1ResourceKindV1") is not _RESOURCE_CLASS
        or common.get("KCI1ResourceKindV1") is not _RESOURCE_CLASS
        or globals().get("_KCI1CodecResource") is not _CODEC_RESOURCE_CLASS
        or vars(_CODEC_RESOURCE_CLASS).get("__init__") is not _CODEC_RESOURCE_INIT
        or _CODEC_RESOURCE_INIT.__code__ is not _CODEC_RESOURCE_INIT_CODE
        or globals().get("_resource_exception_v1") is not _RESOURCE_EXCEPTION
        or _RESOURCE_EXCEPTION.__code__ is not _RESOURCE_EXCEPTION_CODE
        or globals().get("KCI1_PREFIX") is not _PREFIX_FROZEN
        or _PREFIX_FROZEN != b"KCI1"
        or (_MAX_OUTPUT, _MAX_EXPECTED, _MAX_TERM) != (1, 2, 3)
        or globals().get("KCI1_SOURCE_PATHS_V1") is not _SOURCE_PATHS_FROZEN
        or globals().get("_validate_source_runtime_v1") is not _VALIDATE_SOURCE_RUNTIME
        or _VALIDATE_SOURCE_RUNTIME.__code__ is not _VALIDATE_SOURCE_RUNTIME_CODE
        or globals().get("_source_manifest_v1") is not _SOURCE_MANIFEST
        or _SOURCE_MANIFEST.__code__ is not _SOURCE_MANIFEST_CODE
        or _SOURCE_MANIFEST.__defaults__ is not _SOURCE_MANIFEST_DEFAULTS
        or type(_SOURCE_MANIFEST_DEFAULTS) is not tuple
        or len(_SOURCE_MANIFEST_DEFAULTS) != 2
        or _SOURCE_MANIFEST_DEFAULTS[0] is not _SOURCE_PATHS_FROZEN
        or _SOURCE_MANIFEST_DEFAULTS[1] is not _REPOSITORY_ROOT_FROZEN
        or globals().get("codec_checker_input_syntax_v1") is not _CODEC_PUBLIC
        or _CODEC_PUBLIC.__code__ is not _CODEC_PUBLIC_CODE
        or _CODEC_PUBLIC.__defaults__ is not _CODEC_PUBLIC_DEFAULTS
        or type(_CODEC_PUBLIC_DEFAULTS) is not tuple
        or len(_CODEC_PUBLIC_DEFAULTS) != 1
        or _CODEC_PUBLIC_DEFAULTS[0] is not _DEFAULT_LIMITS
        or globals().get("kci1_source_root_v1") is not _SOURCE_ROOT_PUBLIC
        or _SOURCE_ROOT_PUBLIC.__code__ is not _SOURCE_ROOT_PUBLIC_CODE
    )
    if drift:
        _LOGGER.error("_validate_codec_integrity_v1 error drift")
        _INTEGRITY_ERROR("kci1-codec-integrity")
    _VALIDATE_SOURCE_RUNTIME()
    _VALIDATE_BUILDER()
    _VALIDATE_COMMON()
    _LOGGER.debug("_validate_codec_integrity_v1 exit")


_VALIDATE_LOCAL = _validate_codec_integrity_v1
_VALIDATE_LOCAL_CODE = _VALIDATE_LOCAL.__code__


def _u64(value: int) -> bytes:
    _LOGGER.debug("_u64 entry value=%s", value)
    checked = _CHECKED_U64(value, "codec-u64")
    result = checked.to_bytes(8, "big")
    _LOGGER.debug("_u64 exit")
    return result


_U64 = _u64
_U64_CODE = _U64.__code__


def _frame(value: bytes) -> bytes:
    _LOGGER.debug("_frame entry")
    if type(value) is not bytes:
        _LOGGER.error("_frame error value-type")
        _INTEGRITY_ERROR("kci1-frame-type")
    if globals().get("_u64") is not _U64 or _U64.__code__ is not _U64_CODE:
        _LOGGER.error("_frame error helper-drift")
        _INTEGRITY_ERROR("kci1-u64-integrity")
    result = _U64(len(value)) + value
    _LOGGER.debug("_frame exit bytes=%d", len(result))
    return result


_FRAME = _frame
_FRAME_CODE = _FRAME.__code__


def _input_fields_v1(value: CheckerInputSyntaxV1) -> tuple[bytes, bytes]:
    _LOGGER.debug("_input_fields_v1 entry")
    if type(value) is not _INPUT_CLASS:
        _LOGGER.error("_input_fields_v1 error value-type")
        _INTEGRITY_ERROR("kci1-input-host-shape")
    expected = _SLOT(_EXPECTED_SLOT, value, "expected-bytes")
    term = _SLOT(_TERM_SLOT, value, "term-bytes")
    if type(expected) is not bytes or type(term) is not bytes:
        _LOGGER.error("_input_fields_v1 error field-type")
        _INTEGRITY_ERROR("kci1-input-host-shape")
    result = (expected, term)
    _LOGGER.debug("_input_fields_v1 exit")
    return result


_INPUT_FIELDS = _input_fields_v1
_INPUT_FIELDS_CODE = _INPUT_FIELDS.__code__


def codec_checker_input_syntax_v1(
    value: CheckerInputSyntaxV1,
    limits: KCI1LimitsV1 = DEFAULT_KCI1_LIMITS_V1,
) -> bytes:
    """Encode one exact inert input with field and output resource gates."""
    _LOGGER.debug("codec_checker_input_syntax_v1 entry")
    if (
        globals().get("codec_checker_input_syntax_v1") is not _CODEC_PUBLIC
        or _CODEC_PUBLIC.__code__ is not _CODEC_PUBLIC_CODE
        or _CODEC_PUBLIC.__defaults__ is not _CODEC_PUBLIC_DEFAULTS
        or type(_CODEC_PUBLIC_DEFAULTS) is not tuple
        or len(_CODEC_PUBLIC_DEFAULTS) != 1
        or _CODEC_PUBLIC_DEFAULTS[0] is not _DEFAULT_LIMITS
        or globals().get("_validate_codec_integrity_v1") is not _VALIDATE_LOCAL
        or _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
        or globals().get("_input_fields_v1") is not _INPUT_FIELDS
        or _INPUT_FIELDS.__code__ is not _INPUT_FIELDS_CODE
        or globals().get("_frame") is not _FRAME
        or _FRAME.__code__ is not _FRAME_CODE
        or globals().get("_resource_exception_v1") is not _RESOURCE_EXCEPTION
        or _RESOURCE_EXCEPTION.__code__ is not _RESOURCE_EXCEPTION_CODE
    ):
        _LOGGER.error("codec_checker_input_syntax_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-codec-helper-integrity")
    _VALIDATE_LOCAL()
    limit_values = _SNAPSHOT_LIMITS(limits)
    expected, term = _INPUT_FIELDS(value)
    b_expected = 14
    lp_term = _CHECKED_ADD(b_expected, len(expected), "codec-lp-term")
    b_term = _CHECKED_ADD(lp_term, 8, "codec-b-term")
    end = _CHECKED_ADD(b_term, len(term), "codec-end")
    if len(expected) > limit_values[_MAX_EXPECTED]:
        _LOGGER.debug("codec_checker_input_syntax_v1 state=expected-resource")
        raise _RESOURCE_EXCEPTION(
            _RESOURCE_CLASS.EXPECTED_BYTES,
            limit_values[_MAX_EXPECTED],
            len(expected),
            b_expected,
        )
    if len(term) > limit_values[_MAX_TERM]:
        _LOGGER.debug("codec_checker_input_syntax_v1 state=term-resource")
        raise _RESOURCE_EXCEPTION(
            _RESOURCE_CLASS.TERM_BYTES,
            limit_values[_MAX_TERM],
            len(term),
            b_term,
        )
    if end > limit_values[_MAX_OUTPUT]:
        _LOGGER.debug("codec_checker_input_syntax_v1 state=output-resource")
        raise _RESOURCE_EXCEPTION(
            _RESOURCE_CLASS.OUTPUT_BYTES,
            limit_values[_MAX_OUTPUT],
            end,
            0,
        )
    result = _PREFIX_FROZEN + b"\x00\x02" + _FRAME(expected) + _FRAME(term)
    if len(result) != end:
        _LOGGER.error("codec_checker_input_syntax_v1 error size-invariant")
        _INTEGRITY_ERROR("kci1-codec-size-invariant")
    _LOGGER.debug("codec_checker_input_syntax_v1 exit bytes=%d", len(result))
    return result


_CODEC_PUBLIC = codec_checker_input_syntax_v1
_CODEC_PUBLIC_CODE = _CODEC_PUBLIC.__code__
_CODEC_PUBLIC_DEFAULTS = _CODEC_PUBLIC.__defaults__


class _KCI1CodecResource(ValueError):
    """Private codec-only resource signal translated by no semantic layer."""

    def __init__(
        self,
        kind: KCI1ResourceKindV1,
        allowed: int,
        required: int,
        absolute_offset: int,
    ) -> None:
        _LOGGER.debug("_KCI1CodecResource.__init__ entry")
        self.kind = kind
        self.allowed = allowed
        self.required = required
        self.absolute_offset = absolute_offset
        super().__init__(f"{kind.name}:{allowed}<{required}@{absolute_offset}")
        _LOGGER.error(
            "KCI1 codec resource refused kind=%s allowed=%d required=%d offset=%d",
            kind.name,
            allowed,
            required,
            absolute_offset,
        )
        _LOGGER.debug("_KCI1CodecResource.__init__ exit")


_CODEC_RESOURCE_CLASS = _KCI1CodecResource
_CODEC_RESOURCE_INIT = vars(_CODEC_RESOURCE_CLASS)["__init__"]
_CODEC_RESOURCE_INIT_CODE = _CODEC_RESOURCE_INIT.__code__


def _resource_exception_v1(
    kind: KCI1ResourceKindV1,
    allowed: int,
    required: int,
    absolute_offset: int,
) -> _KCI1CodecResource:
    _LOGGER.debug("_resource_exception_v1 entry")
    if (
        globals().get("_KCI1CodecResource") is not _CODEC_RESOURCE_CLASS
        or vars(_CODEC_RESOURCE_CLASS).get("__init__") is not _CODEC_RESOURCE_INIT
        or _CODEC_RESOURCE_INIT.__code__ is not _CODEC_RESOURCE_INIT_CODE
        or type(kind) is not _RESOURCE_CLASS
    ):
        _LOGGER.error("_resource_exception_v1 error integrity")
        _INTEGRITY_ERROR("kci1-codec-resource-integrity")
    for value, label in (
        (allowed, "codec-resource-allowed"),
        (required, "codec-resource-required"),
        (absolute_offset, "codec-resource-offset"),
    ):
        _CHECKED_U64(value, label)
    if required <= allowed:
        _LOGGER.error("_resource_exception_v1 error nonexcess")
        _INTEGRITY_ERROR("kci1-codec-resource-nonexcess")
    result = _CODEC_RESOURCE_CLASS(kind, allowed, required, absolute_offset)
    _LOGGER.debug("_resource_exception_v1 exit")
    return result


_RESOURCE_EXCEPTION = _resource_exception_v1
_RESOURCE_EXCEPTION_CODE = _RESOURCE_EXCEPTION.__code__


def _root_v1(label: str, fields: tuple[bytes, ...]) -> bytes:
    _LOGGER.debug("_root_v1 entry fields=%d", len(fields))
    if (
        globals().get("_validate_source_runtime_v1") is not _VALIDATE_SOURCE_RUNTIME
        or _VALIDATE_SOURCE_RUNTIME.__code__ is not _VALIDATE_SOURCE_RUNTIME_CODE
        or globals().get("_frame") is not _FRAME
        or _FRAME.__code__ is not _FRAME_CODE
    ):
        _LOGGER.error("_root_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-root-helper-integrity")
    _VALIDATE_SOURCE_RUNTIME()
    if (
        type(label) is not str
        or type(fields) is not tuple
        or any(type(field) is not bytes for field in fields)
    ):
        _LOGGER.error("_root_v1 error host-shape")
        _INTEGRITY_ERROR("kci1-root-host-shape")
    if _UNICODE_NORMALIZE_FROZEN("NFC", label) != label:
        _LOGGER.error("_root_v1 error normalization")
        _INTEGRITY_ERROR("kci1-root-label-normalization")
    encoded = label.encode("utf-8", errors="strict")
    result = _SHA256_FROZEN(
        _FRAME(encoded) + b"".join(_FRAME(field) for field in fields)
    ).digest()
    _LOGGER.debug("_root_v1 exit")
    return result


_ROOT = _root_v1
_ROOT_CODE = _ROOT.__code__


def _validate_manifest_path_v1(name: str) -> tuple[str, ...]:
    _LOGGER.debug("_validate_manifest_path_v1 entry")
    if (
        globals().get("_validate_source_runtime_v1") is not _VALIDATE_SOURCE_RUNTIME
        or _VALIDATE_SOURCE_RUNTIME.__code__ is not _VALIDATE_SOURCE_RUNTIME_CODE
    ):
        _LOGGER.error("_validate_manifest_path_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-manifest-path-helper-integrity")
    _VALIDATE_SOURCE_RUNTIME()
    if type(name) is not str or _UNICODE_NORMALIZE_FROZEN("NFC", name) != name:
        _LOGGER.error("_validate_manifest_path_v1 error text")
        _INTEGRITY_ERROR("kci1-manifest-path-text")
    parts = tuple(name.split("/"))
    if (
        not parts
        or name.startswith("/")
        or any(part in {"", ".", ".."} for part in parts)
        or "/".join(parts) != name
    ):
        _LOGGER.error("_validate_manifest_path_v1 error relative")
        _INTEGRITY_ERROR("kci1-manifest-path-relative")
    _LOGGER.debug("_validate_manifest_path_v1 exit")
    return parts


_VALIDATE_MANIFEST_PATH = _validate_manifest_path_v1
_VALIDATE_MANIFEST_PATH_CODE = _VALIDATE_MANIFEST_PATH.__code__


def _close_fd_v1(file_descriptor: int) -> None:
    _LOGGER.debug("_close_fd_v1 entry fd=%d", file_descriptor)
    if type(file_descriptor) is not int or file_descriptor < 0:
        _LOGGER.error("_close_fd_v1 error fd")
        _INTEGRITY_ERROR("kci1-close-fd-integrity")
    try:
        _LOGGER.debug("_close_fd_v1 external_call=os.close")
        _OS_CLOSE_FROZEN(file_descriptor)
    except OSError as exc:
        _LOGGER.error("_close_fd_v1 error os=%s", type(exc).__name__)
        _INTEGRITY_ERROR("kci1-manifest-close-integrity")
    _LOGGER.debug("_close_fd_v1 exit")


_CLOSE_FD = _close_fd_v1
_CLOSE_FD_CODE = _CLOSE_FD.__code__


def _open_repository_root_v1(repository_root: Path) -> int:
    """Open every absolute root component with O_NOFOLLOW and dirfds."""
    _LOGGER.debug("_open_repository_root_v1 entry")
    if (
        globals().get("_validate_source_runtime_v1") is not _VALIDATE_SOURCE_RUNTIME
        or _VALIDATE_SOURCE_RUNTIME.__code__ is not _VALIDATE_SOURCE_RUNTIME_CODE
        or globals().get("_close_fd_v1") is not _CLOSE_FD
        or _CLOSE_FD.__code__ is not _CLOSE_FD_CODE
    ):
        _LOGGER.error("_open_repository_root_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-root-open-helper-integrity")
    _VALIDATE_SOURCE_RUNTIME()
    if type(repository_root) is not _REPOSITORY_ROOT_TYPE:
        _LOGGER.error("_open_repository_root_v1 error root-type")
        _INTEGRITY_ERROR("kci1-manifest-root-integrity")
    parts = _PATH_PARTS_GETTER(repository_root)
    if (
        type(parts) is not tuple
        or not parts
        or parts[0] != _SEPARATOR_FROZEN
        or any(type(part) is not str or part in {"", ".", ".."} for part in parts[1:])
    ):
        _LOGGER.error("_open_repository_root_v1 error absolute-root")
        _INTEGRITY_ERROR("kci1-manifest-root-integrity")
    directory_fd = -1
    try:
        _LOGGER.debug("_open_repository_root_v1 external_call=os.open-anchor")
        directory_fd = _OS_OPEN_FROZEN(
            _SEPARATOR_FROZEN,
            _OPEN_FLAGS_FROZEN | _DIRECTORY_FLAG_FROZEN,
        )
        for part in parts[1:]:
            _LOGGER.debug("_open_repository_root_v1 external_call=os.open-component")
            next_fd = _OS_OPEN_FROZEN(
                part,
                _OPEN_FLAGS_FROZEN | _DIRECTORY_FLAG_FROZEN,
                dir_fd=directory_fd,
            )
            _CLOSE_FD(directory_fd)
            directory_fd = next_fd
    except OSError as exc:
        _LOGGER.error("_open_repository_root_v1 error os=%s", type(exc).__name__)
        if directory_fd >= 0:
            _CLOSE_FD(directory_fd)
        _INTEGRITY_ERROR("kci1-manifest-root-integrity")
    _LOGGER.debug("_open_repository_root_v1 exit")
    return directory_fd


_OPEN_REPOSITORY_ROOT = _open_repository_root_v1
_OPEN_REPOSITORY_ROOT_CODE = _OPEN_REPOSITORY_ROOT.__code__


def _read_manifest_file_v1(repository_root: Path, parts: tuple[str, ...]) -> bytes:
    """Read one raw regular file through componentwise no-follow dirfds."""
    _LOGGER.debug("_read_manifest_file_v1 entry")
    if (
        globals().get("_validate_source_runtime_v1") is not _VALIDATE_SOURCE_RUNTIME
        or _VALIDATE_SOURCE_RUNTIME.__code__ is not _VALIDATE_SOURCE_RUNTIME_CODE
        or globals().get("_open_repository_root_v1") is not _OPEN_REPOSITORY_ROOT
        or _OPEN_REPOSITORY_ROOT.__code__ is not _OPEN_REPOSITORY_ROOT_CODE
        or globals().get("_close_fd_v1") is not _CLOSE_FD
        or _CLOSE_FD.__code__ is not _CLOSE_FD_CODE
    ):
        _LOGGER.error("_read_manifest_file_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-manifest-read-helper-integrity")
    _VALIDATE_SOURCE_RUNTIME()
    if (
        type(parts) is not tuple
        or not parts
        or any(type(part) is not str or part in {"", ".", ".."} for part in parts)
    ):
        _LOGGER.error("_read_manifest_file_v1 error parts")
        _INTEGRITY_ERROR("kci1-manifest-path-integrity")
    directory_fd = -1
    file_fd = -1
    result = b""
    try:
        directory_fd = _OPEN_REPOSITORY_ROOT(repository_root)
        for part in parts[:-1]:
            _LOGGER.debug("_read_manifest_file_v1 external_call=os.open-directory")
            next_fd = _OS_OPEN_FROZEN(
                part,
                _OPEN_FLAGS_FROZEN | _DIRECTORY_FLAG_FROZEN,
                dir_fd=directory_fd,
            )
            _CLOSE_FD(directory_fd)
            directory_fd = next_fd
        _LOGGER.debug("_read_manifest_file_v1 external_call=os.open-file")
        file_fd = _OS_OPEN_FROZEN(parts[-1], _OPEN_FLAGS_FROZEN, dir_fd=directory_fd)
        _LOGGER.debug("_read_manifest_file_v1 external_call=os.fstat-before")
        before = _OS_FSTAT_FROZEN(file_fd)
        if not _STAT_ISREG_FROZEN(before.st_mode):
            _LOGGER.error("_read_manifest_file_v1 error nonregular")
            _INTEGRITY_ERROR("kci1-manifest-path-integrity")
        chunks: list[bytes] = []
        while True:
            _LOGGER.debug("_read_manifest_file_v1 external_call=os.read")
            chunk = _OS_READ_FROZEN(file_fd, 131_072)
            if not chunk:
                break
            chunks.append(chunk)
        _LOGGER.debug("_read_manifest_file_v1 external_call=os.fstat-after")
        after = _OS_FSTAT_FROZEN(file_fd)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if before_identity != after_identity:
            _LOGGER.error("_read_manifest_file_v1 error read-drift")
            _INTEGRITY_ERROR("kci1-manifest-read-drift")
        result = b"".join(chunks)
    except OSError as exc:
        _LOGGER.error("_read_manifest_file_v1 error os=%s", type(exc).__name__)
        _INTEGRITY_ERROR("kci1-manifest-path-integrity")
    finally:
        if file_fd >= 0:
            _CLOSE_FD(file_fd)
        if directory_fd >= 0:
            _CLOSE_FD(directory_fd)
    _LOGGER.debug("_read_manifest_file_v1 exit bytes=%d", len(result))
    return result


_READ_MANIFEST_FILE = _read_manifest_file_v1
_READ_MANIFEST_FILE_CODE = _READ_MANIFEST_FILE.__code__


def _source_manifest_v1(
    paths: tuple[str, ...] = _SOURCE_PATHS_FROZEN,
    repository_root: Path = _REPOSITORY_ROOT_FROZEN,
) -> bytes:
    _LOGGER.debug("_source_manifest_v1 entry")
    if (
        globals().get("_source_manifest_v1") is not _SOURCE_MANIFEST
        or _SOURCE_MANIFEST.__code__ is not _SOURCE_MANIFEST_CODE
        or _SOURCE_MANIFEST.__defaults__ is not _SOURCE_MANIFEST_DEFAULTS
        or type(_SOURCE_MANIFEST_DEFAULTS) is not tuple
        or len(_SOURCE_MANIFEST_DEFAULTS) != 2
        or _SOURCE_MANIFEST_DEFAULTS[0] is not _SOURCE_PATHS_FROZEN
        or _SOURCE_MANIFEST_DEFAULTS[1] is not _REPOSITORY_ROOT_FROZEN
        or globals().get("_validate_source_runtime_v1") is not _VALIDATE_SOURCE_RUNTIME
        or _VALIDATE_SOURCE_RUNTIME.__code__ is not _VALIDATE_SOURCE_RUNTIME_CODE
        or globals().get("_validate_manifest_path_v1") is not _VALIDATE_MANIFEST_PATH
        or _VALIDATE_MANIFEST_PATH.__code__ is not _VALIDATE_MANIFEST_PATH_CODE
        or globals().get("_read_manifest_file_v1") is not _READ_MANIFEST_FILE
        or _READ_MANIFEST_FILE.__code__ is not _READ_MANIFEST_FILE_CODE
        or globals().get("_frame") is not _FRAME
        or _FRAME.__code__ is not _FRAME_CODE
    ):
        _LOGGER.error("_source_manifest_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-manifest-helper-integrity")
    _VALIDATE_SOURCE_RUNTIME()
    if (
        type(paths) is not tuple
        or any(type(name) is not str for name in paths)
        or paths != _SOURCE_PATHS_FROZEN
        or paths != tuple(sorted(paths))
        or len(paths) != len(set(paths))
        or type(repository_root) is not _REPOSITORY_ROOT_TYPE
    ):
        _LOGGER.error("_source_manifest_v1 error closed-input")
        _INTEGRITY_ERROR("kci1-manifest-closed-input")
    chunks: list[bytes] = []
    for name in paths:
        parts = _VALIDATE_MANIFEST_PATH(name)
        encoded = name.encode("utf-8", errors="strict")
        chunks.append(
            _FRAME(encoded) + _FRAME(_READ_MANIFEST_FILE(repository_root, parts))
        )
    result = _U64(len(paths)) + b"".join(chunks)
    _LOGGER.debug("_source_manifest_v1 exit bytes=%d", len(result))
    return result


_SOURCE_MANIFEST = _source_manifest_v1
_SOURCE_MANIFEST_CODE = _SOURCE_MANIFEST.__code__
_SOURCE_MANIFEST_DEFAULTS = _SOURCE_MANIFEST.__defaults__


def kci1_source_root_v1() -> bytes:
    """Recompute the exact independent five-file KCI1 source root."""
    _LOGGER.debug("kci1_source_root_v1 entry")
    if (
        globals().get("kci1_source_root_v1") is not _SOURCE_ROOT_PUBLIC
        or _SOURCE_ROOT_PUBLIC.__code__ is not _SOURCE_ROOT_PUBLIC_CODE
        or globals().get("_validate_codec_integrity_v1") is not _VALIDATE_LOCAL
        or _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
        or globals().get("_root_v1") is not _ROOT
        or _ROOT.__code__ is not _ROOT_CODE
        or globals().get("_source_manifest_v1") is not _SOURCE_MANIFEST
        or _SOURCE_MANIFEST.__code__ is not _SOURCE_MANIFEST_CODE
        or _SOURCE_MANIFEST.__defaults__ is not _SOURCE_MANIFEST_DEFAULTS
        or globals().get("_validate_source_runtime_v1") is not _VALIDATE_SOURCE_RUNTIME
        or _VALIDATE_SOURCE_RUNTIME.__code__ is not _VALIDATE_SOURCE_RUNTIME_CODE
    ):
        _LOGGER.error("kci1_source_root_v1 error helper-drift")
        _INTEGRITY_ERROR("kci1-source-root-helper-integrity")
    _VALIDATE_LOCAL()
    result = _ROOT(
        "omegaa.kci1-source.v1",
        (_SOURCE_MANIFEST(_SOURCE_PATHS_FROZEN, _REPOSITORY_ROOT_FROZEN),),
    )
    _LOGGER.debug("kci1_source_root_v1 exit")
    return result


_SOURCE_ROOT_PUBLIC = kci1_source_root_v1
_SOURCE_ROOT_PUBLIC_CODE = _SOURCE_ROOT_PUBLIC.__code__
