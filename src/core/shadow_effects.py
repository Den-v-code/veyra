"""R12.1 bridge-direction and evidence-boundary registry."""

from __future__ import annotations

import logging
from .shadow_effect_branding import canonical_data_bytes, digest_bytes, reject
from .shadow_effect_types import (
    BridgeCapability,
    BridgeClaim,
    BridgeDirection,
    CarrierId,
    EvidenceClass,
    EvidenceRef,
    EvidenceScope,
)

logger = logging.getLogger(__name__)
REGISTRY_SCHEMA = "veyra.shadow-effects.r12.1"
MAX_BRIDGE_EVIDENCE = 8
MAX_REGISTRY_ROWS = 16
_DIRECTION_ROWS = {
    (BridgeCapability.PRESERVES,): BridgeDirection.PRESERVATION,
    (BridgeCapability.PRESERVES, BridgeCapability.COLLAPSE_WITNESS): BridgeDirection.QUOTIENT,
    (BridgeCapability.REFLECTS,): BridgeDirection.REFLECTION,
    (BridgeCapability.PRESERVES, BridgeCapability.REFLECTS): BridgeDirection.FAITHFUL,
    (
        BridgeCapability.PRESERVES,
        BridgeCapability.REFLECTS,
        BridgeCapability.LEFT_ROUND_TRIP,
        BridgeCapability.RIGHT_ROUND_TRIP,
    ): BridgeDirection.EQUIVALENCE,
}
_CAPABILITY_ORDER = tuple(BridgeCapability)


def _text(value: object, reason: str) -> str:
    if type(value) is not str or not value or len(value) > 512 or any(ord(char) < 0x20 for char in value):
        reject(reason)
    return value


def bridge_direction(capabilities: object) -> BridgeDirection:
    """Derive one named direction from an exact canonical capability tuple."""
    logger.debug("bridge_direction entry type=%s", type(capabilities).__name__)
    if type(capabilities) is not tuple or not capabilities:
        reject("invalid-capability-row")
    if any(type(item) is not BridgeCapability for item in capabilities):
        reject("invalid-capability-row")
    canonical = tuple(item for item in _CAPABILITY_ORDER if item in capabilities)
    if len(set(capabilities)) != len(capabilities) or capabilities != canonical:
        reject("noncanonical-capability-row")
    result = _DIRECTION_ROWS.get(capabilities)
    if result is None:
        reject("unsupported-capability-combination")
    logger.debug("bridge_direction exit direction=%s", result.value)
    return result


def validate_evidence(item: object) -> EvidenceRef:
    """Validate one exact evidence reference without treating it as a proof."""
    logger.debug("validate_evidence entry type=%s", type(item).__name__)
    if type(item) is not EvidenceRef:
        reject("invalid-evidence-reference")
    if type(item.evidence_class) is not EvidenceClass or type(item.scope) is not EvidenceScope:
        reject("invalid-evidence-enum")
    _text(item.evidence_id, "invalid-evidence-id")
    _text(item.boundary, "invalid-evidence-boundary")
    if (
        item.scope is EvidenceScope.GENERAL
        and item.evidence_class
        not in {EvidenceClass.KERNEL_PROOF, EvidenceClass.FORMAL_BRIDGE, EvidenceClass.SHADOW}
    ):
        reject("finite-evidence-scope-escalation")
    logger.debug("validate_evidence exit class=%s scope=%s", item.evidence_class.value, item.scope.value)
    return item


def validate_bridge_claim(claim: object) -> BridgeClaim:
    """Validate a bridge claim and reject evidence laundering or escalation."""
    logger.debug("validate_bridge_claim entry type=%s", type(claim).__name__)
    if type(claim) is not BridgeClaim:
        reject("invalid-bridge-claim")
    _text(claim.bridge_id, "invalid-bridge-id")
    _text(claim.boundary, "invalid-bridge-boundary")
    if type(claim.source) is not CarrierId or type(claim.target) is not CarrierId:
        reject("invalid-carrier")
    if (
        type(claim.scope) is not EvidenceScope
        or type(claim.evidence) is not tuple
        or not claim.evidence
        or len(claim.evidence) > MAX_BRIDGE_EVIDENCE
    ):
        reject("invalid-bridge-evidence")
    bridge_direction(claim.capabilities)
    evidence = tuple(validate_evidence(item) for item in claim.evidence)
    identities = tuple((item.evidence_class, item.evidence_id) for item in evidence)
    if len(set(identities)) != len(identities):
        reject("duplicate-evidence-reference")
    if any(item.scope is not claim.scope for item in evidence):
        reject("mixed-evidence-scope")
    if claim.scope is EvidenceScope.GENERAL and not any(
        item.evidence_class is EvidenceClass.KERNEL_PROOF for item in evidence
    ):
        reject("general-bridge-without-kernel-proof")
    audited = {item.bridge_id: item for item in default_shadow_bridge_registry()}
    if claim.bridge_id not in audited or claim != audited[claim.bridge_id]:
        reject("unaudited-bridge-claim")
    logger.debug("validate_bridge_claim exit bridge=%s", claim.bridge_id)
    return claim


def bridge_claim_data(claim: object) -> dict[str, object]:
    """Serialize one validated bridge claim with a derived direction."""
    logger.debug("bridge_claim_data entry")
    valid = validate_bridge_claim(claim)
    result = {
        "bridge_id": valid.bridge_id,
        "source": valid.source.value,
        "target": valid.target.value,
        "direction": bridge_direction(valid.capabilities).value,
        "capabilities": [item.value for item in valid.capabilities],
        "scope": valid.scope.value,
        "evidence": [
            {
                "class": item.evidence_class.value,
                "id": item.evidence_id,
                "scope": item.scope.value,
                "boundary": item.boundary,
                "may_enter_promotion_contract": item.may_enter_promotion_contract,
            }
            for item in valid.evidence
        ],
        "boundary": valid.boundary,
        "promotion_ready": False,
    }
    logger.debug("bridge_claim_data exit bridge=%s", valid.bridge_id)
    return result


