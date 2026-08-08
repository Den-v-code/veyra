"""KIE1 integrity channel, exact enums, U64 arithmetic, and source identity."""

from __future__ import annotations

from enum import IntEnum
from hashlib import sha256
import logging
import os
from pathlib import Path, PurePosixPath
import stat
from typing import NoReturn
import unicodedata

from . import omegaa_kci1_codec as _kci_codec
from . import omegaa_keb1_codec as _keb_codec

logger = logging.getLogger(__name__)
_LOGGER = logger
U64_LIMIT = 18_446_744_073_709_551_616
_U64_LIMIT = U64_LIMIT


class KIEPrepareCodeV1(IntEnum):
    """The sole normal KIE1 preparation failure."""

    EXPECTED_WIRE_MISMATCH = 0


class KIEPayloadOriginV1(IntEnum):
    """Which opaque KCI1 payload owns a relative KPT origin."""

    EXPECTED = 0
    TERM = 1


class KIE1IntegrityErrorV1(ValueError):
    """Sanitized host, alias, arithmetic, or captured-object failure."""

    def __init__(self, reason: str) -> None:
        _LOGGER.debug("KIE1IntegrityErrorV1.__init__ entry")
        if type(reason) is not str:
            _LOGGER.error("KIE1IntegrityErrorV1.__init__ error reason-type")
            raise TypeError("invalid KIE1 integrity reason")
        self.reason = reason
        ValueError.__init__(self, reason)
        _LOGGER.error("KIE1 integrity rejected reason=%s", reason)
        _LOGGER.debug("KIE1IntegrityErrorV1.__init__ exit")


_PREPARE_CODE_CLASS = KIEPrepareCodeV1
_ORIGIN_CLASS = KIEPayloadOriginV1
_PREPARE_CODES_FROZEN = (KIEPrepareCodeV1.EXPECTED_WIRE_MISMATCH,)
_PREPARE_CODES = _PREPARE_CODES_FROZEN
_ORIGINS_FROZEN = (KIEPayloadOriginV1.EXPECTED, KIEPayloadOriginV1.TERM)
_ORIGINS = _ORIGINS_FROZEN
_INTEGRITY_CLASS = KIE1IntegrityErrorV1
_INTEGRITY_INIT = vars(_INTEGRITY_CLASS)["__init__"]
_INTEGRITY_INIT_CODE = _INTEGRITY_INIT.__code__


def _integrity_error(reason: str) -> NoReturn:
    """Raise the frozen KIE1 integrity type without a mutable class hook."""
    _LOGGER.debug("_integrity_error entry reason=%s", reason)
    error = ValueError.__new__(_INTEGRITY_CLASS)
    object.__setattr__(error, "reason", reason)
    ValueError.__init__(error, reason)
    _LOGGER.error("KIE1 integrity rejected reason=%s", reason)
    raise error


_INTEGRITY_ERROR = _integrity_error
_INTEGRITY_ERROR_CODE = _INTEGRITY_ERROR.__code__


def validate_kie1_common_integrity_v1() -> None:
    """Refuse logger, enum, error-class, ordinal, or U64 drift."""
    _LOGGER.debug("validate_kie1_common_integrity_v1 entry")
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("U64_LIMIT") is not _U64_LIMIT
        or _U64_LIMIT != 18_446_744_073_709_551_616
        or globals().get("KIEPrepareCodeV1") is not _PREPARE_CODE_CLASS
        or globals().get("KIEPayloadOriginV1") is not _ORIGIN_CLASS
        or globals().get("KIE1IntegrityErrorV1") is not _INTEGRITY_CLASS
        or vars(_INTEGRITY_CLASS).get("__init__") is not _INTEGRITY_INIT
        or _INTEGRITY_INIT.__code__ is not _INTEGRITY_INIT_CODE
        or globals().get("_integrity_error") is not _INTEGRITY_ERROR
        or _INTEGRITY_ERROR.__code__ is not _INTEGRITY_ERROR_CODE
        or globals().get("_PREPARE_CODES") is not _PREPARE_CODES_FROZEN
        or globals().get("_ORIGINS") is not _ORIGINS_FROZEN
        or len(_PREPARE_CODES_FROZEN) != 1
        or len(_ORIGINS_FROZEN) != 2
        or any(
            type(value) is not _PREPARE_CODE_CLASS
            or value is not _PREPARE_CODE_CLASS(index)
            or object.__getattribute__(value, "_value_") != index
            for index, value in enumerate(_PREPARE_CODES_FROZEN)
        )
        or any(
            type(value) is not _ORIGIN_CLASS
            or value is not _ORIGIN_CLASS(index)
            or object.__getattribute__(value, "_value_") != index
            for index, value in enumerate(_ORIGINS_FROZEN)
        )
    )
    if drift:
        _LOGGER.error("validate_kie1_common_integrity_v1 error drift")
        _INTEGRITY_ERROR("kie1-common-integrity")
    _LOGGER.debug("validate_kie1_common_integrity_v1 exit")


