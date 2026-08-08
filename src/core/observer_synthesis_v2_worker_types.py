"""Frozen public contracts for the isolated R14.2b synthesis worker."""
from __future__ import annotations

from dataclasses import dataclass

from .observer_synthesis_v2_budget import BudgetLimits
from .observer_synthesis_v2_types import SynthesisStatus

WORKER_REQUEST_SCHEMA = "veyra.observer-synthesis-v2.worker-request.r14.2b.v1"
WORKER_RESULT_SCHEMA = "veyra.observer-synthesis-v2.worker-result.r14.2b.v1"


@dataclass(frozen=True, slots=True)
class ObserverWorkerRequestV2:
    """Exact data-only request; it carries no path, command, hook, or env."""

    schema: str
    catalog_digest: str
    corpus_digest: str
    train_case_ids: tuple[int, ...]
    train_case_digests: tuple[str, ...]
    limits: BudgetLimits


@dataclass(frozen=True, slots=True)
class ObserverWorkerResultV2:
    """Parent-owned terminal result with optional validated canonical report."""

    schema: str
    status: SynthesisStatus
    detail: str
    report_canonical: bytes | None
    report_digest: str | None
