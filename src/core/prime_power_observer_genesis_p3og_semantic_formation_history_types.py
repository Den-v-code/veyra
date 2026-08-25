"""Closed DTOs for semantic P3-OG formation-history replay v3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SemanticFormationHistoryEventKind(str, Enum):
    SOURCE_COMMIT = "source-commit"
    AUTONOMOUS_LAW_COMMIT = "autonomous-law-commit"
    SEMANTIC_CONFIGURATION_CONTRACT_COMMIT = "semantic-configuration-contract-commit"
    FORMATION_CONTRACT_COMMIT = "formation-contract-commit"
    SEMANTIC_FORMATION_BRIDGE_CONTRACT_COMMIT = "semantic-formation-bridge-contract-commit"
    HISTORY_PLAN_COMMIT = "history-plan-commit"
    SELECTION = "selection"
    FORMATION_BINDING = "formation-binding"
    SEMANTIC_FORMATION_TICK = "semantic-formation-tick"
    FIRST_CLOSURE = "first-closure"
    DECISIVE_CRITERION = "decisive-criterion"
    LATER_RESULT = "later-result"


class SemanticFormationHistoryStatus(str, Enum):
    """Status of the bounded semantic formation DAG only."""

    WITNESSED = "witnessed-semantic-formation-history-replay-graph"


@dataclass(frozen=True)
class P3OGSemanticFormationHistoryPlan:
    """Outcome-free graph plan committed before deterministic selection."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    semantic_configuration_contract_digest: str
    formation_contract_digest: str
    semantic_formation_bridge_contract_digest: str
    lineage_id: str
    scope_digest: str
    graph_rule_id: str
    max_events: int
    max_parents_per_event: int
    plan_digest: str


@dataclass(frozen=True)
class SemanticFormationHistoryEvent:
    event_id: str
    kind: SemanticFormationHistoryEventKind
    parent_ids: tuple[str, ...]
    logical_time: int
    lineage_id: str
    scope_digest: str
    payload_digest: str
    event_digest: str


@dataclass(frozen=True)
class P3OGSemanticFormationHistoryEvidence:
    """Typed DAG around one Q_sem first-return formation witness."""

    version: str
    plan_digest: str
    formation_binding_digest: str
    semantic_formation_bridge_evidence_digest: str
    closure_payload_digest: str
    criterion_payload_digest: str
    later_result_payload_digest: str
    events: tuple[SemanticFormationHistoryEvent, ...]
    closure_event_id: str
    criterion_event_id: str
    later_result_event_id: str
    strict_past_event_ids: tuple[str, ...]
    future_event_ids: tuple[str, ...]
    status: SemanticFormationHistoryStatus
    ancestry_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_SEMANTIC_FORMATION_HISTORY_NONCLAIMS = (
    "external-or-real-world-chronology-authentication",
    "criterion-truth-or-result-truth",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "full-def-og-002-discharge",
    "full-def-og-003-discharge",
    "full-def-og-009-discharge",
    "semantic-nonderivability-of-future-seals",
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
