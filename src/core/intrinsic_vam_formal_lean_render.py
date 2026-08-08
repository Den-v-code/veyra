"""Deterministic Lean export binding the exact R12.5 effect and R11 continuity."""
from __future__ import annotations

import json
import logging
import re

from .intrinsic_vam_formal_effects import (
    EVIDENCE_ID,
    intrinsic_vam_formal_effect_digest,
)
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope
from .shadow_effects import shadow_effect_registry_digest

logger = logging.getLogger(__name__)
THEOREM_ROWS = (
    ("THM-R12-001", "THM_R12_001_lower_recurrence_preserves_image"),
    ("THM-R12-002", "THM_R12_002_decode_lower_recurrence"),
    ("THM-R12-003", "THM_R12_003_lower_recurrence_injective"),
    ("THM-R12-004", "THM_R12_004_prefix_obstruction_transport"),
    ("THM-R12-005", "THM_R12_005_runPrimitive_transport"),
    ("THM-R12-006", "THM_R12_006_runObserver_transport"),
    ("THM-R12-007", "THM_R12_007_observe_transport"),
    ("THM-R12-008", "THM_R12_008_echo_transport"),
    ("THM-R12-009", "THM_R12_009_tail_silence_obstruction_transport"),
)
THEOREM_IDS = tuple(row[0] for row in THEOREM_ROWS)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _lean_strings(values: tuple[str, ...]) -> str:
    logger.debug("intrinsic_vam_formal_lean_render._lean_strings entry count=%d", len(values))
    if type(values) is not tuple or any(type(item) is not str for item in values):
        raise ValueError("r12.5-invalid-lean-string-list")
    result = "[" + ", ".join(json.dumps(item) for item in values) + "]"
    logger.debug("intrinsic_vam_formal_lean_render._lean_strings exit")
    return result


def render_intrinsic_vam_formal_lean(
    r11_binding_digest: str,
    effect_registry_digest: str,
    effect_digest: str,
) -> str:
    """Render only the exact canonical continuity/effect-bound export."""
    logger.debug("render_intrinsic_vam_formal_lean entry")
    expected_registry = shadow_effect_registry_digest()
    expected_effect = intrinsic_vam_formal_effect_digest()
    if (
        type(r11_binding_digest) is not str
        or _DIGEST.fullmatch(r11_binding_digest) is None
        or type(effect_registry_digest) is not str
        or effect_registry_digest != expected_registry
        or type(effect_digest) is not str
        or effect_digest != expected_effect
    ):
        logger.error("render_intrinsic_vam_formal_lean rejected binding input")
        raise ValueError("r12.5-generated-export-binding-invalid")
    checks = "\n".join(f"#check {symbol}" for _, symbol in THEOREM_ROWS)
    result = f'''import VeyraIntrinsicVamBridge

/- Generated from the exact R12.5 formal effect and a verified R11 report. -/
namespace VeyraIntrinsicVamExport
open VeyraIntrinsicVam

def theoremIds : List String := {_lean_strings(THEOREM_IDS)}
def r11BindingDigest : String := "{r11_binding_digest}"
def effectRegistryDigest : String := "{effect_registry_digest}"
def effectDigest : String := "{effect_digest}"
def capability : String := "{BridgeCapability.PRESERVES.value}"
def evidenceClass : String := "{EvidenceClass.FORMAL_BRIDGE.value}"
def evidenceScope : String := "{EvidenceScope.GENERAL.value}"
def evidenceId : String := "{EVIDENCE_ID}"
def promotionReady : Bool := false
def taxonomyChanged : Bool := false

{checks}

end VeyraIntrinsicVamExport
'''
    logger.debug("render_intrinsic_vam_formal_lean exit bytes=%d", len(result.encode()))
    return result


def canonical_intrinsic_vam_formal_lean(
    r11_binding_digest: str,
    effect_registry_digest: str,
    effect_digest: str,
) -> bytes:
    """Return canonical UTF-8 bytes for one immutable snapshot stage."""
    logger.debug("canonical_intrinsic_vam_formal_lean entry")
    result = render_intrinsic_vam_formal_lean(
        r11_binding_digest,
        effect_registry_digest,
        effect_digest,
    ).encode()
    logger.debug("canonical_intrinsic_vam_formal_lean exit bytes=%d", len(result))
    return result
