"""Closed DTOs for matched post-closure semantic intervention pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    SemanticAblationReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticCouplingReceipt,
    SemanticTickReceipt,
)


class MatchedPostClosureEventKind(str, Enum):
    FORMATION_HISTORY_PLAN_COMMIT = "formation-history-plan-commit"
    ABLATION_CONTRACT_COMMIT = "ablation-contract-commit"
    MATCH_PLAN_COMMIT = "match-plan-commit"
    SELECTION = "selection"
    FORMATION_BINDING = "formation-binding"
    SEMANTIC_FORMATION_BRIDGE = "semantic-formation-bridge"
    FIRST_CLOSURE = "first-closure"
    UNABLATED_BRANCH = "unablated-branch"
    ABLATION = "ablation"
    CONTROL_TICK = "control-tick"
    ABLATED_TICK = "ablated-tick"
    CONTROL_OBSERVATION = "control-observation"
    ABLATED_OBSERVATION = "ablated-observation"
    MATCHED_RESULT = "matched-result"


class MatchedPostClosureStatus(str, Enum):
    WITNESSED = "witnessed-post-closure-maintenance-efficacy-divergence"
    REFUTED = "refuted-no-post-closure-maintenance-efficacy-divergence"


@dataclass(frozen=True)
class P3OGMatchedPostClosurePlan:
    """Selection-free matched continuation committed before candidate selection."""

    version: str
    semantic_formation_history_plan_digest: str
    semantic_ablation_contract_digest: str
    lineage_id: str
    scope_digest: str
    continuation_rule_id: str
    continuation_steps: int
    observation_rule_id: str
    observation_input: int
    graph_rule_id: str
    max_events: int
    max_parents_per_event: int
    plan_digest: str


@dataclass(frozen=True)
class MatchedPostClosureEvent:
    event_id: str
    kind: MatchedPostClosureEventKind
    parent_ids: tuple[str, ...]
    logical_time: int
    lineage_id: str
    scope_digest: str
    payload_digest: str
    event_digest: str


@dataclass(frozen=True)
class P3OGMatchedPostClosureEvidence:
    """Matched control/ablation histories starting from one exact first-closure cut."""

    version: str
    match_plan_digest: str
    semantic_formation_bridge_evidence_digest: str
    closure_payload_digest: str
    control_initial: P3OGSemanticConfiguration
    ablated_initial: P3OGSemanticConfiguration
    ablation_receipt: SemanticAblationReceipt
    control_ticks: tuple[SemanticTickReceipt, ...]
    ablated_ticks: tuple[SemanticTickReceipt, ...]
    control_final: P3OGSemanticConfiguration
    ablated_final: P3OGSemanticConfiguration
    control_observation_after: P3OGSemanticConfiguration
    ablated_observation_after: P3OGSemanticConfiguration
    control_observation: SemanticCouplingReceipt
    ablated_observation: SemanticCouplingReceipt
    first_transition_divergence_step: int | None
    liveness_diverged: bool
    response_diverged: bool
    status: MatchedPostClosureStatus
    reason: str
    events: tuple[MatchedPostClosureEvent, ...]
    closure_event_id: str
    ablation_event_id: str
    control_observation_event_id: str
    ablated_observation_event_id: str
    result_event_id: str
    ancestry_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_MATCHED_POST_CLOSURE_NONCLAIMS = (
    "external-or-real-world-chronology-authentication",
    "consumed-one-shot-capability",
    "full-def-og-006-discharge",
    "full-def-og-007-discharge",
    "full-def-og-008-discharge",
    "full-def-og-009-discharge",
    "same-historical-token",
    "birth-core-or-historical-token",
    "endogenous-observer-role",
    "doctrine-admission",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "physical-birth-or-consciousness",
    "absolute-observerhood-or-object-adoption",
    "promotion",
)
