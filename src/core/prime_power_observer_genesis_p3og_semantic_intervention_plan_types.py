"""Closed DTOs for a selection-free P3-OG semantic intervention plan."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class P3OGSemanticContinuationSpec:
    """One precommitted semantic continuation in the finite catalog."""

    entry_id: str
    tick_rule_id: str
    steps: int
    schedule_digest: str
    spec_digest: str


@dataclass(frozen=True)
class P3OGSemanticComparisonCut:
    """One precommitted observation cut after a named continuation entry."""

    cut_id: str
    continuation_entry_id: str
    observation_rule_id: str
    observation_input: int
    cut_digest: str


@dataclass(frozen=True)
class P3OGSemanticInterventionPlan:
    """Selection-free matched-intervention grammar committed before outcomes."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    semantic_configuration_contract_digest: str
    semantic_formation_bridge_contract_digest: str
    semantic_ablation_contract_digest: str
    maintenance_component_id: str
    continuation_catalog: tuple[P3OGSemanticContinuationSpec, ...]
    continuation_catalog_digest: str
    comparison_cuts: tuple[P3OGSemanticComparisonCut, ...]
    comparison_cut_catalog_digest: str
    code_identity_rule_id: str
    arithmetic_input_match_rule_id: str
    external_schedule_match_rule_id: str
    scope_match_rule_id: str
    semantic_scope_digest: str
    max_continuations: int
    max_comparison_cuts: int
    nonclaims: tuple[str, ...]
    plan_digest: str


P3OG_SEMANTIC_INTERVENTION_PLAN_NONCLAIMS = (
    "standalone-plan-is-not-history-evidence",
    "plan-commitment-is-not-external-chronology-authentication",
    "selection-free-plan-does-not-authenticate-selection-history",
    "singleton-continuation-catalog-is-not-full-def-og-005-discharge",
    "typed-ablation-contract-is-not-post-formation-ablation-cut",
    "matched-branch-equality-not-yet-executed",
    "comparison-cut-not-yet-observed",
    "retained-distinction-not-yet-proven-over-continuation",
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
