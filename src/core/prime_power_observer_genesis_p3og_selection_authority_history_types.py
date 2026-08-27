"""Closed DTOs for P3-OG local-authority to typed-history binding."""

from __future__ import annotations

from dataclasses import dataclass


P3OG_SELECTION_AUTHORITY_HISTORY_BOUNDARY = (
    "one preselection plan binds the exact base history plan to one RESERVED local "
    "authority receipt, and fresh final validation binds that same plan-backed local "
    "consume to one exact typed-history selection trace; no trusted chronology, "
    "cross-store uniqueness, operator non-bypass, or detached replay authority"
)


@dataclass(frozen=True, slots=True)
class P3OGSelectionAuthorityHistoryPlan:
    """Outcome-free preselection binding between history plan and local reservation."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    formation_history_plan_digest: str
    selection_source_digest: str
    source_closure_digest: str
    available_capability_digest: str
    authority_reservation_id: str
    authority_reserved_receipt_digest: str
    authority_capability_digest: str
    boundary: str
    plan_digest: str


@dataclass(frozen=True, slots=True)
class P3OGSelectionAuthorityHistoryBinding:
    """Store-backed identity link between one local consume and one typed-history trace."""

    version: str
    authority_history_plan_digest: str
    formation_history_plan_digest: str
    formation_history_evidence_digest: str
    formation_history_ancestry_digest: str
    formation_terminal_event_id: str
    formation_source_digest: str
    selection_source_digest: str
    source_closure_digest: str
    available_capability_digest: str
    selection_consume_event_digest: str
    selection_receipt_digest: str
    consumed_capability_digest: str
    authority_reserved_receipt_digest: str
    authority_claimed_receipt_digest: str
    authority_attempt_digest: str
    authority_terminal_receipt_digest: str
    authority_evidence_digest: str
    boundary: str
    promotions: int
    nonclaims: tuple[str, ...]
    binding_digest: str


P3OG_SELECTION_AUTHORITY_HISTORY_NONCLAIMS = (
    "full-def-og-002-discharge",
    "external-or-real-world-chronology-authentication",
    "cross-store-or-process-global-uniqueness",
    "operator-non-bypass-or-anti-rollback-storage",
    "undeclared-or-out-of-band-source-dependency-blindness",
    "externally-authenticated-dependency-completeness",
    "detached-binding-dto-is-not-local-store-authority",
    "plan-existence-is-not-a-trusted-preselection-timestamp",
    "full-def-og-003-or-def-og-009-discharge",
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
