"""Exact immutable report shapes for the R11 bridge and R10 continuity."""
from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import stat
from typing import Mapping

from .observer_core_manifest import _EXPECTED_R11_TCB_DIGEST_ROWS, EXPECTED_R11_TCB_DIGESTS
from .observer_core_objects import _EXPECTED_LEAN_OBJECT_ROWS, EXPECTED_LEAN_OBJECTS
from .proof_elaboration_bridge import ProofElaborationBridgeReport

logger = logging.getLogger(__name__)
_DIGEST = re.compile(r"[0-9a-f]{64}")
MAX_REVIEWED_SOURCE_BYTES = 1_048_576


@dataclass(frozen=True)
class ObserverCoreBridgeReport:
    """Exact R11 artifact, R10 continuity, source, snapshot, and Lean evidence."""

    status: str
    bridge_id: str
    theorem_ids: tuple[str, ...]
    observer_ast_digest: str
    observer_result_digest: str
    artifact_digest: str
    r10_binding_digest: str
    source_digests: tuple[tuple[str, str], ...]
    snapshot_digest: str
    binding_digest: str
    artifact_checked: bool
    r10_checked: bool
    manifest_checked: bool
    source_bound: bool
    snapshot_checked: bool
    lean_checked: bool
    toolchain: str
    diagnostics: str
    boundary: str


def _source_identity(metadata: os.stat_result) -> tuple[int, ...]:
    logger.debug("observer_core_bridge_report._source_identity entry")
    result = (
        metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_nlink,
        metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns,
    )
    logger.debug("observer_core_bridge_report._source_identity exit")
    return result


def _entry_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    logger.debug("observer_core_bridge_report._entry_identity entry")
    result = metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)
    logger.debug("observer_core_bridge_report._entry_identity exit")
    return result


