"""Canonical KCC1 singleton encoder and manifest-only dynamic identities."""

from __future__ import annotations

from hashlib import sha256
import logging
import os
from pathlib import Path, PurePosixPath
import stat
import unicodedata

from . import omegaa_kcc1_common as _common
from . import omegaa_kcc1_types as _syntax
from .omegaa_kcc1_builder import (
    build_empty_checker_config_v1,
    validate_kcc1_builder_integrity_v1,
)
from .omegaa_kcc1_common import (
    DEFAULT_KCC1_LIMITS_V1,
    KCC1_PREFIX,
    MAX_OUTPUT,
    KCC1LimitsV1,
    KCC1ResourceKindV1,
    _integrity_error,
    _resource,
    _snapshot_limits,
    validate_kcc1_common_integrity_v1,
)
from .omegaa_kcc1_types import EMPTY_CHECKER_CONFIG_V1, EmptyCheckerConfigV1

logger = logging.getLogger(__name__)
_LOGGER = logger
_SYNTAX_MODULE = _syntax
_COMMON_MODULE = _common
_PREFIX_ALIAS = KCC1_PREFIX
_WIRE_LITERAL = b"KCC1\x00\x00"
_WIRE_FROZEN = _WIRE_LITERAL
_SINGLETON = EMPTY_CHECKER_CONFIG_V1
_CONFIG_CLASS = EmptyCheckerConfigV1
_BUILD = build_empty_checker_config_v1
_BUILD_CODE = _BUILD.__code__
_VALIDATE_BUILDER = validate_kcc1_builder_integrity_v1
_VALIDATE_BUILDER_CODE = _VALIDATE_BUILDER.__code__
_VALIDATE_COMMON = validate_kcc1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON.__code__
_INTEGRITY_ERROR = _integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__
_RESOURCE = _resource
_RESOURCE_CODE = _RESOURCE.__code__
_RESOURCE_KIND_CLASS = KCC1ResourceKindV1
_MAX_OUTPUT = MAX_OUTPUT
_SNAPSHOT_LIMITS = _snapshot_limits
_SNAPSHOT_LIMITS_CODE = _SNAPSHOT_LIMITS.__code__
_REPOSITORY_ROOT = Path(__file__).parents[2]
KCC1_SOURCE_PATHS_V1 = (
    "src/core/omegaa_kcc1_builder.py",
    "src/core/omegaa_kcc1_codec.py",
    "src/core/omegaa_kcc1_common.py",
    "src/core/omegaa_kcc1_parser.py",
    "src/core/omegaa_kcc1_types.py",
)
_SOURCE_PATHS_FROZEN = KCC1_SOURCE_PATHS_V1


def _validate_codec_integrity_v1() -> None:
    _LOGGER.debug("_validate_codec_integrity_v1 entry")
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("_syntax") is not _SYNTAX_MODULE
        or globals().get("_common") is not _COMMON_MODULE
        or vars(_SYNTAX_MODULE).get("EmptyCheckerConfigV1") is not _CONFIG_CLASS
        or vars(_SYNTAX_MODULE).get("EMPTY_CHECKER_CONFIG_V1") is not _SINGLETON
        or globals().get("EmptyCheckerConfigV1") is not _CONFIG_CLASS
        or globals().get("EMPTY_CHECKER_CONFIG_V1") is not _SINGLETON
        or globals().get("build_empty_checker_config_v1") is not _BUILD
        or _BUILD.__code__ is not _BUILD_CODE
        or globals().get("validate_kcc1_builder_integrity_v1") is not _VALIDATE_BUILDER
        or _VALIDATE_BUILDER.__code__ is not _VALIDATE_BUILDER_CODE
        or globals().get("validate_kcc1_common_integrity_v1") is not _VALIDATE_COMMON
        or _VALIDATE_COMMON.__code__ is not _VALIDATE_COMMON_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or globals().get("_resource") is not _RESOURCE
        or _RESOURCE.__code__ is not _RESOURCE_CODE
        or globals().get("KCC1ResourceKindV1") is not _RESOURCE_KIND_CLASS
        or _COMMON_MODULE.KCC1ResourceKindV1 is not _RESOURCE_KIND_CLASS
        or globals().get("MAX_OUTPUT") is not _MAX_OUTPUT
        or _MAX_OUTPUT != 1
        or globals().get("_snapshot_limits") is not _SNAPSHOT_LIMITS
        or _SNAPSHOT_LIMITS.__code__ is not _SNAPSHOT_LIMITS_CODE
        or globals().get("_source_manifest_v1") is not _SOURCE_MANIFEST
        or _SOURCE_MANIFEST.__code__ is not _SOURCE_MANIFEST_CODE
        or globals().get("KCC1_SOURCE_PATHS_V1") is not _SOURCE_PATHS_FROZEN
        or globals().get("KCC1_PREFIX") is not _PREFIX_ALIAS
        or _PREFIX_ALIAS is not _COMMON_MODULE.KCC1_PREFIX
        or _COMMON_MODULE.KCC1_PREFIX != b"KCC1"
        or globals().get("_WIRE_FROZEN") is not _WIRE_LITERAL
    )
    if drift:
        _LOGGER.error("_validate_codec_integrity_v1 error drift")
        _INTEGRITY_ERROR("kcc1-codec-integrity")
    _VALIDATE_BUILDER()
    _VALIDATE_COMMON()
    _LOGGER.debug("_validate_codec_integrity_v1 exit")