_VALIDATE_COMMON = validate_kie1_common_integrity_v1
_VALIDATE_COMMON_CODE = _VALIDATE_COMMON.__code__


def _checked_u64(value: int, label: str) -> int:
    """Return one exact unsigned 64-bit host integer."""
    _LOGGER.debug("_checked_u64 entry label=%s", label)
    _VALIDATE_COMMON()
    if type(value) is not int or not 0 <= value < _U64_LIMIT:
        _LOGGER.error("_checked_u64 error label=%s", label)
        _INTEGRITY_ERROR(f"kie1-{label}-u64")
    _LOGGER.debug("_checked_u64 exit label=%s", label)
    return value


_CHECKED_U64_FROZEN = _checked_u64
_CHECKED_U64 = _CHECKED_U64_FROZEN
_CHECKED_U64_CODE = _CHECKED_U64_FROZEN.__code__


def _checked_add_u64(left: int, right: int, label: str) -> int:
    """Add two exact U64 values and refuse overflow."""
    _LOGGER.debug("_checked_add_u64 entry label=%s", label)
    if (
        globals().get("_checked_u64") is not _CHECKED_U64
        or _CHECKED_U64.__code__ is not _CHECKED_U64_CODE
    ):
        _INTEGRITY_ERROR("kie1-u64-helper-integrity")
    checked_left = _CHECKED_U64(left, f"{label}-left")
    checked_right = _CHECKED_U64(right, f"{label}-right")
    result = checked_left + checked_right
    if result >= _U64_LIMIT:
        _LOGGER.error("_checked_add_u64 error overflow label=%s", label)
        _INTEGRITY_ERROR(f"kie1-{label}-overflow")
    _LOGGER.debug("_checked_add_u64 exit label=%s", label)
    return result


_CHECKED_ADD = _checked_add_u64
_CHECKED_ADD_CODE = _CHECKED_ADD.__code__


KIE1_SOURCE_PATHS_V1 = (
    "src/core/omegaa_kie1_binding.py",
    "src/core/omegaa_kie1_common.py",
    "src/core/omegaa_kie1_offsets.py",
    "src/core/omegaa_kie1_prepare.py",
    "src/core/omegaa_kie1_types.py",
)
_SOURCE_PATHS_FROZEN = KIE1_SOURCE_PATHS_V1
_SOURCE_PATHS = _SOURCE_PATHS_FROZEN
_REPOSITORY_ROOT_FROZEN = Path(__file__).parents[2]
_REPOSITORY_ROOT = _REPOSITORY_ROOT_FROZEN
_PATH_CLASS = type(_REPOSITORY_ROOT)
_PATH_FACTORY_FROZEN = Path
_PATH_FACTORY = _PATH_FACTORY_FROZEN
_PURE_PATH_FACTORY_FROZEN = PurePosixPath
_PURE_PATH_FACTORY = _PURE_PATH_FACTORY_FROZEN
_FILE_FROZEN = __file__
_KPT1_SOURCE_ROOT_FROZEN = bytes.fromhex(
    "55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a"
)
_KPT1_SOURCE_ROOT = _KPT1_SOURCE_ROOT_FROZEN
_KCI_ROOT_FROZEN = _kci_codec.kci1_source_root_v1
_KCI_ROOT = _KCI_ROOT_FROZEN
_KCI_ROOT_CODE = _KCI_ROOT_FROZEN.__code__
_KEB_ROOT_FROZEN = _keb_codec.keb1_source_root_v1
_KEB_ROOT = _KEB_ROOT_FROZEN
_KEB_ROOT_CODE = _KEB_ROOT_FROZEN.__code__
_SHA256_FROZEN = sha256
_SHA256 = _SHA256_FROZEN
_NORMALIZE_FROZEN = unicodedata.normalize
_NORMALIZE = _NORMALIZE_FROZEN
_OS_MODULE_FROZEN = os
_OS_MODULE = _OS_MODULE_FROZEN
_OS_OPEN_FROZEN, _OS_CLOSE_FROZEN = os.open, os.close
_OS_READ_FROZEN, _OS_FSTAT_FROZEN = os.read, os.fstat
_OS_OPEN, _OS_CLOSE = _OS_OPEN_FROZEN, _OS_CLOSE_FROZEN
_OS_READ, _OS_FSTAT = _OS_READ_FROZEN, _OS_FSTAT_FROZEN
_O_RDONLY_FROZEN = 0
_O_CLOEXEC_FROZEN = 524_288
_O_NOFOLLOW_FROZEN = 131_072
_O_DIRECTORY_FROZEN = 65_536
_FILE_FLAGS_FROZEN = 655_360
_DIRECTORY_FLAGS_FROZEN = 720_896
_ISREG_FROZEN = stat.S_ISREG
_ISREG = _ISREG_FROZEN
_STAT_MODULE_FROZEN = stat
_STAT_MODULE = _STAT_MODULE_FROZEN
_UNICODE_MODULE_FROZEN = unicodedata
_UNICODE_MODULE = _UNICODE_MODULE_FROZEN


