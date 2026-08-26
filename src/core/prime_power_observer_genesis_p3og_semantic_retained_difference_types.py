"""Closed DTOs for semantic retained-difference pressure in P3-OG."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticCouplingReceipt,
    SemanticTickReceipt,
)


class SemanticRetainedDifferenceStatus(str, Enum):
    WITNESSED = "witnessed-retained-difference-over-declared-prefix-catalog"
    REFUTED = "refuted-retained-difference-over-declared-prefix-catalog"


@dataclass(frozen=True)
class P3OGSemanticRetainedDifferencePlan:
    """Selection-free common-continuation plan for exact arithmetic F0/F1 inputs."""

    version: str
    semantic_formation_bridge_contract_digest: str
    arithmetic_input_source_digest: str
    continuation_rule_id: str
    continuation_lengths: tuple[int, ...]
    max_steps: int
    plan_digest: str


@dataclass(frozen=True)
class P3OGSemanticRetainedDifferenceEvidence:
    """Two exact semantic runs from one first-closure state under a common tick law."""

    version: str
    plan_digest: str
    semantic_formation_bridge_evidence_digest: str
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
    every_prefix_residues_distinct: bool
    every_prefix_boundary_alive: bool
    status: SemanticRetainedDifferenceStatus
    reason: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS = (
    "different-response-required-for-retained-difference",
    "retained-residue-causes-later-transition-or-response",
    "universal-def-og-004-theorem",
    "full-def-og-005-discharge",
    "all-possible-continuation-catalogs",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "same-historical-token",
    "birth-core-or-historical-token",
    "endogenous-observer-role",
    "doctrine-admission",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "promotion",
)
