"""Exact R12.5 effect/evidence declaration; this is not an R12.1 registry row."""
from __future__ import annotations

from hashlib import sha256
import logging
from types import MappingProxyType

from .proof_core_codec import canonical_json
from .shadow_effect_types import (
    BridgeCapability,
    CarrierId,
    EvidenceClass,
    EvidenceScope,
)
from .shadow_effects import shadow_effect_registry_digest

logger = logging.getLogger(__name__)
EFFECT_SCHEMA = "veyra.intrinsic-vam.formal-effect.r12.5.v1"
EVIDENCE_ID = "veyra.lean.r12.5.intrinsic-vam-tcb.v1"
EFFECT_BOUNDARY = (
    "general Lean preservation only on the valid R12.2 lowering image; Python and "
    "Rust codecs remain bounded reviewed implementations, receipts remain unauthenticated, "
    "and no R8 promotion, certificate, Sage, legacy VAM, or taxonomy claim follows"
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
        "evidence_class": EvidenceClass.FORMAL_BRIDGE,
        "evidence_scope": EvidenceScope.GENERAL,
        "evidence_id": EVIDENCE_ID,
        "boundary": EFFECT_BOUNDARY,
        "promotion_ready": False,
        "taxonomy_changed": False,
    }
)


def intrinsic_vam_formal_effect_data() -> dict[str, object]:
    """Return the one immutable R12.5 declaration in canonical scalar form."""
    logger.debug("intrinsic_vam_formal_effect_data entry")
    row = _EFFECT_ROW
    if (
        row.get("schema") != EFFECT_SCHEMA
        or row.get("sources")
        != (
            CarrierId.R7_RECURRENCE,
            CarrierId.R9_INTRINSIC_MODE,
            CarrierId.R11_RESPONSE,
        )
        or row.get("target") is not CarrierId.VAM_INTRINSIC_IR
        or row.get("capabilities") != (BridgeCapability.PRESERVES,)
        or row.get("evidence_class") is not EvidenceClass.FORMAL_BRIDGE
        or row.get("evidence_scope") is not EvidenceScope.GENERAL
        or row.get("evidence_id") != EVIDENCE_ID
        or row.get("boundary") != EFFECT_BOUNDARY
        or row.get("promotion_ready") is not False
        or row.get("taxonomy_changed") is not False
    ):
        logger.error("intrinsic_vam_formal_effect_data immutable row drift")
        raise ValueError("r12.5-effect-row-invalid")
    result = {
        "schema": EFFECT_SCHEMA,
        "sources": [
            CarrierId.R7_RECURRENCE.value,
            CarrierId.R9_INTRINSIC_MODE.value,
            CarrierId.R11_RESPONSE.value,
        ],
        "target": CarrierId.VAM_INTRINSIC_IR.value,
        "capabilities": [BridgeCapability.PRESERVES.value],
        "evidence": {
            "class": EvidenceClass.FORMAL_BRIDGE.value,
            "scope": EvidenceScope.GENERAL.value,
            "id": EVIDENCE_ID,
        },
        "boundary": EFFECT_BOUNDARY,
        "promotion_ready": False,
        "taxonomy_changed": False,
    }
    logger.debug("intrinsic_vam_formal_effect_data exit")
    return result


def intrinsic_vam_formal_effect_digest() -> str:
    """Bind the exact effect row and the unchanged audited R12.1 registry."""
    logger.debug("intrinsic_vam_formal_effect_digest entry")
    payload = {
        "effect": intrinsic_vam_formal_effect_data(),
        "r12_1_registry_digest": shadow_effect_registry_digest(),
    }
    result = sha256(canonical_json(payload).encode()).hexdigest()
    logger.debug("intrinsic_vam_formal_effect_digest exit digest=%s", result)
    return result
