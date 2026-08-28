"""Closed DTOs for current P3-OG retained-residue phase sensitivity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_types import TransitionKind


class SemanticResiduePhaseEffectStatus(str, Enum):
    """Status of one exact later ADVANCE phase-sensitivity replay."""

    WITNESSED = "witnessed-retained-residue-changes-later-advance-phase"
    REFUTED = "refuted-retained-residue-changes-later-advance-phase"


@dataclass(frozen=True)
class P3OGSemanticResiduePhaseEffectEvidence:
    """One later transition outcome bound to an earlier retained residue."""

    version: str
    retained_difference_evidence_digest: str
    selected_seed_digest: str
    comparison_step: int
    left_coupling_response: int | None
    right_coupling_response: int | None
    equal_coupling_response: bool
    left_residue: int
    right_residue: int
    residues_distinct: bool
    left_selected_kind: TransitionKind
    right_selected_kind: TransitionKind
    same_advance_kind: bool
    left_before_phase: int
    right_before_phase: int
    before_matched_except_residue: bool
    left_after_phase: int
    right_after_phase: int
    phase_diverged: bool
    transition_law_bound: bool
    status: SemanticResiduePhaseEffectStatus
    reason: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_SEMANTIC_RESIDUE_PHASE_EFFECT_NONCLAIMS = (
    "different-later-transition-kind",
    "different-later-readiness-state",
    "different-later-typed-response",
    "same-historical-token-causal-efficacy",
    "full-def-og-008-discharge",
    "arithmetic-source-preselection-history-binding",
    "standalone-witness-does-not-prove-intervention-plan-strict-past",
    "universal-def-og-004-theorem",
    "full-def-og-004-discharge",
    "full-def-og-009-discharge",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "promotion",
)
