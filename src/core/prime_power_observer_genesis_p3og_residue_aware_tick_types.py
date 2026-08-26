"""Closed DTOs for residue-aware P3-OG semantic tick pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_autonomous_tick_types import MaintenanceCreditClass
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticOperationMode,
)
from .prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
    TransitionKind,
)


class ResiduePresenceClass(str, Enum):
    ABSENT = "retained-residue-is-none"
    PRESENT = "retained-residue-is-present"


@dataclass(frozen=True)
class ResidueAwareTickRule:
    maintenance_control: MaintenanceControlState
    credit_class: MaintenanceCreditClass
    residue_class: ResiduePresenceClass
    transition_kind: TransitionKind


@dataclass(frozen=True)
class P3OGResidueAwareTickSource:
    """Pre-selection extension of one exact v1 Q_sem/autonomous kernel."""

    version: str
    pressure_source_digest: str
    base_autonomous_source_digest: str
    semantic_configuration_contract_digest: str
    rules: tuple[ResidueAwareTickRule, ...]
    rule_id: str
    absent_kernel_rule_id: str
    source_digest: str


@dataclass(frozen=True)
class ResidueAwareSemanticTickReceipt:
    mode: SemanticOperationMode
    residue_class: ResiduePresenceClass | None
    selected_kind: TransitionKind
    before_configuration_digest: str
    native_before_state_digest: str
    native_receipt_digest: str
    native_after_state_digest: str
    after_configuration_digest: str
    receipt_digest: str


class ResidueAwareFormationCompatibilityStatus(str, Enum):
    WITNESSED = "witnessed-residue-aware-tick-equals-v1-on-formation-genealogy"


@dataclass(frozen=True)
class P3OGResidueAwareFormationCompatibilityEvidence:
    version: str
    residue_aware_source_digest: str
    semantic_formation_bridge_evidence_digest: str
    selected_seed_digest: str
    q_seed: P3OGSemanticConfiguration
    ticks: tuple[ResidueAwareSemanticTickReceipt, ...]
    final_configuration: P3OGSemanticConfiguration
    all_steps_residue_absent: bool
    first_closure_step: int
    status: ResidueAwareFormationCompatibilityStatus
    reason: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_RESIDUE_AWARE_TICK_NONCLAIMS = (
    "v1-feedback-grammar-general-impossibility-theorem",
    "residue-aware-tick-is-upstream-native-api",
    "full-def-og-001-discharge",
    "full-def-og-002-discharge",
    "full-def-og-003-discharge",
    "universal-def-og-004-theorem",
    "full-def-og-005-discharge",
    "full-def-og-006-through-def-og-009-discharge",
    "same-historical-token",
    "endogenous-observer-role",
    "doctrine-admission",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "promotion",
)
