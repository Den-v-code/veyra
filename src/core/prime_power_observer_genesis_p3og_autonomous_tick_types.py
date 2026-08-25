"""Closed DTOs for bounded P3-OG autonomous-tick pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_types import (
    CandidateMachineState,
    DeterministicSelectionReceipt,
    MaintenanceControlState,
    TransitionKind,
    TransitionReceipt,
)


class AutonomousTickStatus(str, Enum):
    """Finite autonomous-tick status; not a formation/role judgment."""

    WITNESSED = "witnessed-autonomous-native-first-closure"
    REFUTED = "refuted-autonomous-native-first-closure"


class MaintenanceCreditClass(str, Enum):
    """Exact partition used by the finite state-feedback program."""

    LOW = "credit-equals-one"
    HIGH = "credit-greater-than-one"


@dataclass(frozen=True)
class AutonomousTickRule:
    """One source-committed state predicate mapped to one native transition."""

    maintenance_control: MaintenanceControlState
    credit_class: MaintenanceCreditClass
    transition_kind: TransitionKind


@dataclass(frozen=True)
class P3OGAutonomousTickSource:
    """Outcome-free source for a state-extensional autonomous transition law."""

    version: str
    pressure_source_digest: str
    rules: tuple[AutonomousTickRule, ...]
    rule_id: str
    projection_rule_id: str
    projection_excluded_fields: tuple[str, ...]
    closure_rule_id: str
    source_digest: str


@dataclass(frozen=True)
class AutonomousTickReceipt:
    """One state-selected native transition with no caller-supplied kind."""

    selected_kind: TransitionKind
    before_state_digest: str
    transition: TransitionReceipt
    after_state_digest: str
    before_projection_digest: str
    after_projection_digest: str
    receipt_digest: str


@dataclass(frozen=True)
class P3OGAutonomousFirstClosureEvidence:
    """Replay-derived first-return pressure under one autonomous tick law."""

    version: str
    autonomous_source_digest: str
    selection: DeterministicSelectionReceipt
    selected_seed_digest: str
    initial_state: CandidateMachineState
    ticks: tuple[AutonomousTickReceipt, ...]
    final_state: CandidateMachineState
    state_space_bound: int
    first_closure_step: int | None
    status: AutonomousTickStatus
    reason: str
    genealogy_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_AUTONOMOUS_TICK_NONCLAIMS = (
    "historical-code-commitment-or-chronology",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "full-def-og-001-discharge",
    "full-def-og-003-discharge",
    "primitive-rez-nod-tact-breath-genealogy",
    "operational-alive-is-not-formation-boundary",
    "historical-formation-or-history-dag",
    "exact-n1-n2-p3t-arithmetic-bridge",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "typed-post-formation-ablation",
    "same-token-causal-efficacy",
    "n0-or-hap-lift",
    "formal-theorem-or-certificate",
    "physical-birth-or-consciousness",
    "absolute-observerhood-or-object-adoption",
    "prime-power-carrier-or-completed-infinity",
    "promotion",
)
