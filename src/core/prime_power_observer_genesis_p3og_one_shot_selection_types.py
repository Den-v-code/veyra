"""Closed DTOs for bounded P3-OG blind one-shot selection pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SelectionDependencyKind(str, Enum):
    """Declared provenance kinds for bounded selection-source closure."""

    PRESSURE_SOURCE = "pressure-source"
    POOL = "pool"
    BLIND_SEED = "blind-seed"
    SELECTOR_LAW = "selector-law"
    TRANSFORM = "transform"
    DISCRIMINATION_CRITERION = "discrimination-criterion"
    TARGET = "target"
    SELECTED_RESPONSE = "selected-response"
    LATER_STATUS = "later-status"
    THEOREM_CONCLUSION = "theorem-conclusion"


@dataclass(frozen=True)
class P3OGSelectionDependencyNode:
    """One declared dependency node; parents are source dependencies."""

    node_id: str
    kind: SelectionDependencyKind
    parent_ids: tuple[str, ...]
    payload_digest: str
    node_digest: str


@dataclass(frozen=True)
class P3OGSelectionSourceClosure:
    """Graph-derived transitive closure for Pool/BlindSeed/SelectorLaw roots."""

    version: str
    pressure_source_digest: str
    nodes: tuple[P3OGSelectionDependencyNode, ...]
    root_ids: tuple[str, ...]
    closure_node_ids: tuple[str, ...]
    forbidden_node_ids: tuple[str, ...]
    closure_digest: str


class SelectionCapabilityState(str, Enum):
    """Replayable capability state for one bounded selection trace."""

    AVAILABLE = "available"
    CONSUMED = "consumed"


@dataclass(frozen=True)
class P3OGOneShotSelectionSource:
    """Outcome-free commitment to Pool x BlindSeed -> CandidateId selection."""

    version: str
    pressure_source_digest: str
    pool_digest: str
    pool_size: int
    blind_seed_digest: str
    selector_rule_id: str
    capability_rule_id: str
    source_closure: P3OGSelectionSourceClosure
    capability_id: str
    source_digest: str


@dataclass(frozen=True)
class P3OGSelectionCapability:
    """One replayable bounded capability value; not process-global authority."""

    selection_source_digest: str
    capability_id: str
    state: SelectionCapabilityState
    capability_digest: str


@dataclass(frozen=True)
class P3OGOneShotSelectionReceipt:
    """Exact AVAILABLE -> CONSUMED selection trace receipt."""

    selection_source_digest: str
    before_capability_digest: str
    after_capability_digest: str
    selected_index: int
    selected_seed_label: str
    selected_seed_digest: str
    receipt_digest: str


P3OG_ONE_SHOT_SELECTION_NONCLAIMS = (
    "full-def-og-002-discharge",
    "historical-strict-past-commitment",
    "undeclared-or-out-of-band-source-dependency-blindness",
    "externally-authenticated-dependency-completeness",
    "process-global-unforgeable-linear-capability",
    "copied-available-value-anti-replay",
    "criterion-or-result-truth",
    "formation-or-first-closure",
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
