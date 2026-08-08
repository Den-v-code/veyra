"""Public check, verification, data, and cache APIs for R13.2."""
from __future__ import annotations

from contextvars import ContextVar
from functools import lru_cache
import logging
from typing import cast

from .intrinsic_observer_echo_effects import intrinsic_observer_echo_effect_digest
from .intrinsic_observer_echo_formal_bridge_core import (
    _CHECKED_DIAGNOSTICS, _blocked, _checked_report, _origins,
    check_intrinsic_observer_echo_formal_bridge,
)
from .intrinsic_observer_echo_formal_bridge_io import snapshot_key
from .intrinsic_observer_echo_formal_compile import compile_snapshot
from .intrinsic_observer_echo_formal_lean_render import THEOREM_IDS
from .intrinsic_observer_echo_formal_manifest import (
    BRIDGE_ID, EXPECTED_BINDING_DIGEST, EXPECTED_PHASE_ARTIFACT,
    EXPECTED_R11_BINDING, EXPECTED_R12_BINDING, EXPECTED_R13_TCB_DIGESTS,
    EXPECTED_SNAPSHOT_DIGEST, EXPECTED_SOURCE_ELABORATION_BINDING,
    EXPECTED_TOOLCHAIN_IDENTITY, MANIFEST_BOUNDARY,
)
from .intrinsic_observer_echo_formal_objects import EXPECTED_R13_OBJECTS
from .intrinsic_observer_echo_formal_report import (
    IntrinsicObserverEchoFormalBridgeReport,
    valid_intrinsic_observer_echo_formal_report_shape,
)
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope
from .shadow_effects import shadow_effect_registry_digest

logger = logging.getLogger(__name__)
_TRUSTED_CONTRACT_REPORT: ContextVar[
    IntrinsicObserverEchoFormalBridgeReport | None
] = ContextVar(
    "r13_trusted_contract_report",
    default=None,
)


def _matches_reviewed_envelope(report: IntrinsicObserverEchoFormalBridgeReport) -> bool:
    """Cheaply reject candidates outside the manually reviewed envelope."""
    logger.debug("r13_bridge._matches_reviewed_envelope entry")
    try:
        registry = shadow_effect_registry_digest()
        effect = intrinsic_observer_echo_effect_digest()
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError):
        logger.exception("R13 reviewed-envelope trust failure")
        return False
    result = (
        report.bridge_id == BRIDGE_ID
        and report.theorem_ids == THEOREM_IDS
        and report.phase_artifact_digest == EXPECTED_PHASE_ARTIFACT
        and report.source_elaboration_binding_digest == EXPECTED_SOURCE_ELABORATION_BINDING
        and report.r11_binding_digest == EXPECTED_R11_BINDING
        and report.r12_binding_digest == EXPECTED_R12_BINDING
        and report.source_digests == tuple(EXPECTED_R13_TCB_DIGESTS.items())
        and report.object_records == tuple(EXPECTED_R13_OBJECTS.items())
        and report.snapshot_digest == EXPECTED_SNAPSHOT_DIGEST
        and report.effect_registry_digest == registry
        and report.effect_digest == effect
        and report.capability is BridgeCapability.PRESERVES
        and report.evidence_class is EvidenceClass.FORMAL_BRIDGE
        and report.evidence_scope is EvidenceScope.GENERAL
        and report.binding_digest == EXPECTED_BINDING_DIGEST
        and report.phase_checked and report.r12_checked and report.manifest_checked
        and report.source_bound and report.object_bound and report.snapshot_checked
        and report.lean_checked
        and report.promotion_ready is False
        and report.taxonomy_changed is False
        and report.toolchain == EXPECTED_TOOLCHAIN_IDENTITY
        and report.diagnostics == _CHECKED_DIAGNOSTICS
        and report.boundary == MANIFEST_BOUNDARY
    )
    logger.debug("r13_bridge._matches_reviewed_envelope exit result=%s", result)
    return result


def verify_intrinsic_observer_echo_formal_bridge_report(report: object) -> bool:
    """Independently rehash, rebuild, compare, and fresh-compile exact evidence."""
    logger.debug("verify_r13_formal_report entry type=%s", type(report).__name__)
    if not valid_intrinsic_observer_echo_formal_report_shape(report):
        return False
    checked_report = cast(IntrinsicObserverEchoFormalBridgeReport, report)
    if (
        checked_report.status != "checked"
        or not _matches_reviewed_envelope(checked_report)
    ):
        return False
    try:
        local, r12, sources, digests, command, toolchain, snapshot = _origins()
        expected = _checked_report(
            local, r12, digests, snapshot.root.name, toolchain, _CHECKED_DIAGNOSTICS,
        )
        if checked_report != expected:
            return False
        checked, diagnostics = compile_snapshot(command, snapshot, sources)
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError):
        logger.exception("R13 report verification trust failure")
        return False
    result = checked and diagnostics == _CHECKED_DIAGNOSTICS
    logger.debug("verify_r13_formal_report exit result=%s", result)
    return result


