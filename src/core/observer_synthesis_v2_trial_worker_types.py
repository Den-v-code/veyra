"""Frozen contracts for isolated per-subject R14.4b execution."""
from __future__ import annotations

from dataclasses import dataclass

from .observer_synthesis_v2_budget import BudgetLimits
from .observer_synthesis_v2_trial_types import (
    ObserverTrialReportV2,
    TrialSubjectResultV2,
    TrialSubjectRoleV2,
)
from .observer_synthesis_v2_types import SynthesisStatus

TRIAL_SUBJECT_REQUEST_SCHEMA = (
    "veyra.observer-synthesis-v2.trial-subject-request.r14.4b.v1"
)
TRIAL_SUBJECT_RESULT_SCHEMA = (
    "veyra.observer-synthesis-v2.trial-subject-result.r14.4b.v1"
)
ISOLATED_TRIAL_RESULT_SCHEMA = (
    "veyra.observer-synthesis-v2.isolated-trial-result.r14.4b.v1"
)


@dataclass(frozen=True, slots=True)
class TrialSubjectWorkerRequestV2:
    """Data-only request bound to one exact predeclared subject."""

    schema: str
    subject_index: int
    subject_id: str
    role: TrialSubjectRoleV2
    observer_digest: str
    winner_digest: str
    corpus_digest: str
    manifest_digest: str
    case_ids: tuple[int, ...]
    case_digests: tuple[str, ...]
    limits: BudgetLimits
    limits_digest: str


@dataclass(frozen=True, slots=True)
class ParsedTrialSubjectResultV2:
    """Strictly validated child terminal result."""

    status: SynthesisStatus
    detail: str
    subject: TrialSubjectResultV2 | None
    subject_payload_digest: str | None


@dataclass(frozen=True, slots=True)
class IsolatedObserverTrialResultV2:
    """Parent-owned atomic outcome; only complete runs retain a report."""

    schema: str
    status: SynthesisStatus
    detail: str
    limits_digest: str
    report: ObserverTrialReportV2 | None
    report_digest: str | None