def _validate_source_runtime_v1() -> None:
    """Refuse hash, OS, path, Unicode, root, dependency, or manifest drift."""
    _LOGGER.debug("_validate_source_runtime_v1 entry")
    drift = (
        globals().get("logger") is not _LOGGER
        or globals().get("KIE1_SOURCE_PATHS_V1") is not _SOURCE_PATHS_FROZEN
        or globals().get("_SOURCE_PATHS") is not _SOURCE_PATHS_FROZEN
        or _SOURCE_PATHS_FROZEN != tuple(sorted(_SOURCE_PATHS_FROZEN))
        or len(_SOURCE_PATHS_FROZEN) != 5
        or len(set(_SOURCE_PATHS_FROZEN)) != 5
        or globals().get("_REPOSITORY_ROOT") is not _REPOSITORY_ROOT_FROZEN
        or type(_REPOSITORY_ROOT_FROZEN) is not _PATH_CLASS
        or not _REPOSITORY_ROOT_FROZEN.is_absolute()
        or globals().get("_PATH_FACTORY") is not _PATH_FACTORY_FROZEN
        or globals().get("_PURE_PATH_FACTORY") is not _PURE_PATH_FACTORY_FROZEN
        or globals().get("_FILE_FROZEN") != _FILE_FROZEN
        or _REPOSITORY_ROOT_FROZEN != _PATH_FACTORY_FROZEN(_FILE_FROZEN).parents[2]
        or globals().get("_SHA256") is not _SHA256_FROZEN
        or _SHA256_FROZEN is not sha256
        or globals().get("_OS_MODULE") is not _OS_MODULE_FROZEN
        or _OS_MODULE_FROZEN is not os
        or globals().get("_OS_OPEN") is not _OS_OPEN_FROZEN
        or globals().get("_OS_CLOSE") is not _OS_CLOSE_FROZEN
        or globals().get("_OS_READ") is not _OS_READ_FROZEN
        or globals().get("_OS_FSTAT") is not _OS_FSTAT_FROZEN
        or _OS_MODULE_FROZEN.open is not _OS_OPEN_FROZEN
        or _OS_MODULE_FROZEN.close is not _OS_CLOSE_FROZEN
        or _OS_MODULE_FROZEN.read is not _OS_READ_FROZEN
        or _OS_MODULE_FROZEN.fstat is not _OS_FSTAT_FROZEN
        or _OS_MODULE_FROZEN.O_RDONLY != _O_RDONLY_FROZEN
        or _OS_MODULE_FROZEN.O_CLOEXEC != _O_CLOEXEC_FROZEN
        or _OS_MODULE_FROZEN.O_NOFOLLOW != _O_NOFOLLOW_FROZEN
        or _OS_MODULE_FROZEN.O_DIRECTORY != _O_DIRECTORY_FROZEN
        or (_O_RDONLY_FROZEN | _O_CLOEXEC_FROZEN | _O_NOFOLLOW_FROZEN) != _FILE_FLAGS_FROZEN
        or (_FILE_FLAGS_FROZEN | _O_DIRECTORY_FROZEN) != _DIRECTORY_FLAGS_FROZEN
        or globals().get("_STAT_MODULE") is not _STAT_MODULE_FROZEN
        or _STAT_MODULE_FROZEN is not stat
        or globals().get("_ISREG") is not _ISREG_FROZEN
        or _STAT_MODULE_FROZEN.S_ISREG is not _ISREG_FROZEN
        or globals().get("_UNICODE_MODULE") is not _UNICODE_MODULE_FROZEN
        or _UNICODE_MODULE_FROZEN is not unicodedata
        or globals().get("_NORMALIZE") is not _NORMALIZE_FROZEN
        or _UNICODE_MODULE_FROZEN.normalize is not _NORMALIZE_FROZEN
        or globals().get("_KPT1_SOURCE_ROOT") is not _KPT1_SOURCE_ROOT_FROZEN
        or len(_KPT1_SOURCE_ROOT_FROZEN) != 32
        or globals().get("_KCI_ROOT") is not _KCI_ROOT_FROZEN
        or vars(_kci_codec).get("kci1_source_root_v1") is not _KCI_ROOT_FROZEN
        or _KCI_ROOT_FROZEN.__code__ is not _KCI_ROOT_CODE
        or globals().get("_KEB_ROOT") is not _KEB_ROOT_FROZEN
        or vars(_keb_codec).get("keb1_source_root_v1") is not _KEB_ROOT_FROZEN
        or _KEB_ROOT_FROZEN.__code__ is not _KEB_ROOT_CODE
    )
    if drift:
        _LOGGER.error("_validate_source_runtime_v1 error drift")
        _INTEGRITY_ERROR("kie1-source-runtime-integrity")
    _LOGGER.debug("_validate_source_runtime_v1 exit")


