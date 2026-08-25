"""Closed DTOs for the P3-OG semantic-formation replay bridge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticTickReceipt,
)


class SemanticFormationBridgeStatus(str, Enum):
    """Status of the exact Q_sem first-return bridge only."""

    WITNESSED = "witnessed-semantic-formation-first-return-bridge"


@dataclass(frozen=True)
class P3OGSemanticFormationBridgeContract:
    """Pre-selection bridge binding two already committed semantic contracts."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    semantic_configuration_contract_digest: str
    native_formation_contract_digest: str
    bridge_rule_id: str
    closure_rule_id: str
    contract_digest: str


@dataclass(frozen=True)
class SemanticFormationBridgeStep:
    """One formation tick replayed through the exact semantic carrier."""

    tick_index: int
    formation_tick_receipt_digest: str
    before_configuration_digest: str
    semantic_tick: SemanticTickReceipt
    after_configuration_digest: str
    departed_after: bool
    closed_after: bool
    receipt_digest: str


@dataclass(frozen=True)
class P3OGSemanticFormationBridgeEvidence:
    """Positive bridge from witnessed native formation into Q_sem genealogy."""

    version: str
    bridge_contract_digest: str
    formation_binding_digest: str
    formation_source_digest: str
    formation_evidence_digest: str
    selected_seed_digest: str
    q_seed: P3OGSemanticConfiguration
    steps: tuple[SemanticFormationBridgeStep, ...]
    final_configuration: P3OGSemanticConfiguration
    departure_step: int
    first_closure_step: int
    status: SemanticFormationBridgeStatus
    reason: str
    genealogy_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_SEMANTIC_FORMATION_BRIDGE_NONCLAIMS = (
    "operational-receipt-identity-across-semantic-quotient",
    "removed-coupling-totalization-is-existing-native-operation",
    "full-def-og-001-discharge",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "full-def-og-002-discharge",
    "typed-history-dag-or-full-def-og-003",
    "full-def-og-009-discharge",
    "primitive-rez-nod-tact-breath-genealogy",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "typed-post-formation-ablation",
    "same-token-causal-efficacy",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "physical-birth-or-consciousness",
    "absolute-observerhood-or-object-adoption",
    "promotion",
)
