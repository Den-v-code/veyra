"""Closed receipt types for R12.3 evidence-aware intrinsic VAM lowering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .shadow_effect_types import (
    BridgeCapability,
    CarrierId,
    EvidenceClass,
    EvidenceScope,
)


class IntrinsicLoweringLane(str, Enum):
    """Exact supported source lanes; no legacy shadow lane exists."""

    R7_RECURRENCE = "r7-recurrence"
    R9_INTRINSIC_MODE = "r9-intrinsic-mode"
    R11_BRANDED_OBSERVATION = "r11-branded-observation"
    R11_ECHO_OUTCOME = "r11-echo-outcome"


@dataclass(frozen=True, slots=True)
class IntrinsicLoweringReceipt:
    """Mutation-evident executable-witness receipt for one exact lowering."""

    schema: str
    lane: IntrinsicLoweringLane
    source: CarrierId
    provenance: CarrierId
    target: CarrierId
    capabilities: tuple[BridgeCapability, ...]
    evidence_class: EvidenceClass
    evidence_scope: EvidenceScope
    evidence_id: str
    source_digests: tuple[str, ...]
    observer_digest: str
    response_kind_digest: str
    payload_digest: str
    ir_digest: str
    boundary: str
    binding_digest: str
    promotion_ready: bool


@dataclass(frozen=True, slots=True)
class TransportedIntrinsicIR:
    """One intrinsic value carried only with its exact R12.3 receipt."""

    value: object
    receipt: IntrinsicLoweringReceipt
