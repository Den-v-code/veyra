"""Closed DTOs for the finite P3-OG semantic configuration quotient."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
    TransitionKind,
)


class SemanticOperationMode(str, Enum):
    """How one semantic operation relates to the existing operational machine."""

    NATIVE_QUOTIENT = "native-operational-quotient"
    REMOVED_TOTALIZATION = "removed-absorbing-totalization"


@dataclass(frozen=True)
class P3OGSemanticConfigurationContract:
    """Pre-selection finite-Q contract with explicit operation and resource rules."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    state_rule_id: str
    tick_rule_id: str
    couple_rule_id: str
    read_rule_id: str
    residue_rule_id: str
    boundary_rule_id: str
    alive_rule_id: str
    removed_totalization_rule_id: str
    max_input_bits: int
    max_transition_count: int
    contract_digest: str


@dataclass(frozen=True)
class P3OGSemanticConfiguration:
    """Semantic Q: native machine configuration without evidence-monotone fields."""

    run_id: str
    seed_digest: str
    boundary: BoundaryState
    maintenance_control: MaintenanceControlState
    phase: int
    retained_residue: int | None
    maintenance_credit: int
    configuration_digest: str


@dataclass(frozen=True)
class SemanticTickReceipt:
    """One total semantic tick with an exact native quotient witness."""

    mode: SemanticOperationMode
    selected_kind: TransitionKind
    before_configuration_digest: str
    native_before_state_digest: str
    native_receipt_digest: str
    native_after_state_digest: str
    after_configuration_digest: str
    receipt_digest: str


@dataclass(frozen=True)
class SemanticCouplingReceipt:
    """One total semantic coupling; removed coupling is an explicit totalization."""

    mode: SemanticOperationMode
    input_value: int
    before_configuration_digest: str
    native_before_state_digest: str | None
    native_receipt_digest: str | None
    native_after_state_digest: str | None
    after_configuration_digest: str
    response: int | None
    receipt_digest: str


P3OG_SEMANTIC_CONFIGURATION_NONCLAIMS = (
    "removed-coupling-totalization-is-existing-native-operation",
    "unbounded-operational-replay-equivalence",
    "full-def-og-001-discharge",
    "standalone-semantic-configuration-is-not-history-evidence",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "declared-event-source-closure-binding",
    "external-or-real-world-chronology-authentication",
    "full-def-og-002-discharge",
    "full-def-og-003-discharge",
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
    "promotion",
)