def intrinsic_observer_echo_formal_bridge_data(report: object) -> dict[str, object]:
    """Serialize one exact report without converting it to promotion evidence."""
    logger.debug("r13_formal_bridge_data entry type=%s", type(report).__name__)
    if not valid_intrinsic_observer_echo_formal_report_shape(report):
        raise ValueError("r13.2-report-shape-invalid")
    checked_report = cast(IntrinsicObserverEchoFormalBridgeReport, report)
    result = {
        "status": checked_report.status, "bridge_id": checked_report.bridge_id,
        "theorem_ids": list(checked_report.theorem_ids),
        "phase_artifact_digest": checked_report.phase_artifact_digest,
        "source_elaboration_binding_digest": checked_report.source_elaboration_binding_digest,
        "r11_binding_digest": checked_report.r11_binding_digest,
        "r12_binding_digest": checked_report.r12_binding_digest,
        "executable_evidence_digest": checked_report.executable_evidence_digest,
        "effect_registry_digest": checked_report.effect_registry_digest,
        "effect_digest": checked_report.effect_digest,
        "source_digests": [
            {"name": name, "sha256": digest}
            for name, digest in checked_report.source_digests
        ],
        "object_records": [
            {"name": name, "filename": row[0], "size": row[1], "sha256": row[2]}
            for name, row in checked_report.object_records
        ],
        "snapshot_digest": checked_report.snapshot_digest,
        "capability": checked_report.capability.value,
        "evidence_class": checked_report.evidence_class.value,
        "evidence_scope": checked_report.evidence_scope.value,
        "binding_digest": checked_report.binding_digest,
        "checks": {
            "phase": checked_report.phase_checked,
            "r12": checked_report.r12_checked,
            "manifest": checked_report.manifest_checked,
            "sources": checked_report.source_bound,
            "objects": checked_report.object_bound,
            "snapshot": checked_report.snapshot_checked,
            "lean": checked_report.lean_checked,
        },
        "promotion_ready": checked_report.promotion_ready,
        "taxonomy_changed": checked_report.taxonomy_changed,
        "toolchain": checked_report.toolchain,
        "diagnostics": checked_report.diagnostics,
        "boundary": checked_report.boundary,
    }
    logger.debug("r13_formal_bridge_data exit status=%s", checked_report.status)
    return result


def _default_trust_key() -> str:
    """Rehash all live inputs into one cache key."""
    logger.debug("r13_bridge._default_trust_key entry")
    try:
        local, r12, _, digests, _, toolchain, _ = _origins()
        phase, evidence, registry, effect, _ = local
        values = (
            phase.artifact_digest, phase.r10_binding_digest, r12.r11_binding_digest,
            r12.binding_digest, evidence.digest, registry, effect,
        )
        result = snapshot_key(digests, *values, toolchain)
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
        result = "blocked:" + str(exc)
    logger.debug("r13_bridge._default_trust_key exit key=%s", result)
    return result


@lru_cache(maxsize=8)
def _cached_default_report(trust_key: str) -> IntrinsicObserverEchoFormalBridgeReport:
    """Cache one checked report under the exact live trust key."""
    logger.debug("r13_bridge._cached_default_report entry key=%s", trust_key)
    result = check_intrinsic_observer_echo_formal_bridge()
    logger.debug("r13_bridge._cached_default_report exit status=%s", result.status)
    return result


def intrinsic_observer_echo_formal_bridge_report() -> IntrinsicObserverEchoFormalBridgeReport:
    """Rehash live inputs and return only a self-verifying checked report."""
    logger.debug("r13_formal_bridge_report entry")
    result = _cached_default_report(_default_trust_key())
    if not valid_intrinsic_observer_echo_formal_report_shape(result):
        result = _blocked("cached-r13.2-bridge-shape-mismatch")
    elif result.status == "checked" and not verify_intrinsic_observer_echo_formal_bridge_report(result):
        result = _blocked("cached-r13.2-bridge-integrity-mismatch")
    logger.debug("r13_formal_bridge_report exit status=%s", result.status)
    return result


def intrinsic_observer_echo_contract_bridge_report(
) -> IntrinsicObserverEchoFormalBridgeReport:
    """Fresh-check once and register only that exact report for R8 resolution."""
    logger.debug("r13_contract_bridge_report entry")
    _TRUSTED_CONTRACT_REPORT.set(None)
    result = check_intrinsic_observer_echo_formal_bridge()
    if (
        not valid_intrinsic_observer_echo_formal_report_shape(result)
        or result.status != "checked"
        or not _matches_reviewed_envelope(result)
    ):
        result = _blocked("r13.4-contract-bridge-integrity-mismatch")
    else:
        _TRUSTED_CONTRACT_REPORT.set(result)
    logger.debug("r13_contract_bridge_report exit status=%s", result.status)
    return result


def is_trusted_intrinsic_observer_echo_contract_report(report: object) -> bool:
    """Accept only the exact live object returned by the contract provider."""
    logger.debug(
        "is_trusted_r13_contract_report entry type=%s",
        type(report).__name__,
    )
    trusted = _TRUSTED_CONTRACT_REPORT.get()
    _TRUSTED_CONTRACT_REPORT.set(None)
    if not valid_intrinsic_observer_echo_formal_report_shape(report):
        return False
    checked_report = cast(IntrinsicObserverEchoFormalBridgeReport, report)
    if (
        checked_report.status != "checked"
        or not _matches_reviewed_envelope(checked_report)
    ):
        return False
    result = checked_report is trusted
    logger.debug("is_trusted_r13_contract_report exit result=%s", result)
    return result
