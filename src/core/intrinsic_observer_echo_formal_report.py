"""Exact report types and local trust-root validators for R13.2."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import re
from typing import Mapping, TypeGuard

from .intrinsic_observer_echo_formal_manifest import (
    _EXPECTED_R13_TCB_DIGEST_ROWS,
    EXPECTED_R13_TCB_DIGESTS,
)
from .intrinsic_observer_echo_formal_objects import (
    _EXPECTED_R13_OBJECT_ROWS,
    EXPECTED_R13_OBJECTS,
)
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope

logger = logging.getLogger(__name__)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class IntrinsicObserverEchoFormalBridgeReport:
    """Complete phase/R11/R12/source/object/toolchain-bound R13 evidence."""

    status: str
    bridge_id: str
    theorem_ids: tuple[str, ...]
    phase_artifact_digest: str
    source_elaboration_binding_digest: str
    r11_binding_digest: str
    r12_binding_digest: str
    executable_evidence_digest: str
    effect_registry_digest: str
    effect_digest: str
    source_digests: tuple[tuple[str, str], ...]
    object_records: tuple[tuple[str, tuple[str, int, str]], ...]
    snapshot_digest: str
    capability: BridgeCapability
    evidence_class: EvidenceClass
    evidence_scope: EvidenceScope
    binding_digest: str
    phase_checked: bool
    r12_checked: bool
    manifest_checked: bool
    source_bound: bool
    object_bound: bool
    snapshot_checked: bool
    lean_checked: bool
    promotion_ready: bool
    taxonomy_changed: bool
    toolchain: str
    diagnostics: str
    boundary: str


def _exact_text_tuple(value: object) -> bool:
    """Recognize only plain ordered text tuples."""
    logger.debug("r13_report._exact_text_tuple entry")
    result = type(value) is tuple and all(type(item) is str for item in value)
    logger.debug("r13_report._exact_text_tuple exit result=%s", result)
    return result


def _exact_digest_rows(value: object) -> bool:
    """Recognize exact ordered name/SHA-256 rows."""
    logger.debug("r13_report._exact_digest_rows entry")
    result = (
        type(value) is tuple
        and all(
            type(row) is tuple
            and len(row) == 2
            and type(row[0]) is str
            and type(row[1]) is str
            and _DIGEST.fullmatch(row[1]) is not None
            for row in value
        )
    )
    logger.debug("r13_report._exact_digest_rows exit result=%s", result)
    return result


def _exact_object_rows(value: object) -> bool:
    """Recognize exact reviewed flat object records."""
    logger.debug("r13_report._exact_object_rows entry")
    result = (
        type(value) is tuple
        and all(
            type(row) is tuple
            and len(row) == 2
            and type(row[0]) is str
            and type(row[1]) is tuple
            and len(row[1]) == 3
            and type(row[1][0]) is str
            and Path(row[1][0]).name == row[1][0]
            and row[1][0].endswith(".olean")
            and type(row[1][1]) is int
            and row[1][1] > 0
            and type(row[1][2]) is str
            and _DIGEST.fullmatch(row[1][2]) is not None
            for row in value
        )
    )
    logger.debug("r13_report._exact_object_rows exit result=%s", result)
    return result


def valid_intrinsic_observer_echo_formal_report_shape(
    report: object,
) -> TypeGuard[IntrinsicObserverEchoFormalBridgeReport]:
    """Reject subclasses and hostile field values before hashing/equality."""
    logger.debug("valid_r13_formal_report_shape entry type=%s", type(report).__name__)
    if type(report) is not IntrinsicObserverEchoFormalBridgeReport:
        return False
    try:
        texts = (
            report.status, report.bridge_id, report.phase_artifact_digest,
            report.source_elaboration_binding_digest, report.r11_binding_digest,
            report.r12_binding_digest, report.executable_evidence_digest,
            report.effect_registry_digest, report.effect_digest, report.snapshot_digest,
            report.binding_digest, report.toolchain, report.diagnostics, report.boundary,
        )
        flags = (
            report.phase_checked, report.r12_checked, report.manifest_checked,
            report.source_bound, report.object_bound, report.snapshot_checked,
            report.lean_checked, report.promotion_ready, report.taxonomy_changed,
        )
        result = (
            all(type(item) is str for item in texts)
            and _exact_text_tuple(report.theorem_ids)
            and _exact_digest_rows(report.source_digests)
            and _exact_object_rows(report.object_records)
            and type(report.capability) is BridgeCapability
            and type(report.evidence_class) is EvidenceClass
            and type(report.evidence_scope) is EvidenceScope
            and all(type(item) is bool for item in flags)
        )
    except AttributeError:
        result = False
    logger.debug("valid_r13_formal_report_shape exit result=%s", result)
    return result


def valid_source_origins(actual: object, expected: Mapping[str, Path]) -> bool:
    """Accept only one exact ordered plain-dict copy of canonical origins."""
    logger.debug("r13_report.valid_source_origins entry")
    if type(actual) is not dict:
        return False
    try:
        rows, expected_rows = tuple(dict.items(actual)), tuple(expected.items())
    except RuntimeError:
        return False
    path_type = type(Path())
    result = len(rows) == len(expected_rows) and all(
        type(name) is str
        and type(path) is path_type
        and (name, path) == expected_row
        for (name, path), expected_row in zip(rows, expected_rows, strict=True)
    )
    logger.debug("r13_report.valid_source_origins exit result=%s", result)
    return result


def valid_digest_manifest(manifest: object, names: tuple[str, ...]) -> bool:
    """Validate identity and order of the manual source digest root."""
    logger.debug("r13_report.valid_digest_manifest entry")
    try:
        rows = tuple(EXPECTED_R13_TCB_DIGESTS.items())
    except RuntimeError:
        return False
    result = (
        manifest is EXPECTED_R13_TCB_DIGESTS
        and rows == _EXPECTED_R13_TCB_DIGEST_ROWS
        and tuple(name for name, _ in rows) == names
        and _exact_digest_rows(rows)
    )
    logger.debug("r13_report.valid_digest_manifest exit result=%s", result)
    return result


def valid_object_manifest(manifest: object, names: tuple[str, ...]) -> bool:
    """Validate identity and order of reviewed fresh Lean objects."""
    logger.debug("r13_report.valid_object_manifest entry")
    try:
        rows = tuple(EXPECTED_R13_OBJECTS.items())
    except RuntimeError:
        return False
    result = (
        manifest is EXPECTED_R13_OBJECTS
        and rows == _EXPECTED_R13_OBJECT_ROWS
        and tuple(name for name, _ in rows) == names
        and _exact_object_rows(rows)
        and len({row[1][0] for row in rows}) == len(rows)
    )
    logger.debug("r13_report.valid_object_manifest exit result=%s", result)
    return result
