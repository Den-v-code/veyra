"""Closed DTOs for matched semantic maintenance-ablation removal pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    SemanticAblationReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticTickReceipt,
)


class SemanticMatchedAblationRemovalStatus(str, Enum):
    """Status of one exact matched maintenance-removal replay."""

    WITNESSED = "witnessed-matched-ablation-removes-declared-ability"
    REFUTED = "refuted-matched-ablation-removes-declared-ability"


@dataclass(frozen=True)
class P3OGSemanticMatchedAblationRemovalEvidence:
    """Matched F0/F1 ablation replay under the already declared continuation."""

    version: str
    intervention_plan_digest: str
    semantic_scope_digest: str
    ablation_contract_digest: str
    retained_difference_evidence_digest: str
    phase_effect_evidence_digest: str
    selected_seed_digest: str
    component_id: str
    continuation_entry_id: str
    continuation_spec_digest: str
    continuation_steps: int
    left_input: int
    right_input: int
    left_ablated_initial: P3OGSemanticConfiguration
    right_ablated_initial: P3OGSemanticConfiguration
    left_ablation: SemanticAblationReceipt
    right_ablation: SemanticAblationReceipt
    left_ablated_configurations: tuple[P3OGSemanticConfiguration, ...]
    right_ablated_configurations: tuple[P3OGSemanticConfiguration, ...]
    left_ablated_ticks: tuple[SemanticTickReceipt, ...]
    right_ablated_ticks: tuple[SemanticTickReceipt, ...]
    matched_initials_except_component: bool
    arithmetic_inputs_bound: bool
    direct_reads_preserved: bool
    unablated_boundaries_alive: bool
    ablated_boundaries_removed: bool
    ablated_residues_cleared: bool
    claimed_ability_destroyed: bool
    status: SemanticMatchedAblationRemovalStatus
    reason: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_SEMANTIC_MATCHED_ABLATION_REMOVAL_NONCLAIMS = (
    "standalone-witness-is-not-complete-event-history",
    "ablation-cut-not-yet-bound-into-noncircular-history-dag",
    "external-or-real-world-chronology-authentication",
    "full-def-og-006-discharge",
    "full-def-og-007-discharge",
    "same-historical-token-causal-efficacy",
    "full-def-og-008-discharge",
    "full-def-og-009-discharge",
    "universal-ablation-separator-theorem",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "promotion",
)
