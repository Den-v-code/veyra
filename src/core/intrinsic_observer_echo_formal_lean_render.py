"""Deterministic Lean export binding the exact R13 theorem envelope."""
from __future__ import annotations

import json
import logging
import re

from .intrinsic_observer_echo_effects import BRIDGE_ID
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope

logger = logging.getLogger(__name__)
THEOREM_ROWS = (
    ("THM-R13-001", "THM_R13_001_captured_unit_weave_accepted"),
    ("THM-R13-002", "THM_R13_002_unit_weave_semantics_and_image"),
    ("THM-R13-003", "THM_R13_003_ready_intrinsic_unit_weave_echo"),
    ("THM-R13-004", "THM_R13_004_tail_silence_two_sided_domain_blocked"),
    ("THM-R13-005", "THM_R13_005_crest_nonreflection"),
)
THEOREM_IDS = tuple(row[0] for row in THEOREM_ROWS)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _lean_strings(values: tuple[str, ...]) -> str:
    """Render one exact tuple as a Lean String list."""
    logger.debug("r13_lean_render._lean_strings entry count=%d", len(values))
    if type(values) is not tuple or any(type(item) is not str for item in values):
        raise ValueError("r13.2-invalid-lean-string-list")
    result = "[" + ", ".join(json.dumps(item) for item in values) + "]"
    logger.debug("r13_lean_render._lean_strings exit")
    return result


def render_intrinsic_observer_echo_formal_lean(
    phase_artifact_digest: str,
    source_elaboration_binding_digest: str,
    r11_binding_digest: str,
    r12_binding_digest: str,
    executable_evidence_digest: str,
    effect_registry_digest: str,
    effect_digest: str,
) -> str:
    """Render only the exact source/parent/effect-bound R13 export."""
    logger.debug("render_r13_formal_lean entry")
    values = (
        phase_artifact_digest, source_elaboration_binding_digest,
        r11_binding_digest, r12_binding_digest, executable_evidence_digest,
        effect_registry_digest, effect_digest,
    )
    if any(type(value) is not str or _DIGEST.fullmatch(value) is None for value in values):
        raise ValueError("r13.2-generated-export-binding-invalid")
    checks = "\n".join(f"#check {symbol}" for _, symbol in THEOREM_ROWS)
    result = f'''import VeyraIntrinsicObserverEcho

/- Generated from exact phase, R11/R12, executable, and formal-effect evidence. -/
namespace VeyraIntrinsicObserverEchoExport
open VeyraIntrinsicObserverEcho

def theoremIds : List String := {_lean_strings(THEOREM_IDS)}
def bridgeId : String := "{BRIDGE_ID}"
def phaseArtifactDigest : String := "{phase_artifact_digest}"
def sourceElaborationBindingDigest : String := "{source_elaboration_binding_digest}"
def r11BindingDigest : String := "{r11_binding_digest}"
def r12BindingDigest : String := "{r12_binding_digest}"
def executableEvidenceDigest : String := "{executable_evidence_digest}"
def effectRegistryDigest : String := "{effect_registry_digest}"
def effectDigest : String := "{effect_digest}"
def capability : String := "{BridgeCapability.PRESERVES.value}"
def evidenceClass : String := "{EvidenceClass.FORMAL_BRIDGE.value}"
def evidenceScope : String := "{EvidenceScope.GENERAL.value}"
def promotionReady : Bool := false
def taxonomyChanged : Bool := false

{checks}

end VeyraIntrinsicObserverEchoExport
'''
    logger.debug("render_r13_formal_lean exit bytes=%d", len(result.encode()))
    return result


def canonical_intrinsic_observer_echo_formal_lean(
    phase_artifact_digest: str,
    source_elaboration_binding_digest: str,
    r11_binding_digest: str,
    r12_binding_digest: str,
    executable_evidence_digest: str,
    effect_registry_digest: str,
    effect_digest: str,
) -> bytes:
    """Return canonical UTF-8 bytes for the generated snapshot stage."""
    logger.debug("canonical_r13_formal_lean entry")
    result = render_intrinsic_observer_echo_formal_lean(
        phase_artifact_digest, source_elaboration_binding_digest,
        r11_binding_digest, r12_binding_digest, executable_evidence_digest,
        effect_registry_digest, effect_digest,
    ).encode()
    logger.debug("canonical_r13_formal_lean exit bytes=%d", len(result))
    return result
