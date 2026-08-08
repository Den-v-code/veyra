"""Dirfd-bound hostile-safe source capture for the checked P3-N6 runner."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import stat

from .prime_power_unbounded_common import reject, sha

logger = logging.getLogger(__name__)
_MAX_SOURCE_BYTES = 3 * 1024 * 1024


def _open_project_root() -> tuple[int, Path]:
    """Open every absolute project-root component with no symlink following."""
    logger.debug("_open_project_root entry")
    module_path = Path(__file__)
    if not module_path.is_absolute():
        reject("n6-capture-module-path-not-absolute")
    root = module_path.parents[2]
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    current = os.open("/", flags)
    try:
        for component in root.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=current)
            os.close(current)
            current = next_fd
    except OSError:
        try:
            os.close(current)
        except OSError:
            logger.error("_open_project_root cleanup failed")
        reject("n6-capture-project-root-symlink-or-unavailable")
    check_fds: list[int] = []
    module_fd: int | None = None
    try:
        module_parent = current
        for component in ("src", "core"):
            opened = os.open(component, flags, dir_fd=module_parent)
            check_fds.append(opened)
            module_parent = opened
        module_fd = os.open(
            "prime_power_unbounded_capture.py",
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=module_parent,
        )
        if not stat.S_ISREG(os.fstat(module_fd).st_mode):
            raise OSError("module-not-regular")
    except OSError:
        os.close(current)
        reject("n6-capture-module-symlink-or-unavailable")
    finally:
        if module_fd is not None:
            os.close(module_fd)
        for check_fd in reversed(check_fds):
            os.close(check_fd)
    logger.debug("_open_project_root exit")
    return current, root


def project_root_path() -> Path:
    """Return the verified absolute project root and close its proof handle."""
    logger.debug("project_root_path entry")
    root_fd, root = _open_project_root()
    try:
        result = root
    finally:
        os.close(root_fd)
    logger.debug("project_root_path exit")
    return result


def project_tmp_path() -> Path:
    """Return only an existing componentwise no-follow project data/tmp path."""
    logger.debug("project_tmp_path entry")
    root_fd, root = _open_project_root()
    opened: list[int] = []
    try:
        current = root_fd
        for component in ("data", "tmp"):
            directory_fd = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=current,
            )
            opened.append(directory_fd)
            current = directory_fd
        result = root / "data" / "tmp"
    except OSError:
        reject("n6-capture-project-tmp-symlink-or-unavailable")
    finally:
        for directory_fd in reversed(opened):
            os.close(directory_fd)
        os.close(root_fd)
    logger.debug("project_tmp_path exit")
    return result


def _signature(fd: int) -> tuple[int, ...]:
    """Capture the exact regular-file continuity signature."""
    logger.debug("_signature entry")
    try:
        metadata = os.fstat(fd)
    except OSError:
        reject("n6-capture-fstat-failed")
    result = (
        metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns,
    )
    logger.debug("_signature exit size=%d", metadata.st_size)
    return result


def _payload(fd: int, size: int) -> bytes:
    """Read exactly the signed file size through the already-open handle."""
    logger.debug("_payload entry size=%d", size)
    chunks: list[bytes] = []
    offset = 0
    try:
        while offset < size:
            chunk = os.pread(fd, min(131072, size - offset), offset)
            if not chunk:
                reject("n6-capture-byte-continuity-drift")
            chunks.append(chunk)
            offset += len(chunk)
        if os.pread(fd, 1, size):
            reject("n6-capture-byte-continuity-drift")
    except OSError:
        reject("n6-capture-read-failed")
    result = b"".join(chunks)
    logger.debug("_payload exit bytes=%d", len(result))
    return result


def capture_fixed_source(path_text: str, expected_sha: str) -> bytes:
    """Capture one fixed relative source with componentwise O_NOFOLLOW."""
    logger.debug("capture_fixed_source entry")
    if type(path_text) is not str or type(expected_sha) is not str:
        reject("n6-capture-spec-type-invalid")
    parts = path_text.split("/")
    if path_text.startswith("/") or not parts or any(x in ("", ".", "..") for x in parts):
        reject("n6-capture-path-invalid")
    root_fd, _ = _open_project_root()
    opened: list[int] = []
    final_fd: int | None = None
    try:
        current = root_fd
        for component in parts[:-1]:
            directory_fd = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=current,
            )
            opened.append(directory_fd)
            current = directory_fd
        final_fd = os.open(
            parts[-1], os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=current,
        )
        before = _signature(final_fd)
        if not stat.S_ISREG(before[2]) or not 0 <= before[3] <= _MAX_SOURCE_BYTES:
            reject("n6-capture-source-type-or-size-invalid")
        result = _payload(final_fd, before[3])
        if _signature(final_fd) != before or sha(result) != expected_sha:
            reject("n6-capture-source-continuity-or-digest-drift")
    except OSError:
        reject("n6-capture-source-unavailable-or-symlinked")
    finally:
        if final_fd is not None:
            os.close(final_fd)
        for directory_fd in reversed(opened):
            os.close(directory_fd)
        os.close(root_fd)
    logger.debug("capture_fixed_source exit bytes=%d", len(result))
    return result