_VALIDATE_LOCAL = _validate_codec_integrity_v1
_VALIDATE_LOCAL_CODE = _VALIDATE_LOCAL.__code__


def codec_empty_checker_config_v1(
    config: EmptyCheckerConfigV1,
    limits: KCC1LimitsV1 = DEFAULT_KCC1_LIMITS_V1,
) -> bytes:
    """Encode exactly the captured inert singleton and nothing else."""
    _LOGGER.debug("codec_empty_checker_config_v1 entry")
    if (
        globals().get("_validate_codec_integrity_v1") is not _VALIDATE_LOCAL
        or _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
    ):
        _INTEGRITY_ERROR("kcc1-codec-validator-integrity")
    _VALIDATE_LOCAL()
    if config is not _SINGLETON:
        _LOGGER.error("codec_empty_checker_config_v1 error singleton-identity")
        _INTEGRITY_ERROR("kcc1-config-singleton-identity")
    values = _SNAPSHOT_LIMITS(limits)
    if len(_WIRE_FROZEN) > values[_MAX_OUTPUT]:
        _RESOURCE(
            _RESOURCE_KIND_CLASS.OUTPUT_BYTES,
            values[_MAX_OUTPUT],
            len(_WIRE_FROZEN),
            0,
        )
    _LOGGER.debug("codec_empty_checker_config_v1 exit bytes=%d", len(_WIRE_FROZEN))
    return _WIRE_FROZEN


def _u64(value: int) -> bytes:
    _LOGGER.debug("_u64 entry value=%d", value)
    if type(value) is not int or not 0 <= value < 2**64:
        _LOGGER.error("_u64 error range")
        _INTEGRITY_ERROR("kcc1-u64-range")
    result = value.to_bytes(8, "big")
    _LOGGER.debug("_u64 exit")
    return result


_U64 = _u64
_U64_CODE = _U64.__code__


def _frame(value: bytes) -> bytes:
    _LOGGER.debug("_frame entry")
    if type(value) is not bytes:
        _LOGGER.error("_frame error type")
        _INTEGRITY_ERROR("kcc1-frame-type")
    if globals().get("_u64") is not _U64 or _U64.__code__ is not _U64_CODE:
        _INTEGRITY_ERROR("kcc1-u64-integrity")
    result = _U64(len(value)) + value
    _LOGGER.debug("_frame exit bytes=%d", len(result))
    return result


_FRAME = _frame
_FRAME_CODE = _FRAME.__code__


def _root_v1(label: str, fields: tuple[bytes, ...]) -> bytes:
    _LOGGER.debug("_root_v1 entry fields=%d", len(fields))
    if type(label) is not str or type(fields) is not tuple or any(type(field) is not bytes for field in fields):
        _LOGGER.error("_root_v1 error host-shape")
        _INTEGRITY_ERROR("kcc1-root-host-shape")
    encoded = label.encode("utf-8", errors="strict")
    if unicodedata.normalize("NFC", label) != label:
        _LOGGER.error("_root_v1 error label-normalization")
        _INTEGRITY_ERROR("kcc1-root-label-normalization")
    if globals().get("_frame") is not _FRAME or _FRAME.__code__ is not _FRAME_CODE:
        _INTEGRITY_ERROR("kcc1-frame-integrity")
    result = sha256(_FRAME(encoded) + b"".join(_FRAME(field) for field in fields)).digest()
    _LOGGER.debug("_root_v1 exit")
    return result


_ROOT = _root_v1
_ROOT_CODE = _ROOT.__code__


def _validate_manifest_path_v1(name: str) -> PurePosixPath:
    _LOGGER.debug("_validate_manifest_path_v1 entry")
    if type(name) is not str or unicodedata.normalize("NFC", name) != name:
        _LOGGER.error("_validate_manifest_path_v1 error text")
        _INTEGRITY_ERROR("kcc1-manifest-path-text")
    pure = PurePosixPath(name)
    if pure.is_absolute() or str(pure) != name or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        _LOGGER.error("_validate_manifest_path_v1 error relative")
        _INTEGRITY_ERROR("kcc1-manifest-path-relative")
    _LOGGER.debug("_validate_manifest_path_v1 exit")
    return pure


_VALIDATE_MANIFEST_PATH = _validate_manifest_path_v1
_VALIDATE_MANIFEST_PATH_CODE = _VALIDATE_MANIFEST_PATH.__code__


