"""Closed DTOs for matched retained-residue causal-effect pressure in P3-OG."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_residue_aware_tick_types import (
    ResidueAwareSemanticTickReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticCouplingReceipt,
)


class ResidueCausalEffectStatus(str, Enum):
    """Finite program-level causal-sensitivity verdict; not DEF-OG-008."""

    WITNESSED = "witnessed-matched-retained-residue-phase-effect"
    REFUTED = "refuted-matched-retained-residue-phase-effect"


@dataclass(frozen=True)
class P3OGResidueCausalEffectPlan:
    """Pre-selection criterion for one matched equal-response F0/F1 comparison."""

    version: str
    semantic_formation_bridge_contract_digest: str
    arithmetic_input_source_digest: str
    residue_aware_source_digest: str
    before_match_rule_id: str
    tick_match_rule_id: str
    effect_rule_id: str
    effect_coordinate: str
    plan_digest: str


@dataclass(frozen=True)
class P3OGResidueCausalEffectEvidence:
    """One replayed matched pair demonstrating or refuting residue-to-phase sensitivity."""

    version: str
    plan_digest: str
    semantic_formation_bridge_evidence_digest: str
    formation_compatibility_evidence_digest: str
    q0: P3OGSemanticConfiguration
    left_coupled: P3OGSemanticConfiguration
    right_coupled: P3OGSemanticConfiguration
    left_coupling: SemanticCouplingReceipt
    right_coupling: SemanticCouplingReceipt
    before_matched_except_residue: bool
    equal_coupling_response: bool
    residues_distinct: bool
    left_tick: ResidueAwareSemanticTickReceipt
    right_tick: ResidueAwareSemanticTickReceipt
    left_after: P3OGSemanticConfiguration
    right_after: P3OGSemanticConfiguration
    same_selected_kind: bool
    same_tick_mode: bool
    selected_advance: bool
    phase_diverged: bool
    after_matched_except_phase_and_residue: bool
    status: ResidueCausalEffectStatus
    reason: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_RESIDUE_CAUSAL_EFFECT_NONCLAIMS = (
    "universal-retained-residue-causal-theorem",
    "f0-f1-input-history-is-a-typed-ablation",
    "do-retained-residue-intervention",
    "same-historical-token-causal-efficacy",
    "full-def-og-004-discharge",
    "full-def-og-006-discharge",
    "full-def-og-007-discharge",
    "full-def-og-008-discharge",
    "full-def-og-009-discharge",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "birth-core-or-historical-token",
    "endogenous-observer-role",
    "doctrine-admission",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "promotion",
)
