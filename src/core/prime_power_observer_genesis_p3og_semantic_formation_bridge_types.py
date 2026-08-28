"""Closed DTOs for the current one-shot P3-OG semantic-formation bridge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticTickReceipt,
)


class SemanticFormationBridgeStatus(str, Enum):
    """Status of the exact Q_sem first-return bridge only."""

    WITNESSED = "witnessed-current-semantic-formation-first-return-bridge"


@dataclass(frozen=True)
class P3OGSemanticFormationBridgeContract:
    """Selection-free contract binding current native-formation rules to Q_sem."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    semantic_configuration_contract_digest: str
    native_formation_source_version: str
    formation_state_rule_id: str
    formation_rule_id: str
    resource_rule_id: str
    max_formation_ticks: int
    bridge_rule_id: str
    closure_rule_id: str
    contract_digest: str


@dataclass(frozen=True)
class SemanticFormationBridgeStep:
    """One current formation tick replayed through the exact semantic carrier."""

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
    """Positive bridge from one-shot native formation into Q_sem genealogy."""

    version: str
    bridge_contract_digest: str
    formation_source_digest: str
    formation_evidence_digest: str
    selection_source_digest: str
    selection_receipt_digest: str
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
    "standalone-bridge-is-not-history-evidence",
    "strict-past-selection-commitment-not-reestablished-by-bridge",
    "declared-event-source-closure-binding",
    "external-or-real-world-chronology-authentication",
    "process-global-unforgeable-linear-capability",
    "copied-available-value-anti-replay",
    "full-def-og-001-discharge",
    "full-def-og-002-discharge",
    "full-def-og-003-discharge",
    "typed-post-formation-ablation",
    "full-def-og-006-discharge",
    "same-token-causal-efficacy",
    "full-def-og-008-discharge",
    "full-def-og-009-discharge",
    "primitive-rez-nod-tact-breath-genealogy",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "physical-birth-or-consciousness",
    "absolute-observerhood-or-object-adoption",
    "promotion",
)