def _read_manifest_file_v1(repository_root: Path, pure: PurePosixPath) -> bytes:
    """Read one regular file through componentwise no-follow directory FDs."""
    _LOGGER.debug("_read_manifest_file_v1 entry")
    directory_fd = -1
    file_fd = -1
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        directory_fd = os.open(repository_root, flags | os.O_DIRECTORY)
        for part in pure.parts[:-1]:
            next_fd = os.open(part, flags | os.O_DIRECTORY, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(pure.parts[-1], flags, dir_fd=directory_fd)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            _INTEGRITY_ERROR("kcc1-manifest-path-integrity")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, 131_072)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(file_fd)
        before_identity = (
            before.st_dev, before.st_ino, before.st_size,
            before.st_mtime_ns, before.st_ctime_ns,
        )
        after_identity = (
            after.st_dev, after.st_ino, after.st_size,
            after.st_mtime_ns, after.st_ctime_ns,
        )
        if before_identity != after_identity:
            _INTEGRITY_ERROR("kcc1-manifest-read-drift")
        result = b"".join(chunks)
    except OSError as exc:
        _LOGGER.error("_read_manifest_file_v1 error os=%s", type(exc).__name__)
        _INTEGRITY_ERROR("kcc1-manifest-path-integrity")
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if directory_fd >= 0:
            os.close(directory_fd)
    _LOGGER.debug("_read_manifest_file_v1 exit bytes=%d", len(result))
    return result


_READ_MANIFEST_FILE = _read_manifest_file_v1
_READ_MANIFEST_FILE_CODE = _READ_MANIFEST_FILE.__code__


def _source_manifest_v1(
    paths: tuple[str, ...] = _SOURCE_PATHS_FROZEN,
    repository_root: Path = _REPOSITORY_ROOT,
) -> bytes:
    _LOGGER.debug("_source_manifest_v1 entry")
    if (
        type(paths) is not tuple
        or paths != _SOURCE_PATHS_FROZEN
        or paths != tuple(sorted(paths))
        or len(paths) != len(set(paths))
        or type(repository_root) is not type(_REPOSITORY_ROOT)
        or not repository_root.is_absolute()
    ):
        _LOGGER.error("_source_manifest_v1 error closed-input")
        _INTEGRITY_ERROR("kcc1-manifest-closed-input")
    chunks: list[bytes] = []
    for name in paths:
        if (
            globals().get("_validate_manifest_path_v1") is not _VALIDATE_MANIFEST_PATH
            or _VALIDATE_MANIFEST_PATH.__code__ is not _VALIDATE_MANIFEST_PATH_CODE
            or globals().get("_read_manifest_file_v1") is not _READ_MANIFEST_FILE
            or _READ_MANIFEST_FILE.__code__ is not _READ_MANIFEST_FILE_CODE
            or globals().get("_frame") is not _FRAME
            or _FRAME.__code__ is not _FRAME_CODE
        ):
            _INTEGRITY_ERROR("kcc1-manifest-helper-integrity")
        pure = _VALIDATE_MANIFEST_PATH(name)
        encoded = name.encode("utf-8", errors="strict")
        chunks.append(_FRAME(encoded) + _FRAME(_READ_MANIFEST_FILE(repository_root, pure)))
    result = _U64(len(paths)) + b"".join(chunks)
    _LOGGER.debug("_source_manifest_v1 exit bytes=%d", len(result))
    return result


_SOURCE_MANIFEST = _source_manifest_v1
_SOURCE_MANIFEST_CODE = _SOURCE_MANIFEST.__code__


def kcc1_source_root_v1() -> bytes:
    """Recompute the exact five-file manifest-only KCC1 source root."""
    _LOGGER.debug("kcc1_source_root_v1 entry")
    if (
        globals().get("_validate_codec_integrity_v1") is not _VALIDATE_LOCAL
        or _VALIDATE_LOCAL.__code__ is not _VALIDATE_LOCAL_CODE
        or globals().get("_root_v1") is not _ROOT
        or _ROOT.__code__ is not _ROOT_CODE
    ):
        _INTEGRITY_ERROR("kcc1-source-root-helper-integrity")
    _VALIDATE_LOCAL()
    result = _ROOT("omegaa.kcc1-empty-source.v1", (_SOURCE_MANIFEST(),))
    _LOGGER.debug("kcc1_source_root_v1 exit")
    return result


_SOURCE_ROOT = kcc1_source_root_v1
_SOURCE_ROOT_CODE = _SOURCE_ROOT.__code__


def kcc1_empty_config_id_v1() -> bytes:
    """Bind the dynamic KCC1 source root to the exact six-byte syntax."""
    _LOGGER.debug("kcc1_empty_config_id_v1 entry")
    if (
        globals().get("kcc1_source_root_v1") is not _SOURCE_ROOT
        or _SOURCE_ROOT.__code__ is not _SOURCE_ROOT_CODE
        or globals().get("_root_v1") is not _ROOT
        or _ROOT.__code__ is not _ROOT_CODE
    ):
        _INTEGRITY_ERROR("kcc1-config-id-helper-integrity")
    source_root = _SOURCE_ROOT()
    result = _ROOT("omegaa.kcc1-empty-config.v1", (source_root, _WIRE_FROZEN))
    _LOGGER.debug("kcc1_empty_config_id_v1 exit")
    return result
