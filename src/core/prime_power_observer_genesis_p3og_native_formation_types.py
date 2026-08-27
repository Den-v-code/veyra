"""Closed DTOs for authority-free P3-OG native formation pressure v3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    AutonomousTickReceipt,
)
from .prime_power_observer_genesis_p3og_one_shot_selection_types import (
    P3OGOneShotSelectionReceipt,
    P3OGOneShotSelectionSource,
    P3OGSelectionCapability,
)
from .prime_power_observer_genesis_p3og_types import (
    CandidateMachineState,
)


class NativeFormationBoundary(str, Enum):
    """Boundary of the derived formation machine, not the operational machine."""

    UNFORMED = "unformed"
    ALIVE = "alive"


class NativeFormationStatus(str, Enum):
    """Finite native-formation status; not an observer-role judgment."""

    WITNESSED = "witnessed-native-formation-first-closure"
    REFUTED = "refuted-native-formation-first-closure"


@dataclass(frozen=True)
class P3OGNativeFormationSource:
    """Bind formation to one validated bounded one-shot selection trace."""

    version: str
    pressure_source_digest: str
    autonomous_source_digest: str
    selection_source: P3OGOneShotSelectionSource
    selection_before: P3OGSelectionCapability
    selection_after: P3OGSelectionCapability
    selection: P3OGOneShotSelectionReceipt
    selected_seed_digest: str
    formation_state_rule_id: str
    formation_rule_id: str
    resource_rule_id: str
    max_formation_ticks: int
    source_digest: str


@dataclass(frozen=True)
class NativeFormationState:
    """State of Q_form = operational Q plus native departure memory."""

    run_id: str
    formation_source_digest: str
    selected_seed_digest: str
    boundary: NativeFormationBoundary
    departed: bool
    native_state: CandidateMachineState
    tick_count: int
    state_digest: str


@dataclass(frozen=True)
class NativeFormationTickReceipt:
    """One native formation tick backed by one autonomous operational tick."""

    tick_index: int
    before_state_digest: str
    autonomous_tick: AutonomousTickReceipt
    after_state_digest: str
    became_departed: bool
    became_alive: bool
    receipt_digest: str


@dataclass(frozen=True)
class P3OGNativeFormationEvidence:
    """Replay-derived authority-free native first-closure evidence."""

    version: str
    formation_source_digest: str
    initial_state: NativeFormationState
    ticks: tuple[NativeFormationTickReceipt, ...]
    final_state: NativeFormationState
    state_space_bound: int
    first_closure_step: int | None
    status: NativeFormationStatus
    reason: str
    genealogy_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_NATIVE_FORMATION_NONCLAIMS = (
    "historical-code-commitment-or-chronology",
    "externally-authenticated-criterion-blind-selection",
    "process-global-unforgeable-linear-capability",
    "copied-available-value-anti-replay",
    "typed-history-dag-or-full-def-og-003",
    "full-def-og-001-discharge",
    "primitive-rez-nod-tact-breath-genealogy",
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