def default_shadow_bridge_registry() -> tuple[BridgeClaim, ...]:
    """Return the immutable audited R12.1 registry over existing R9–R11/VAM evidence."""
    logger.debug("default_shadow_bridge_registry entry")
    general_kernel = EvidenceScope.GENERAL
    finite = EvidenceScope.FINITE
    result = (
        BridgeClaim(
            "r9-recurrence-intrinsic-image",
            CarrierId.R7_RECURRENCE,
            CarrierId.R9_INTRINSIC_MODE,
            (
                BridgeCapability.PRESERVES,
                BridgeCapability.REFLECTS,
                BridgeCapability.LEFT_ROUND_TRIP,
                BridgeCapability.RIGHT_ROUND_TRIP,
            ),
            (
                EvidenceRef(EvidenceClass.KERNEL_PROOF, "THM-R9-002..007", general_kernel, "exact intrinsic image only"),
                EvidenceRef(EvidenceClass.FORMAL_BRIDGE, "veyra-intrinsic-mode-tcb-v1", general_kernel, "pinned reviewed bridge"),
            ),
            general_kernel,
            "equivalence only on the fixed-anchor unary intrinsic image",
        ),
        BridgeClaim(
            "r11-equality-to-ready-echo",
            CarrierId.R7_RECURRENCE,
            CarrierId.R11_RESPONSE,
            (BridgeCapability.PRESERVES,),
            (
                EvidenceRef(EvidenceClass.KERNEL_PROOF, "THM-R11-003", general_kernel, "one-way equality lifting"),
                EvidenceRef(EvidenceClass.FORMAL_BRIDGE, "veyra.lean.r11.observer-echo-tcb.v1", general_kernel, "closed observers only"),
            ),
            general_kernel,
            "echo does not imply equality",
        ),
        BridgeClaim(
            "r11-crest-response",
            CarrierId.R7_RECURRENCE,
            CarrierId.R11_RESPONSE,
            (BridgeCapability.PRESERVES, BridgeCapability.COLLAPSE_WITNESS),
            (
                EvidenceRef(EvidenceClass.KERNEL_PROOF, "THM-R11-006", general_kernel, "unequal pulses share crest mark"),
                EvidenceRef(EvidenceClass.FORMAL_BRIDGE, "veyra.lean.r11.observer-echo-tcb.v1", general_kernel, "closed crest observer"),
            ),
            general_kernel,
            "quotient means preservation plus an explicit nonreflection witness",
        ),
        BridgeClaim(
            "legacy-core-to-vam-shadow",
            CarrierId.LEGACY_CORE,
            CarrierId.LEGACY_VAM_SHADOW,
            (BridgeCapability.PRESERVES,),
            (
                EvidenceRef(EvidenceClass.EXECUTABLE_WITNESS, "core-vam-semantic-parity", finite, "bounded compiled subset"),
                EvidenceRef(EvidenceClass.VAM_CERT, "vam-reference-v1:CERT", finite, "accepted finite Echo only"),
            ),
            finite,
            "legacy VAM Shadow/CERT is never kernel-proof or promotion evidence",
        ),
    )
    logger.debug("default_shadow_bridge_registry exit count=%d", len(result))
    return result


def shadow_effect_registry_data(registry: object | None = None) -> dict[str, object]:
    """Return canonical registry data and reject mutable/hostile containers."""
    logger.debug("shadow_effect_registry_data entry type=%s", type(registry).__name__)
    rows = default_shadow_bridge_registry() if registry is None else registry
    if type(rows) is not tuple or not rows or len(rows) > MAX_REGISTRY_ROWS:
        reject("invalid-effect-registry")
    expected_ids = tuple(item.bridge_id for item in default_shadow_bridge_registry())
    if tuple(getattr(item, "bridge_id", None) for item in rows) != expected_ids:
        reject("unaudited-effect-registry")
    claims = [bridge_claim_data(row) for row in rows]
    ids = [row["bridge_id"] for row in claims]
    if len(set(ids)) != len(ids):
        reject("duplicate-bridge-id")
    result = {"schema": REGISTRY_SCHEMA, "rows": claims}
    logger.debug("shadow_effect_registry_data exit count=%d", len(claims))
    return result


def shadow_effect_registry_digest(registry: object | None = None) -> str:
    """Hash the exact canonical R12.1 registry."""
    logger.debug("shadow_effect_registry_digest entry")
    result = digest_bytes(canonical_data_bytes(shadow_effect_registry_data(registry)))
    logger.debug("shadow_effect_registry_digest exit digest=%s", result)
    return result


def shadow_effect_summary() -> dict[str, object]:
    """Return the bounded R12.1 audit summary without a completion claim."""
    logger.debug("shadow_effect_summary entry")
    rows = shadow_effect_registry_data()["rows"]
    result = {
        "schema": REGISTRY_SCHEMA,
        "rows": len(rows),
        "directions": tuple(row["direction"] for row in rows),
        "general": sum(row["scope"] == EvidenceScope.GENERAL.value for row in rows),
        "finite": sum(row["scope"] == EvidenceScope.FINITE.value for row in rows),
        "promotion_ready": sum(bool(row["promotion_ready"]) for row in rows),
        "r12_complete": False,
        "taxonomy_changed": False,
        "digest": shadow_effect_registry_digest(),
    }
    logger.debug("shadow_effect_summary exit rows=%d", result["rows"])
    return result
