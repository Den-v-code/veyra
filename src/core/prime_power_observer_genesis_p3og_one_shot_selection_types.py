"""Closed DTOs for bounded P3-OG blind one-shot selection pressure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
    "transitive-source-closure-blindness",
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
