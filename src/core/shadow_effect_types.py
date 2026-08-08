"""Closed R12.1 types for shadow-bridge effects and evidence provenance."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CarrierId(str, Enum):
    """Closed carrier vocabulary for the first effect-registry slice."""

    R7_RECURRENCE = "r7-recurrence"
    R9_INTRINSIC_MODE = "r9-intrinsic-mode-image"
    R11_RESPONSE = "r11-observer-response"
    VAM_INTRINSIC_IR = "vam-intrinsic-ir"
    LEGACY_CORE = "legacy-core-value"
    LEGACY_VAM_SHADOW = "legacy-vam-shadow"


class BridgeCapability(str, Enum):
    """Atomic bridge facts; named directions are derived, never asserted."""

    PRESERVES = "preserves"
    REFLECTS = "reflects"
    COLLAPSE_WITNESS = "collapse-witness"
    LEFT_ROUND_TRIP = "left-round-trip"
    RIGHT_ROUND_TRIP = "right-round-trip"


class BridgeDirection(str, Enum):
    """Human-facing strongest classification of one exact capability row."""

    PRESERVATION = "preservation"
    QUOTIENT = "quotient"
    REFLECTION = "reflection"
    FAITHFUL = "faithful"
    EQUIVALENCE = "equivalence"


class EvidenceClass(str, Enum):
    """Disjoint evidence origins with no implicit total strength ordering."""

    KERNEL_PROOF = "kernel-proof"
    FORMAL_BRIDGE = "formal-bridge"
    FINITE_OBLIGATION = "finite-obligation"
    EXECUTABLE_WITNESS = "executable-witness"
    VAM_CERT = "vam-cert"
    SHADOW = "shadow"


class EvidenceScope(str, Enum):
    """Whether evidence is general on its carrier or explicitly finite."""

    GENERAL = "general"
    FINITE = "finite"


@dataclass(frozen=True)
class EvidenceRef:
    """One exact evidence reference; it is not evidence verification itself."""

    evidence_class: EvidenceClass
    evidence_id: str
    scope: EvidenceScope
    boundary: str

    @property
    def may_enter_promotion_contract(self) -> bool:
        """Only a general kernel proof may be proposed to the separate R8 gate."""
        return self.evidence_class is EvidenceClass.KERNEL_PROOF and self.scope is EvidenceScope.GENERAL


@dataclass(frozen=True)
class BridgeClaim:
    """A typed bridge claim whose direction is derived from capabilities."""

    bridge_id: str
    source: CarrierId
    target: CarrierId
    capabilities: tuple[BridgeCapability, ...]
    evidence: tuple[EvidenceRef, ...]
    scope: EvidenceScope
    boundary: str


@dataclass(frozen=True)
class ObservationBrand:
    """Observer/source/kind identity bound to one R11 observation."""

    schema: str
    source: CarrierId
    observer_digest: str
    response_kind_digest: str
    binding_digest: str


@dataclass(frozen=True)
class BrandedObservation:
    """An R11 Ready/Blocked observation plus its canonical payload digest."""

    brand: ObservationBrand
    observation: object
    payload_digest: str