_VALIDATE_SOURCE_RUNTIME = _validate_source_runtime_v1
_VALIDATE_SOURCE_RUNTIME_CODE = _VALIDATE_SOURCE_RUNTIME.__code__


def _u64_bytes_v1(value: int) -> bytes:
    """Encode one exact U64 for source-identity framing."""
    _LOGGER.debug("_u64_bytes_v1 entry")
    _VALIDATE_SOURCE_RUNTIME()
    if (
        globals().get("_checked_u64") is not _CHECKED_U64_FROZEN
        or globals().get("_CHECKED_U64") is not _CHECKED_U64_FROZEN
        or _CHECKED_U64_FROZEN.__code__ is not _CHECKED_U64_CODE
    ):
        _LOGGER.error("_u64_bytes_v1 error checked-u64-helper-drift")
        _INTEGRITY_ERROR("kie1-source-u64-helper-integrity")
    result = _CHECKED_U64_FROZEN(value, "source-frame").to_bytes(8, "big")
    _LOGGER.debug("_u64_bytes_v1 exit")
    return result


_U64_BYTES = _u64_bytes_v1
_U64_BYTES_CODE = _U64_BYTES.__code__


def _frame_v1(value: bytes) -> bytes:
    """Frame exact immutable bytes for source identity."""
    _LOGGER.debug("_frame_v1 entry")
    _VALIDATE_SOURCE_RUNTIME()
    if type(value) is not bytes:
        _LOGGER.error("_frame_v1 error value-type")
        _INTEGRITY_ERROR("kie1-frame-host-shape")
    if globals().get("_u64_bytes_v1") is not _U64_BYTES or _U64_BYTES.__code__ is not _U64_BYTES_CODE:
        _INTEGRITY_ERROR("kie1-frame-helper-integrity")
    result = _U64_BYTES(len(value)) + value
    _LOGGER.debug("_frame_v1 exit bytes=%d", len(result))
    return result


_FRAME_FROZEN = _frame_v1
_FRAME = _FRAME_FROZEN
_FRAME_CODE = _FRAME_FROZEN.__code__


def _close_fd_v1(file_descriptor: int) -> None:
    """Close one descriptor and sanitize every OS close failure."""
    _LOGGER.debug("_close_fd_v1 entry fd=%d", file_descriptor)
    _VALIDATE_SOURCE_RUNTIME()
    if type(file_descriptor) is not int or file_descriptor < 0:
        _LOGGER.error("_close_fd_v1 error fd-shape")
        _INTEGRITY_ERROR("kie1-close-fd-shape")
    try:
        _OS_CLOSE_FROZEN(file_descriptor)
    except OSError as exc:
        _LOGGER.error("_close_fd_v1 error os=%s", type(exc).__name__)
        _INTEGRITY_ERROR("kie1-close-fd-integrity")
    _LOGGER.debug("_close_fd_v1 exit")


_CLOSE_FD_FROZEN = _close_fd_v1
_CLOSE_FD = _CLOSE_FD_FROZEN
_CLOSE_FD_CODE = _CLOSE_FD_FROZEN.__code__