def read_exact_regular_source(path: Path) -> bytes:
    """Read one bounded regular source through a pinned no-symlink path chain."""
    logger.debug("read_exact_regular_source entry type=%s", type(path).__name__)
    if type(path) is not type(Path()) or not path.is_absolute():
        logger.error("read_exact_regular_source invalid path")
        raise ValueError("r11-source-path-invalid")
    parts = path.parts
    if len(parts) < 2 or parts[0] != os.sep or any(part in {"", ".", ".."} for part in parts[1:]):
        logger.error("read_exact_regular_source invalid components=%r", parts)
        raise ValueError("r11-source-path-invalid")
    descriptors: list[int] = []
    ancestors: list[tuple[int, str, int, tuple[int, int, int]]] = []
    try:
        directory_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptors.append(os.open(os.sep, directory_flags))
        for component in parts[1:-1]:
            parent = descriptors[-1]
            initial_directory = os.stat(component, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISDIR(initial_directory.st_mode):
                raise ValueError("r11-source-ancestor-shape-invalid")
            opened_directory = os.open(component, directory_flags, dir_fd=parent)
            descriptors.append(opened_directory)
            identity = _entry_identity(os.fstat(opened_directory))
            if identity != _entry_identity(initial_directory):
                raise ValueError("r11-source-ancestor-raced")
            ancestors.append((parent, component, opened_directory, identity))
        parent, filename = descriptors[-1], parts[-1]
        initial = os.stat(filename, dir_fd=parent, follow_symlinks=False)
        if (
            not stat.S_ISREG(initial.st_mode) or initial.st_nlink != 1
            or initial.st_size < 0 or initial.st_size > MAX_REVIEWED_SOURCE_BYTES
        ):
            raise ValueError("r11-source-file-shape-invalid")
        descriptor = os.open(
            filename, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent,
        )
        descriptors.append(descriptor)
        opened = os.fstat(descriptor)
        if _source_identity(initial) != _source_identity(opened):
            raise ValueError("r11-source-file-raced")
        chunks, remaining = [], opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            if not chunk:
                raise ValueError("r11-source-file-raced")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise ValueError("r11-source-file-raced")
        finished = os.fstat(descriptor)
        current = os.stat(filename, dir_fd=parent, follow_symlinks=False)
        identity = _source_identity(opened)
        if identity != _source_identity(finished) or identity != _source_identity(current):
            raise ValueError("r11-source-file-raced")
        for ancestor_parent, component, ancestor_fd, ancestor_identity in ancestors:
            current_ancestor = os.stat(component, dir_fd=ancestor_parent, follow_symlinks=False)
            if (
                ancestor_identity != _entry_identity(os.fstat(ancestor_fd))
                or ancestor_identity != _entry_identity(current_ancestor)
            ):
                raise ValueError("r11-source-ancestor-raced")
        result = b"".join(chunks)
    except OSError as exc:
        logger.error("read_exact_regular_source filesystem rejection=%s", exc)
        raise ValueError("r11-source-file-unreadable") from exc
    except ValueError as exc:
        logger.error("read_exact_regular_source rejected reason=%s", exc)
        raise
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError as exc:
                logger.error("read_exact_regular_source close failed=%s", exc)
    logger.debug("read_exact_regular_source exit bytes=%d", len(result))
    return result


def _exact_text_tuple(values: object) -> bool:
    logger.debug("observer_core_bridge_report._exact_text_tuple entry type=%s", type(values).__name__)
    result = type(values) is tuple and all(type(item) is str for item in values)
    logger.debug("observer_core_bridge_report._exact_text_tuple exit result=%s", result)
    return result


def _exact_digest_rows(values: object) -> bool:
    logger.debug("observer_core_bridge_report._exact_digest_rows entry type=%s", type(values).__name__)
    result = (
        type(values) is tuple
        and all(
            type(row) is tuple and len(row) == 2
            and all(type(item) is str for item in row)
            for row in values
        )
    )
    logger.debug("observer_core_bridge_report._exact_digest_rows exit result=%s", result)
    return result


def valid_observer_core_bridge_report_shape(report: object) -> bool:
    """Reject field subclasses before any equality or cache comparison."""
    logger.debug("valid_observer_core_bridge_report_shape entry type=%s", type(report).__name__)
    if type(report) is not ObserverCoreBridgeReport:
        logger.debug("valid_observer_core_bridge_report_shape exit result=False")
        return False
    texts = (
        report.status, report.bridge_id, report.observer_ast_digest,
        report.observer_result_digest, report.artifact_digest,
        report.r10_binding_digest, report.snapshot_digest, report.binding_digest,
        report.toolchain, report.diagnostics, report.boundary,
    )
    flags = (
        report.artifact_checked, report.r10_checked, report.manifest_checked,
        report.source_bound, report.snapshot_checked, report.lean_checked,
    )
    result = (
        all(type(item) is str for item in texts)
        and _exact_text_tuple(report.theorem_ids)
        and _exact_digest_rows(report.source_digests)
        and all(type(item) is bool for item in flags)
    )
    logger.debug("valid_observer_core_bridge_report_shape exit result=%s", result)
    return result


def valid_r10_continuity_report_shape(report: object) -> bool:
    """Type-harden the inherited R10 report before continuity comparison."""
    logger.debug("valid_r10_continuity_report_shape entry type=%s", type(report).__name__)
    if type(report) is not ProofElaborationBridgeReport:
        logger.debug("valid_r10_continuity_report_shape exit result=False")
        return False
    texts = (
        report.status, report.elaboration_binding_digest,
        report.surface_syntax_digest, report.semantic_digest,
        report.r7_artifact_digest, report.r9_binding_digest,
        report.snapshot_digest, report.binding_digest, report.toolchain,
        report.diagnostics, report.boundary,
    )
    flags = (
        report.artifact_checked, report.manifest_checked, report.source_bound,
        report.snapshot_checked, report.lean_checked,
    )
    result = (
        all(type(item) is str for item in texts)
        and _exact_text_tuple(report.theorem_ids)
        and _exact_digest_rows(report.source_digests)
        and all(type(item) is bool for item in flags)
    )
    logger.debug("valid_r10_continuity_report_shape exit result=%s", result)
    return result


def valid_source_origins(
    actual: object, expected: Mapping[str, Path],
) -> bool:
    """Accept only an exact dict snapshot; trusted proxies are handled by identity."""
    logger.debug("valid_source_origins entry type=%s", type(actual).__name__)
    path_type = type(Path())
    if type(actual) is not dict:
        logger.debug("valid_source_origins exit result=False")
        return False
    try:
        actual_rows = tuple(dict.items(actual))
    except RuntimeError:
        logger.error("valid_source_origins rejected unstable dict snapshot")
        return False
    expected_rows = tuple(expected.items())
    result = (
        len(actual_rows) == len(expected_rows)
        and all(
            type(name) is str and type(path) is path_type
            and type(expected_name) is str and type(expected_path) is path_type
            and name == expected_name and path == expected_path
            for (name, path), (expected_name, expected_path)
            in zip(actual_rows, expected_rows, strict=True)
        )
    )
    logger.debug("valid_source_origins exit result=%s", result)
    return result


def _trusted_proxy_rows(
    manifest: object, trusted: Mapping[object, object],
) -> tuple[tuple[object, object], ...] | None:
    logger.debug("observer_core_bridge_report._trusted_proxy_rows entry type=%s", type(manifest).__name__)
    if manifest is not trusted:
        logger.debug("observer_core_bridge_report._trusted_proxy_rows exit rejected identity")
        return None
    try:
        result = tuple(trusted.items())
    except RuntimeError:
        logger.error("observer_core_bridge_report rejected concurrent proxy mutation")
        return None
    logger.debug("observer_core_bridge_report._trusted_proxy_rows exit rows=%d", len(result))
    return result


def valid_digest_manifest(manifest: object, names: tuple[str, ...]) -> bool:
    """Accept only the trusted proxy when it still equals immutable reviewed rows."""
    logger.debug("valid_digest_manifest entry type=%s", type(manifest).__name__)
    rows = _trusted_proxy_rows(manifest, EXPECTED_R11_TCB_DIGESTS)
    result = (
        rows is not None and type(names) is tuple and all(type(name) is str for name in names)
        and all(type(row) is tuple and len(row) == 2 and type(row[0]) is str
                and type(row[1]) is str and _DIGEST.fullmatch(row[1]) is not None for row in rows)
        and tuple(row[0] for row in _EXPECTED_R11_TCB_DIGEST_ROWS) == names
        and rows == _EXPECTED_R11_TCB_DIGEST_ROWS
    )
    logger.debug("valid_digest_manifest exit result=%s", result)
    return result


def valid_object_manifest(manifest: object, names: tuple[str, ...]) -> bool:
    """Accept only the trusted object proxy when immutable rows still match."""
    logger.debug("valid_object_manifest entry type=%s", type(manifest).__name__)
    rows = _trusted_proxy_rows(manifest, EXPECTED_LEAN_OBJECTS)
    result = (
        rows is not None and type(names) is tuple and all(type(name) is str for name in names)
        and all(
            type(row) is tuple and len(row) == 2 and type(row[0]) is str
            and type(row[1]) is tuple and len(row[1]) == 3
            and type(row[1][0]) is str and Path(row[1][0]).name == row[1][0]
            and row[1][0].endswith(".olean") and type(row[1][1]) is int and row[1][1] > 0
            and type(row[1][2]) is str and _DIGEST.fullmatch(row[1][2]) is not None for row in rows
        )
        and len({row[0] for row in rows}) == len(rows)
        and len({row[1][0] for row in rows}) == len(rows)
        and tuple(row[0] for row in _EXPECTED_LEAN_OBJECT_ROWS) == names
        and rows == _EXPECTED_LEAN_OBJECT_ROWS
    )
    logger.debug("valid_object_manifest exit result=%s", result)
    return result
