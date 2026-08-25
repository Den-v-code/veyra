"""Closed DTOs for bounded P3-OG formation-history replay pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FormationHistoryEventKind(str, Enum):
    SOURCE_COMMIT = "source-commit"
    AUTONOMOUS_LAW_COMMIT = "autonomous-law-commit"
    FORMATION_CONTRACT_COMMIT = "formation-contract-commit"
    HISTORY_PLAN_COMMIT = "history-plan-commit"
    SELECTION = "selection"
    FORMATION_SOURCE_BIND = "formation-source-bind"
    FORMATION_TICK = "formation-tick"
    FIRST_CLOSURE = "first-closure"
    DECISIVE_CRITERION = "decisive-criterion"
    LATER_RESULT = "later-result"


class FormationHistoryStatus(str, Enum):
    """Status of the bounded replay graph only, not historical actualization."""

    WITNESSED = "witnessed-bounded-noncircular-formation-replay-graph"


@dataclass(frozen=True)
class P3OGFormationHistoryPlan:
    """Outcome-free plan fixed by pressure/autonomous sources only."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    formation_contract_digest: str
    lineage_id: str
    scope_digest: str
    graph_rule_id: str
    max_events: int
    max_parents_per_event: int
    plan_digest: str


@dataclass(frozen=True)
class FormationHistoryEvent:
    event_id: str
    kind: FormationHistoryEventKind
    parent_ids: tuple[str, ...]
    logical_time: int
    lineage_id: str
    scope_digest: str
    payload_digest: str
    event_digest: str


@dataclass(frozen=True)
class P3OGFormationHistoryEvidence:
    """Typed DAG around one witnessed native formation replay."""

    version: str
    plan_digest: str
    formation_source_digest: str
    formation_evidence_digest: str
    criterion_payload_digest: str
    later_result_payload_digest: str
    events: tuple[FormationHistoryEvent, ...]
    closure_event_id: str
    criterion_event_id: str
    later_result_event_id: str
    strict_past_event_ids: tuple[str, ...]
    future_event_ids: tuple[str, ...]
    status: FormationHistoryStatus
    ancestry_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_FORMATION_HISTORY_NONCLAIMS = (
    "external-or-real-world-chronology-authentication",
    "criterion-truth-or-result-truth",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "full-def-og-002-discharge",
    "full-def-og-003-discharge",
    "full-def-og-009-discharge",
    "semantic-nonderivability-of-future-seals",
    "declared-doctrine-or-external-semantic-scope",
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
    "absolute-observerhood-or-object-adoption",
    "promotion",
)
