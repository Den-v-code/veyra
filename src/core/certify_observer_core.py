"""Standalone certificate gate for the fail-closed R11 observer Lean bridge."""
from __future__ import annotations

import logging

from .certify_types import Certificate
from .observer_core_bridge import (
    BRIDGE_ID,
    THEOREM_IDS,
    observer_core_bridge_report,
    verify_observer_core_bridge_report,
)
from .observer_core_bridge_report import valid_observer_core_bridge_report_shape
from .observer_core_lean_render import canonical_observer_artifact
from .observer_core_manifest import EXPECTED_R11_TCB_DIGESTS

logger = logging.getLogger(__name__)


def certify_observer_core_r11() -> Certificate:
    """Gate exact artifact replay, R10 continuity, manifest, snapshot, and Lean."""
    logger.debug("certify_observer_core_r11 entry")
    artifact = canonical_observer_artifact()
    bridge = observer_core_bridge_report()
    report_shape = valid_observer_core_bridge_report_shape(bridge)
    expected_support = (
        "observer-core-semantics", "observer-core-codec", "crest-pulse-law",
    )
    passed = (
        report_shape
        and bridge.status == "checked"
        and bridge.bridge_id == BRIDGE_ID
        and bridge.theorem_ids == THEOREM_IDS
        and bridge.artifact_digest == artifact.proof_digest
        and artifact.support == expected_support
        and bridge.source_digests == tuple(EXPECTED_R11_TCB_DIGESTS.items())
        and bridge.artifact_checked and bridge.r10_checked
        and bridge.manifest_checked and bridge.source_bound
        and bridge.snapshot_checked and bridge.lean_checked
        and verify_observer_core_bridge_report(bridge)
        and "does not renew or widen the R8 promotion contract" in bridge.boundary
    )
    detail = (
        f"theorems={len(bridge.theorem_ids)}/6 sources={len(bridge.source_digests)}/34 "
        f"artifact={artifact.proof_digest[:16]} r10={bridge.r10_binding_digest[:16]} "
        f"binding={bridge.binding_digest[:16]}"
        if report_shape else "invalid R11 bridge report shape"
    )
    result = Certificate(
        "observer_core_r11",
        "closed observer artifact bound to unchanged R7, exact R9 image, and verified R10",
        passed, detail, 2,
    )
    if not passed:
        logger.error("certify_observer_core_r11 blocked detail=%s bridge=%r", detail, bridge)
    logger.debug("certify_observer_core_r11 exit result=%r", result)
    return result
