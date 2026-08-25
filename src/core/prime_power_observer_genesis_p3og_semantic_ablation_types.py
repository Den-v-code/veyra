"""Closed DTOs for selection-free P3-OG semantic maintenance ablation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class P3OGSemanticAblationContract:
    """Pre-selection contract for one typed maintenance-component ablation."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    semantic_configuration_contract_digest: str
    component_id: str
    ablation_rule_id: str
    unchanged_fields: tuple[str, ...]
    contract_digest: str


@dataclass(frozen=True)
class SemanticAblationReceipt:
    """One exact Q_sem intervention changing only the named component."""

    component_id: str
    before_configuration_digest: str
    after_configuration_digest: str
    unchanged_fields_digest: str
    read_before: int | None
    read_after: int | None
    receipt_digest: str


P3OG_SEMANTIC_ABLATION_NONCLAIMS = (
    "post-formation-chronology-without-history",
    "before-later-efficacy-observation-cut",
    "matched-history-causal-efficacy",
    "full-def-og-006-discharge",
    "full-def-og-007-discharge",
    "full-def-og-008-discharge",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "physical-birth-or-consciousness",
    "promotion",
)
