"""Frozen request and terminal types for one isolated R14.5 receipt child."""
from __future__ import annotations

from dataclasses import dataclass

from .observer_synthesis_v2_budget import BudgetLimits
from .observer_synthesis_v2_trial_types import ObserverTrialReportV2
from .observer_synthesis_v2_types import SynthesisStatus

RECEIPT_REQUEST_SCHEMA = (
    "veyra.observer-synthesis-v2.receipt-request.r14.5b.v1"
)
RECEIPT_RESULT_SCHEMA = (
    "veyra.observer-synthesis-v2.receipt-result.r14.5b.v1"
)
ISOLATED_RECEIPT_RESULT_SCHEMA = (
    "veyra.observer-synthesis-v2.isolated-receipt-result.r14.5b.v1"
)


@dataclass(frozen=True, slots=True)
class ReceiptWorkerRequestV2:
    """Exact canonical trial plus all roots needed by one fixed child."""

    schema: str
    trial_payload: bytes
    trial_payload_sha256: str
    winner_digest: str
    corpus_digest: str
    manifest_digest: str
    guarantee_digest: str
    trial_report_digest: str
    limits: BudgetLimits
    limits_digest: str


@dataclass(frozen=True, slots=True)
class ValidatedReceiptWorkerRequestV2:
    """Fresh request snapshot with a reconstructed trusted trial report."""

    request: ReceiptWorkerRequestV2
    trial: ObserverTrialReportV2


@dataclass(frozen=True, slots=True)
class ParsedReceiptWorkerResultV2:
    """Strict child terminal envelope; receipt bytes remain opaque to parent."""

    status: SynthesisStatus
    detail: str
    bundle_bytes: bytes | None
    bundle_sha256: str | None
    bundle_digest: str | None


@dataclass(frozen=True, slots=True)
class IsolatedObserverReceiptResultV2:
    """Parent-owned atomic result from exactly one dedicated receipt child."""

    schema: str
    status: SynthesisStatus
    detail: str
    limits_digest: str
    trial_report_digest: str | None
    bundle_bytes: bytes | None
    bundle_sha256: str | None
    bundle_digest: str | None
