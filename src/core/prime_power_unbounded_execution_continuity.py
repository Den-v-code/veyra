"""N6-local no-follow continuity checks for launcher and private proof files."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging
import os
from pathlib import Path
import stat

logger = logging.getLogger(__name__)
_MAX_RUNTIME_FILE = 256 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class RuntimeFileSnapshotV1:
    """One path, inode/stat signature, and content identity captured together."""

    path: Path
    signature: tuple[int, ...]
    content_sha256: str


def _open_absolute(path: Path) -> int | None:
    """Open an absolute regular file componentwise without following symlinks."""
    logger.debug("_open_absolute entry")
    if not isinstance(path, Path) or not path.is_absolute() or path.name in ("", ".", ".."):
        logger.error("_open_absolute invalid absolute path")
        return None
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    current: int | None = None
    try:
        current = os.open("/", flags | os.O_DIRECTORY)
        for component in path.parts[1:-1]:
            next_fd = os.open(component, flags | os.O_DIRECTORY, dir_fd=current)
            os.close(current)
            current = next_fd
        result = os.open(path.name, flags, dir_fd=current)
    except OSError:
        logger.error("_open_absolute component or leaf unavailable")
        if current is not None:
            os.close(current)
        return None
    os.close(current)
    logger.debug("_open_absolute exit")
    return result


def _signature(fd: int) -> tuple[int, ...] | None:
    """Capture the immutable comparison signature of one open regular file."""
    logger.debug("_signature entry")
    try:
        metadata = os.fstat(fd)
    except OSError:
        logger.error("_signature fstat failed")
        return None
    if not stat.S_ISREG(metadata.st_mode) or not 0 <= metadata.st_size <= _MAX_RUNTIME_FILE:
        logger.error("_signature nonregular or oversize file")
        return None
    result = (
        metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns,
    )
    logger.debug("_signature exit bytes=%d", metadata.st_size)
    return result


def _hash(fd: int, size: int) -> str | None:
    """Hash exact bytes through an already-open descriptor."""
    logger.debug("_hash entry bytes=%d", size)
    value, offset = hashlib.sha256(), 0
    try:
        while offset < size:
            chunk = os.pread(fd, min(1024 * 1024, size - offset), offset)
            if not chunk:
                logger.error("_hash premature eof")
                return None
            value.update(chunk)
            offset += len(chunk)
        if os.pread(fd, 1, size):
            logger.error("_hash trailing byte drift")
            return None
    except OSError:
        logger.error("_hash read failed")
        return None
    result = value.hexdigest()
    logger.debug("_hash exit bytes=%d", offset)
    return result


def snapshot_runtime_file(path: Path, expected_sha256: str) -> RuntimeFileSnapshotV1 | None:
    """Capture one no-follow regular file only when bytes remain stable and expected."""
    logger.debug("snapshot_runtime_file entry")
    if (
        type(expected_sha256) is not str
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_sha256)
    ):
        logger.error("snapshot_runtime_file expected digest invalid")
        return None
    fd = _open_absolute(path)
    if fd is None:
        return None
    try:
        before = _signature(fd)
        if before is None:
            return None
        content = _hash(fd, before[3])
        after = _signature(fd)
    finally:
        os.close(fd)
    if before != after or content != expected_sha256:
        logger.error("snapshot_runtime_file content or stat drift")
        return None
    result = RuntimeFileSnapshotV1(path, before, content)
    logger.debug("snapshot_runtime_file exit bytes=%d", before[3])
    return result


def runtime_file_unchanged(snapshot: RuntimeFileSnapshotV1) -> bool:
    """Reopen and compare path, inode/stat signature, and full content digest."""
    logger.debug("runtime_file_unchanged entry")
    if type(snapshot) is not RuntimeFileSnapshotV1:
        logger.error("runtime_file_unchanged exact snapshot required")
        return False
    current = snapshot_runtime_file(snapshot.path, snapshot.content_sha256)
    result = current is not None and current.signature == snapshot.signature
    logger.debug("runtime_file_unchanged exit result=%s", result)
    return result


def continuity_set_holds(snapshots: tuple[RuntimeFileSnapshotV1, ...]) -> bool:
    """Check every exact snapshot without accepting caller-defined containers."""
    logger.debug("continuity_set_holds entry")
    if type(snapshots) is not tuple or any(
        type(item) is not RuntimeFileSnapshotV1 for item in snapshots
    ):
        logger.error("continuity_set_holds exact tuple required")
        return False
    result = all(runtime_file_unchanged(item) for item in snapshots)
    logger.debug("continuity_set_holds exit files=%d result=%s", len(snapshots), result)
    return result
