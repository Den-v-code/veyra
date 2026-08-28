"""Closed DTOs for current semantic retained-difference evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticCouplingReceipt,
    SemanticTickReceipt,
)


class SemanticRetainedDifferenceStatus(str, Enum):
    """Status of one exact bounded retained-difference replay."""

    WITNESSED = "witnessed-retained-difference-over-declared-continuation"
    REFUTED = "refuted-retained-difference-over-declared-continuation"


@dataclass(frozen=True)
class P3OGSemanticRetainedDifferenceEvidence:
    """Two exact F0/F1 semantic branches under one committed continuation."""

    version: str
    intervention_plan_digest: str
    arithmetic_input_source_digest: str
    semantic_formation_bridge_evidence_digest: str
    selected_seed_digest: str
    continuation_entry_id: str
    continuation_spec_digest: str
    continuation_steps: int
    q0: P3OGSemanticConfiguration
    left_coupled: P3OGSemanticConfiguration
    right_coupled: P3OGSemanticConfiguration
    left_coupling: SemanticCouplingReceipt
    right_coupling: SemanticCouplingReceipt
    left_configurations: tuple[P3OGSemanticConfiguration, ...]
    right_configurations: tuple[P3OGSemanticConfiguration, ...]
    left_ticks: tuple[SemanticTickReceipt, ...]
    right_ticks: tuple[SemanticTickReceipt, ...]
    initial_residues_distinct: bool
    every_step_residues_distinct: bool
    every_step_boundary_alive: bool
    status: SemanticRetainedDifferenceStatus
    reason: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS = (
    "standalone-witness-does-not-prove-intervention-plan-strict-past",
    "arithmetic-source-preselection-history-binding",
    "retained-residue-causes-later-transition-or-response",
    "comparison-cut-observation",
    "universal-def-og-004-theorem",
    "full-def-og-004-discharge",
    "full-def-og-005-discharge",
    "full-def-og-006-discharge",
    "full-def-og-007-discharge",
    "full-def-og-008-discharge",
    "full-def-og-009-discharge",
    "same-historical-token",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "physical-birth-or-consciousness",
    "promotion",
)