def _open_absolute_root_v1(root: Path) -> int:
    """Open every absolute-root component through no-follow directory FDs."""
    _LOGGER.debug("_open_absolute_root_v1 entry")
    _VALIDATE_SOURCE_RUNTIME()
    if type(root) is not _PATH_CLASS or not root.is_absolute():
        _LOGGER.error("_open_absolute_root_v1 error root-shape")
        _INTEGRITY_ERROR("kie1-manifest-root-shape")
    if globals().get("_close_fd_v1") is not _CLOSE_FD_FROZEN or globals().get("_CLOSE_FD") is not _CLOSE_FD_FROZEN or _CLOSE_FD_FROZEN.__code__ is not _CLOSE_FD_CODE:
        _LOGGER.error("_open_absolute_root_v1 error close-helper-drift")
        _INTEGRITY_ERROR("kie1-close-helper-integrity")
    descriptor = -1
    try:
        descriptor = _OS_OPEN_FROZEN("/", _DIRECTORY_FLAGS_FROZEN)
        for component in root.parts[1:]:
            next_descriptor = _OS_OPEN_FROZEN(
                component,
                _DIRECTORY_FLAGS_FROZEN,
                dir_fd=descriptor,
            )
            _CLOSE_FD_FROZEN(descriptor)
            descriptor = next_descriptor
    except OSError as exc:
        _LOGGER.error("_open_absolute_root_v1 error os=%s", type(exc).__name__)
        if descriptor >= 0:
            _CLOSE_FD_FROZEN(descriptor)
        _INTEGRITY_ERROR("kie1-manifest-root-integrity")
    _LOGGER.debug("_open_absolute_root_v1 exit")
    return descriptor


_OPEN_ROOT_FROZEN = _open_absolute_root_v1
_OPEN_ROOT = _OPEN_ROOT_FROZEN
_OPEN_ROOT_CODE = _OPEN_ROOT_FROZEN.__code__


def _read_source_file_v1(root: Path, name: str) -> bytes:
    """Read one exact regular manifest file through componentwise no-follow FDs."""
    _LOGGER.debug("_read_source_file_v1 entry")
    _VALIDATE_SOURCE_RUNTIME()
    if type(root) is not _PATH_CLASS or not root.is_absolute() or type(name) is not str:
        _INTEGRITY_ERROR("kie1-manifest-host-shape")
    if _NORMALIZE("NFC", name) != name:
        _INTEGRITY_ERROR("kie1-manifest-path-text")
    pure = _PURE_PATH_FACTORY(name)
    if pure.is_absolute() or str(pure) != name or any(part in {"", ".", ".."} for part in pure.parts):
        _INTEGRITY_ERROR("kie1-manifest-path-relative")
    directory_fd = -1
    file_fd = -1
    try:
        if globals().get("_open_absolute_root_v1") is not _OPEN_ROOT_FROZEN or globals().get("_OPEN_ROOT") is not _OPEN_ROOT_FROZEN or _OPEN_ROOT_FROZEN.__code__ is not _OPEN_ROOT_CODE:
            _LOGGER.error("_read_source_file_v1 error open-helper-drift")
            _INTEGRITY_ERROR("kie1-open-helper-integrity")
        directory_fd = _OPEN_ROOT_FROZEN(root)
        for part in pure.parts[:-1]:
            next_fd = _OS_OPEN_FROZEN(
                part,
                _DIRECTORY_FLAGS_FROZEN,
                dir_fd=directory_fd,
            )
            _CLOSE_FD_FROZEN(directory_fd)
            directory_fd = next_fd
        file_fd = _OS_OPEN_FROZEN(
            pure.parts[-1],
            _FILE_FLAGS_FROZEN,
            dir_fd=directory_fd,
        )
        before = _OS_FSTAT_FROZEN(file_fd)
        if not _ISREG(before.st_mode):
            _INTEGRITY_ERROR("kie1-manifest-path-integrity")
        chunks: list[bytes] = []
        while True:
            chunk = _OS_READ_FROZEN(file_fd, 131_072)
            if not chunk:
                break
            chunks.append(chunk)
        after = _OS_FSTAT_FROZEN(file_fd)
        if (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns
        ) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns
        ):
            _INTEGRITY_ERROR("kie1-manifest-read-drift")
        result = b"".join(chunks)
    except OSError as exc:
        _LOGGER.error("_read_source_file_v1 error os=%s", type(exc).__name__)
        _INTEGRITY_ERROR("kie1-manifest-path-integrity")
    finally:
        if file_fd >= 0:
            _CLOSE_FD_FROZEN(file_fd)
        if directory_fd >= 0:
            _CLOSE_FD_FROZEN(directory_fd)
    _LOGGER.debug("_read_source_file_v1 exit bytes=%d", len(result))
    return result


