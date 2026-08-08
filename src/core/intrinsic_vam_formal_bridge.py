"""Public check, verification, canonical data, and cache APIs for R12.5."""
from __future__ import annotations

from functools import lru_cache
import logging

from .intrinsic_vam_formal_bridge_core import (
    _CHECKED_DIAGNOSTICS,
    _blocked,
    _checked_report,
    _origins,
    check_intrinsic_vam_formal_bridge,
)
from .intrinsic_vam_formal_bridge_io import snapshot_key
from .intrinsic_vam_formal_compile import compile_snapshot
from .intrinsic_vam_formal_effects import intrinsic_vam_formal_effect_digest
from .intrinsic_vam_formal_lean_render import THEOREM_IDS
from .intrinsic_vam_formal_manifest import (
    BRIDGE_ID,
    EXPECTED_BINDING_DIGEST,
    EXPECTED_R11_BINDING,
    EXPECTED_SNAPSHOT_DIGEST,
    EXPECTED_TOOLCHAIN_IDENTITY,
    EXPECTED_R12_5_TCB_DIGESTS,
    MANIFEST_BOUNDARY,
)
from .intrinsic_vam_formal_objects import EXPECTED_R12_5_OBJECTS
from .intrinsic_vam_formal_report import (
    IntrinsicVamFormalBridgeReport,
    valid_intrinsic_vam_formal_report_shape,
)
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope
from .shadow_effects import shadow_effect_registry_digest

logger = logging.getLogger(__name__)


def _matches_reviewed_envelope(report: IntrinsicVamFormalBridgeReport) -> bool:
    """Cheaply reject any candidate outside the manually reviewed envelope."""
    logger.debug("intrinsic_vam_formal_bridge._matches_reviewed_envelope entry")
    try:
        registry = shadow_effect_registry_digest()
        effect = intrinsic_vam_formal_effect_digest()
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError):
        logger.exception("R12.5 reviewed-envelope trust failure")
        return False
    result = (
        report.bridge_id == BRIDGE_ID
        and report.theorem_ids == THEOREM_IDS
        and report.r11_binding_digest == EXPECTED_R11_BINDING
        and report.source_digests == tuple(EXPECTED_R12_5_TCB_DIGESTS.items())
        and report.object_records == tuple(EXPECTED_R12_5_OBJECTS.items())
        and report.snapshot_digest == EXPECTED_SNAPSHOT_DIGEST
        and report.effect_registry_digest == registry
        and report.effect_digest == effect
        and report.capability is BridgeCapability.PRESERVES
        and report.evidence_class is EvidenceClass.FORMAL_BRIDGE
        and report.evidence_scope is EvidenceScope.GENERAL
        and report.binding_digest == EXPECTED_BINDING_DIGEST
        and report.r11_checked
        and report.manifest_checked
        and report.source_bound
        and report.object_bound
        and report.snapshot_checked
        and report.lean_checked
        and report.promotion_ready is False
        and report.taxonomy_changed is False
        and report.toolchain == EXPECTED_TOOLCHAIN_IDENTITY
        and report.diagnostics == _CHECKED_DIAGNOSTICS
        and report.boundary == MANIFEST_BOUNDARY
    )
    logger.debug(
        "intrinsic_vam_formal_bridge._matches_reviewed_envelope exit result=%s",
        result,
    )
    return result


def verify_intrinsic_vam_formal_bridge_report(report: object) -> bool:
    """Independently rebuild, rehash, compare, and fresh-compile exact evidence."""
    logger.debug(
        "verify_intrinsic_vam_formal_bridge_report entry type=%s",
        type(report).__name__,
    )
    if (
        not valid_intrinsic_vam_formal_report_shape(report)
        or report.status != "checked"
        or not _matches_reviewed_envelope(report)
    ):
        return False
    try:
        r11, registry, effect, sources, digests, command, toolchain, snapshot = _origins(
            None, None,
        )
        expected = _checked_report(
            r11,
            digests,
            snapshot.root.name,
            registry,
            effect,
            toolchain,
            _CHECKED_DIAGNOSTICS,
        )
        if report != expected:
            return False
        checked, diagnostics = compile_snapshot(command, snapshot, sources)
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError):
        logger.exception("R12.5 report verification trust failure")
        return False
    result = checked and diagnostics == _CHECKED_DIAGNOSTICS
    logger.debug("verify_intrinsic_vam_formal_bridge_report exit result=%s", result)
    return result


def intrinsic_vam_formal_bridge_data(report: object) -> dict[str, object]:
    """Serialize one exact report without converting it into promotion evidence."""
    logger.debug("intrinsic_vam_formal_bridge_data entry type=%s", type(report).__name__)
    if not valid_intrinsic_vam_formal_report_shape(report):
        raise ValueError("r12.5-report-shape-invalid")
    result = {
        "status": report.status,
        "bridge_id": report.bridge_id,
        "theorem_ids": list(report.theorem_ids),
        "r11_binding_digest": report.r11_binding_digest,
        "source_digests": [
            {"name": name, "sha256": digest} for name, digest in report.source_digests
        ],
        "object_records": [
            {"name": name, "filename": row[0], "size": row[1], "sha256": row[2]}
            for name, row in report.object_records
        ],
        "snapshot_digest": report.snapshot_digest,
        "effect_registry_digest": report.effect_registry_digest,
        "effect_digest": report.effect_digest,
        "capability": report.capability.value,
        "evidence_class": report.evidence_class.value,
        "evidence_scope": report.evidence_scope.value,
        "binding_digest": report.binding_digest,
        "checks": {
            "r11": report.r11_checked,
            "manifest": report.manifest_checked,
            "sources": report.source_bound,
            "objects": report.object_bound,
            "snapshot": report.snapshot_checked,
            "lean": report.lean_checked,
        },
        "promotion_ready": report.promotion_ready,
        "taxonomy_changed": report.taxonomy_changed,
        "toolchain": report.toolchain,
        "diagnostics": report.diagnostics,
        "boundary": report.boundary,
    }
    logger.debug("intrinsic_vam_formal_bridge_data exit status=%s", report.status)
    return result


def _default_trust_key() -> str:
    logger.debug("intrinsic_vam_formal_bridge._default_trust_key entry")
    try:
        r11, registry, effect, _, digests, _, toolchain, _ = _origins(None, None)
        result = snapshot_key(
            digests, r11.binding_digest, registry, effect, toolchain,
        )
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
        result = "blocked:" + str(exc)
    logger.debug("intrinsic_vam_formal_bridge._default_trust_key exit key=%s", result)
    return result


@lru_cache(maxsize=8)
def _cached_default_report(trust_key: str) -> IntrinsicVamFormalBridgeReport:
    logger.debug("intrinsic_vam_formal_bridge._cached_default_report entry key=%s", trust_key)
    result = check_intrinsic_vam_formal_bridge()
    logger.debug("intrinsic_vam_formal_bridge._cached_default_report exit status=%s", result.status)
    return result


def intrinsic_vam_formal_bridge_report() -> IntrinsicVamFormalBridgeReport:
    """Rehash live inputs and cache compilation only under the exact trust key."""
    logger.debug("intrinsic_vam_formal_bridge_report entry")
    result = _cached_default_report(_default_trust_key())
    if not valid_intrinsic_vam_formal_report_shape(result):
        result = _blocked("cached-r12.5-bridge-shape-mismatch")
    elif result.status == "checked" and not verify_intrinsic_vam_formal_bridge_report(result):
        result = _blocked("cached-r12.5-bridge-integrity-mismatch")
    logger.debug("intrinsic_vam_formal_bridge_report exit status=%s", result.status)
    return result
