"""Closed DTOs for bounded P3-OG formation-history replay pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FormationHistoryEventKind(str, Enum):
    SOURCE_COMMIT = "source-commit"
    AUTONOMOUS_LAW_COMMIT = "autonomous-law-commit"
    FORMATION_CONTRACT_COMMIT = "formation-contract-commit"
    PRESELECTION_COMMITMENT = "preselection-commitment"
    SELECTION_POOL_COMMIT = "selection-pool-commit"
    BLIND_SEED_COMMIT = "blind-seed-commit"
    SELECTOR_LAW_COMMIT = "selector-law-commit"
    SELECTION_SOURCE_CLOSURE_COMMIT = "selection-source-closure-commit"
    SELECTION_SOURCE_COMMIT = "selection-source-commit"
    SELECTION_CAPABILITY_AVAILABLE = "selection-capability-available"
    HISTORY_PLAN_COMMIT = "history-plan-commit"
    SELECTION_CONSUME = "selection-consume"
    SELECTION_CAPABILITY_CONSUMED = "selection-capability-consumed"
    FORMATION_SOURCE_BIND = "formation-source-bind"
    FORMATION_TICK = "formation-tick"
    FIRST_CLOSURE = "first-closure"
    FORMATION_REFUTATION = "formation-refutation"
    SEMANTIC_FIRST_CLOSURE = "semantic-first-closure"
    ARITHMETIC_INPUT_SOURCE = "arithmetic-input-source"
    ARITHMETIC_COUPLING = "arithmetic-coupling"
    RETAINED_DIFFERENCE = "retained-difference"
    RESIDUE_PHASE_EFFECT = "residue-phase-effect"
    TYPED_ABLATION = "typed-ablation"
    REMOVAL_DEPENDENCE = "removal-dependence"
    DECISIVE_CRITERION = "decisive-criterion"
    LATER_RESULT = "later-result"


class FormationHistoryStatus(str, Enum):
    """Status of the bounded replay graph only, not historical actualization."""

    WITNESSED = "witnessed-bounded-noncircular-formation-replay-graph"
    REFUTED = "refuted-bounded-one-shot-formation-replay-graph"


@dataclass(frozen=True)
class FormationHistoryPrecommitment:
    """One generic outcome-free commitment inserted before candidate selection."""

    commitment_id: str
    payload_digest: str
    direct_source_event_ids: tuple[str, ...]
    commitment_digest: str


@dataclass(frozen=True)
class FormationHistoryPostClosureBindings:
    """Exact post-closure payloads inserted into the existing v6 DAG."""

    semantic_first_closure_digest: str
    arithmetic_input_source_digest: str
    arithmetic_coupling_digest: str
    retained_difference_digest: str
    residue_phase_effect_digest: str
    typed_ablation_digest: str
    removal_dependence_digest: str


@dataclass(frozen=True)
class P3OGFormationHistoryPlan:
    """Outcome-free plan fixed through the exact AVAILABLE selection cut."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    formation_contract_digest: str
    selection_source_digest: str
    selection_pool_digest: str
    blind_seed_digest: str
    selection_source_closure_digest: str
    available_capability_digest: str
    preselection_commitments: tuple[FormationHistoryPrecommitment, ...]
    preselection_commitments_digest: str
    lineage_id: str
    scope_digest: str
    graph_rule_id: str
    max_events: int
    max_parents_per_event: int
    max_sources_per_event: int
    max_preselection_commitments: int
    plan_digest: str


@dataclass(frozen=True)
class FormationHistoryEventSourceClosure:
    """Exact closure of the event's declared in-history information sources."""

    plan_digest: str
    event_id: str
    direct_source_event_ids: tuple[str, ...]
    transitive_source_event_ids: tuple[str, ...]
    closure_digest: str


@dataclass(frozen=True)
class FormationHistoryEvent:
    event_id: str
    kind: FormationHistoryEventKind
    parent_ids: tuple[str, ...]
    source_closure: FormationHistoryEventSourceClosure
    logical_time: int
    lineage_id: str
    scope_digest: str
    payload_digest: str
    event_digest: str


@dataclass(frozen=True)
class P3OGFormationHistoryEvidence:
    """Typed DAG preserving one consumed selection and its formation outcome."""

    version: str
    plan_digest: str
    formation_source_digest: str
    formation_evidence_digest: str
    criterion_payload_digest: str | None
    later_result_payload_digest: str | None
    events: tuple[FormationHistoryEvent, ...]
    formation_terminal_event_id: str
    closure_event_id: str | None
    criterion_event_id: str | None
    later_result_event_id: str | None
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
    "semantic-nonderivability-of-criterion-from-blind-seed",
    "process-global-unforgeable-linear-capability",
    "copied-available-value-anti-replay",
    "full-def-og-002-discharge",
    "full-def-og-003-discharge",
    "full-def-og-009-discharge",
    "externally-authenticated-event-source-dependency-completeness",
    "undeclared-or-out-of-band-event-source-dependencies",
    "generic-preselection-commitment-payload-truth",
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