_READ_SOURCE = _read_source_file_v1
_READ_SOURCE_CODE = _READ_SOURCE.__code__


def _source_manifest_v1(
    paths: tuple[str, ...] = _SOURCE_PATHS,
    repository_root: Path = _REPOSITORY_ROOT,
) -> bytes:
    """Build the closed five-file KIE1 raw source manifest."""
    _LOGGER.debug("_source_manifest_v1 entry paths=%d", len(paths) if type(paths) is tuple else -1)
    _VALIDATE_SOURCE_RUNTIME()
    if (
        paths is not _SOURCE_PATHS
        or paths != tuple(sorted(paths))
        or len(paths) != len(set(paths))
        or type(repository_root) is not _PATH_CLASS
        or repository_root != _REPOSITORY_ROOT
    ):
        _INTEGRITY_ERROR("kie1-manifest-closed-input")
    if (
        globals().get("_frame_v1") is not _FRAME
        or _FRAME.__code__ is not _FRAME_CODE
        or globals().get("_read_source_file_v1") is not _READ_SOURCE
        or _READ_SOURCE.__code__ is not _READ_SOURCE_CODE
    ):
        _INTEGRITY_ERROR("kie1-manifest-helper-integrity")
    chunks = tuple(
        _FRAME(name.encode("utf-8", errors="strict"))
        + _FRAME(_READ_SOURCE(repository_root, name))
        for name in paths
    )
    result = _U64_BYTES(len(paths)) + b"".join(chunks)
    _LOGGER.debug("_source_manifest_v1 exit bytes=%d", len(result))
    return result


_SOURCE_MANIFEST = _source_manifest_v1
_SOURCE_MANIFEST_CODE = _SOURCE_MANIFEST.__code__
_SOURCE_MANIFEST_DEFAULTS = _SOURCE_MANIFEST.__defaults__


def kie1_source_root_v1() -> bytes:
    """Return RootV1(KPT1,KCI1,KEB1,closed five-file KIE1 manifest)."""
    _LOGGER.debug("kie1_source_root_v1 entry")
    _VALIDATE_SOURCE_RUNTIME()
    if (
        globals().get("kie1_source_root_v1") is not _SOURCE_ROOT_FROZEN
        or _SOURCE_ROOT_FROZEN.__code__ is not _SOURCE_ROOT_CODE
        or globals().get("_frame_v1") is not _FRAME_FROZEN
        or globals().get("_FRAME") is not _FRAME_FROZEN
        or _FRAME_FROZEN.__code__ is not _FRAME_CODE
        or globals().get("_source_manifest_v1") is not _SOURCE_MANIFEST
        or _SOURCE_MANIFEST.__code__ is not _SOURCE_MANIFEST_CODE
        or _SOURCE_MANIFEST.__defaults__ is not _SOURCE_MANIFEST_DEFAULTS
        or vars(_kci_codec).get("kci1_source_root_v1") is not _KCI_ROOT
        or _KCI_ROOT.__code__ is not _KCI_ROOT_CODE
        or vars(_keb_codec).get("keb1_source_root_v1") is not _KEB_ROOT
        or _KEB_ROOT.__code__ is not _KEB_ROOT_CODE
    ):
        _INTEGRITY_ERROR("kie1-source-root-helper-integrity")
    _VALIDATE_COMMON()
    kci_root = _KCI_ROOT()
    keb_root = _KEB_ROOT()
    if type(kci_root) is not bytes or len(kci_root) != 32 or type(keb_root) is not bytes or len(keb_root) != 32:
        _INTEGRITY_ERROR("kie1-prerequisite-root-integrity")
    label = _FRAME_FROZEN(b"omegaa.kie1-source.v1")
    payload = b"".join(
        _FRAME_FROZEN(field)
        for field in (_KPT1_SOURCE_ROOT, kci_root, keb_root, _SOURCE_MANIFEST())
    )
    result = _SHA256(label + payload).digest()
    _LOGGER.debug("kie1_source_root_v1 exit")
    return result


_SOURCE_ROOT_FROZEN = kie1_source_root_v1
_SOURCE_ROOT = _SOURCE_ROOT_FROZEN
_SOURCE_ROOT_CODE = _SOURCE_ROOT_FROZEN.__code__
