"""Isolated R13 theorem/effect declaration; the R12.1 registry is immutable."""
from __future__ import annotations

from hashlib import sha256
import logging
from types import MappingProxyType

from .intrinsic_observer_echo_evidence import (
    EVIDENCE_ID as EXECUTABLE_EVIDENCE_ID,
    intrinsic_observer_echo_evidence,
)
from .proof_core_codec import canonical_json
from .shadow_effect_types import (
    BridgeCapability,
    CarrierId,
    EvidenceClass,
    EvidenceScope,
)
from .shadow_effects import shadow_effect_registry_digest

logger = logging.getLogger(__name__)
EFFECT_SCHEMA = "veyra.intrinsic-observer-echo.formal-effect.r13.2.v1"
BRIDGE_ID = "veyra.lean.r13.intrinsic-observer-echo-tcb.v1"
KERNEL_EVIDENCE_ID = "THM-R13-003"
EXPECTED_REGISTRY_DIGEST = "6a62bf002948aa8f8acf30c8c3d01cfc5f1a3a87e97dbcdd6bb66e378210be41"
EFFECT_BOUNDARY = (
    "general preservation is conditional on R11 readiness and restricted to the exact "
    "R12 lowering image; tail/silence blockage and crest nonreflection are retained, "
    "with no reflects, equivalence, raw-IR, VAMI, receipt, legacy-VAM, or promotion claim"
)
_EFFECT_ROW = MappingProxyType(
    {
        "schema": EFFECT_SCHEMA,
        "sources": (
            CarrierId.R7_RECURRENCE,
            CarrierId.R9_INTRINSIC_MODE,
            CarrierId.R11_RESPONSE,
        ),
        "target": CarrierId.VAM_INTRINSIC_IR,
        "capabilities": (BridgeCapability.PRESERVES,),
        "kernel": (EvidenceClass.KERNEL_PROOF, EvidenceScope.GENERAL, KERNEL_EVIDENCE_ID),
        "formal": (EvidenceClass.FORMAL_BRIDGE, EvidenceScope.GENERAL, BRIDGE_ID),
        "executable_id": EXECUTABLE_EVIDENCE_ID,
        "boundary": EFFECT_BOUNDARY,
        "promotion_ready": False,
        "taxonomy_changed": False,
    }
)


def intrinsic_observer_echo_effect_data() -> dict[str, object]:
    """Return the exact standalone R13 declaration in canonical scalar form."""
    logger.debug("intrinsic_observer_echo_effect_data entry")
    row = _EFFECT_ROW
    expected = (
        EFFECT_SCHEMA,
        (CarrierId.R7_RECURRENCE, CarrierId.R9_INTRINSIC_MODE, CarrierId.R11_RESPONSE),
        CarrierId.VAM_INTRINSIC_IR,
        (BridgeCapability.PRESERVES,),
        (EvidenceClass.KERNEL_PROOF, EvidenceScope.GENERAL, KERNEL_EVIDENCE_ID),
        (EvidenceClass.FORMAL_BRIDGE, EvidenceScope.GENERAL, BRIDGE_ID),
        EXECUTABLE_EVIDENCE_ID,
        EFFECT_BOUNDARY,
        False,
        False,
    )
    actual = tuple(row[key] for key in (
        "schema", "sources", "target", "capabilities", "kernel", "formal",
        "executable_id", "boundary", "promotion_ready", "taxonomy_changed",
    ))
    if actual != expected or shadow_effect_registry_digest() != EXPECTED_REGISTRY_DIGEST:
        raise ValueError("r13-effect-row-or-r12.1-registry-invalid")
    evidence = intrinsic_observer_echo_evidence()
    result = {
        "schema": EFFECT_SCHEMA,
        "sources": [item.value for item in expected[1]],
        "target": CarrierId.VAM_INTRINSIC_IR.value,
        "capabilities": [BridgeCapability.PRESERVES.value],
        "evidence": [
            {"class": EvidenceClass.KERNEL_PROOF.value, "scope": EvidenceScope.GENERAL.value, "id": KERNEL_EVIDENCE_ID},
            {"class": EvidenceClass.FORMAL_BRIDGE.value, "scope": EvidenceScope.GENERAL.value, "id": BRIDGE_ID},
        ],
        "executable_evidence": {"id": evidence.evidence_id, "digest": evidence.digest, "scope": EvidenceScope.FINITE.value},
        "r12_1_registry_digest": EXPECTED_REGISTRY_DIGEST,
        "boundary": EFFECT_BOUNDARY,
        "promotion_ready": False,
        "taxonomy_changed": False,
    }
    logger.debug("intrinsic_observer_echo_effect_data exit")
    return result


def intrinsic_observer_echo_effect_digest() -> str:
    """Bind the exact R13 declaration and unchanged R12.1 registry."""
    logger.debug("intrinsic_observer_echo_effect_digest entry")
    result = sha256(canonical_json(intrinsic_observer_echo_effect_data()).encode()).hexdigest()
    logger.debug("intrinsic_observer_echo_effect_digest exit digest=%s", result)
    return result
