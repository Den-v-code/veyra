"""Closed DTOs for bounded P3-OG native-state first-closure pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_types import (
    CandidateMachineState,
    DeterministicSelectionReceipt,
    TransitionKind,
    TransitionReceipt,
)


class NativeClosureStatus(str, Enum):
    """Finite native-state closure status; not a formation/role judgment."""

    WITNESSED = "witnessed-native-state-first-closure"
    REFUTED = "refuted-native-state-first-closure"


@dataclass(frozen=True)
class P3OGNativeClosureSource:
    """Outcome-free source for one selected candidate's closure pressure."""

    version: str
    pressure_source_digest: str
    selection: DeterministicSelectionReceipt
    selected_seed_digest: str
    step_bound: int
    transition_kind: TransitionKind
    transition_rule_id: str
    projection_rule_id: str
    projection_excluded_fields: tuple[str, ...]
    closure_rule_id: str
    source_digest: str


@dataclass(frozen=True)
class NativeClosureStepReceipt:
    """One exact native transition plus its declared closure projections."""

    step_index: int
    before_state_digest: str
    transition: TransitionReceipt
    after_state_digest: str
    before_projection_digest: str
    after_projection_digest: str
    became_departed: bool
    became_closed: bool
    receipt_digest: str


@dataclass(frozen=True)
class P3OGNativeFirstClosureEvidence:
    """Replay-derived pressure for first return under one declared state projection."""

    version: str
    native_closure_source_digest: str
    initial_state: CandidateMachineState
    steps: tuple[NativeClosureStepReceipt, ...]
    final_state: CandidateMachineState
    first_closure_step: int | None
    status: NativeClosureStatus
    reason: str
    genealogy_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_NATIVE_CLOSURE_NONCLAIMS = (
    "raw-cycle-v1-promotion",
    "advance-probe-is-not-def-og-001-tick",
    "autonomous-native-tick-not-established",
    "operational-alive-is-not-formation-boundary",
    "full-candidate-machine-state-recurrence",
    "full-operational-machine-equivalence",
    "full-def-og-003-discharge",
    "historical-formation-or-chronology",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "primitive-rez-nod-tact-breath-genealogy",
    "exact-n1-n2-p3t-arithmetic-bridge",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "post-formation-ablation",
    "same-token-causal-efficacy",
    "n0-or-hap-lift",
    "formal-theorem-or-certificate",
    "physical-birth-or-consciousness",
    "absolute-observerhood-or-object-adoption",
    "prime-power-carrier-or-completed-infinity",
    "promotion",
)
