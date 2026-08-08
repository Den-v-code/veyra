"""Frozen report types for the bounded in-process R14.4 trial core."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .observer_core_types import ObserverExpr
from .observer_synthesis_v2_protocol import ExpectedRelation, SplitId


class TrialSubjectRoleV2(str, Enum):
    """Closed roles in the exact five-subject trial manifest."""

    SYNTHESIZED = "SYNTHESIZED"
    BASELINE = "BASELINE"


@dataclass(frozen=True, slots=True)
class TrialSubjectV2:
    """One predeclared exact R11 AST and its canonical identity."""

    subject_id: str
    role: TrialSubjectRoleV2
    observer: ObserverExpr
    canonical: bytes
    digest: str


@dataclass(frozen=True, slots=True)
class TrialSubjectManifestV2:
    """The exact synthesized subject plus four fixed AST controls."""

    schema: str
    subjects: tuple[TrialSubjectV2, ...]
    manifest_digest: str


@dataclass(frozen=True, slots=True)
class TrialCaseResultV2:
    """One retained exact R11 outcome summary."""

    case_id: int
    case_digest: str
    split: SplitId
    required_for_winner: bool
    expected: ExpectedRelation
    actual: ExpectedRelation
    matched: bool
    outcome_digest: str
    provenance: object = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class TrialSplitSummaryV2:
    """Required and diagnostic counts for one frozen split."""

    split: SplitId
    total: int
    required_total: int
    required_matched: int
    diagnostic_total: int
    diagnostic_matched: int


@dataclass(frozen=True, slots=True)
class TrialAccountingV2:
    """Deterministic retained accounting; wall-clock values are excluded."""

    candidates: int
    canonical_bytes: int
    evaluations: int
    retained_output_bytes: int
    cutoff: bool


@dataclass(frozen=True, slots=True)
class TrialSubjectResultV2:
    """A complete ten-case result produced with a fresh ledger and cache."""

    subject_id: str
    role: TrialSubjectRoleV2
    observer_digest: str
    cases: tuple[TrialCaseResultV2, ...]
    splits: tuple[TrialSplitSummaryV2, ...]
    required_matched: int
    required_total: int
    diagnostic_matched: int
    diagnostic_total: int
    accounting: TrialAccountingV2
    retained_digest: str
    provenance: object = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class BoundedGuaranteeV2:
    """Only finite R14.4 guarantees, with all broad claims explicitly false."""

    catalog_complete: bool
    train_prefix_minimal: bool
    train_matched: int
    train_total: int
    postfit_required_matched: int
    postfit_required_total: int
    all_required_matched: int
    all_required_total: int
    diagnostic_matched: int
    diagnostic_total: int
    resource_path_complete: bool
    general_completeness: bool
    general_minimality: bool
    novelty: bool
    superiority: bool
    evidence_accepted: bool
    promotion_ready: bool
    taxonomy_changed: bool
    proof_complete: bool
    guarantee_digest: str
    boundary: str


@dataclass(frozen=True, slots=True)
class ObserverTrialReportV2:
    """Deterministic bounded trial report, not a subprocess certificate."""

    schema: str
    winner_digest: str
    corpus_digest: str
    manifest_digest: str
    subjects: tuple[TrialSubjectResultV2, ...]
    guarantee: BoundedGuaranteeV2
    report_digest: str
    boundary: str
    provenance: object = field(default=None, compare=False, repr=False)
