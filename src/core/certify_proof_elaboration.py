"""Certificate gate for the source-replayed R10 proof elaboration bridge."""
from __future__ import annotations

import logging

from .certify_types import Certificate
from .proof_elaboration_bridge import (
    THEOREM_IDS, proof_elaboration_bridge_report,
    verify_proof_elaboration_bridge_report,
)
from .proof_elaboration_canonical import CANONICAL_SOURCE, canonical_elaboration

logger = logging.getLogger(__name__)


def certify_proof_elaboration_r10() -> Certificate:
    """Gate exact source replay, structural support, snapshot, and Lean image soundness."""
    logger.debug("certify_proof_elaboration_r10 entry")
    artifact, _ = canonical_elaboration()
    bridge = proof_elaboration_bridge_report()
    support = dict(artifact.dependency_support)
    expected_support = {
        "formation": ("formation.proposition", "formation.recurrence"),
        "definition": (
            "definition.equal", "definition.forall", "definition.pulse",
            "definition.resonates", "definition.silence", "definition.weave",
        ),
        "logical": ("logical.forall-intro", "logical.resonance-intro"),
        "domain": ("domain.weave-unit-right",),
        "observer": ("observer.intrinsic-mode",),
        "obstruction": (),
    }
    passed = (
        bridge.status == "checked"
        and bridge.theorem_ids == THEOREM_IDS
        and bridge.elaboration_binding_digest == artifact.binding_digest
        and bridge.surface_syntax_digest == artifact.surface_syntax_digest
        and bridge.semantic_digest == artifact.semantic_digest
        and bridge.r7_artifact_digest == artifact.r7_artifact_digest
        and bridge.r9_binding_digest == artifact.r9_binding_digest
        and bridge.artifact_checked and bridge.manifest_checked
        and bridge.source_bound and bridge.snapshot_checked and bridge.lean_checked
        and verify_proof_elaboration_bridge_report(bridge)
        and len(bridge.source_digests) == 37
        and len(CANONICAL_SOURCE) == artifact.source_size
        and support == expected_support
        and "parser correctness remains reviewed source TCB" in bridge.boundary
    )
    detail = (
        f"theorems={len(bridge.theorem_ids)}/5 sources={len(bridge.source_digests)}/37 "
        f"artifact={artifact.binding_digest[:16]} binding={bridge.binding_digest[:16]}"
    )
    result = Certificate(
        "proof_elaboration_r10",
        "source-replayed surface proof bound to R7 checking and R9 image semantics",
        passed, detail, 2,
    )
    if not passed:
        logger.error("certify_proof_elaboration_r10 blocked detail=%s bridge=%r", detail, bridge)
    logger.debug("certify_proof_elaboration_r10 exit result=%r", result)
    return result
