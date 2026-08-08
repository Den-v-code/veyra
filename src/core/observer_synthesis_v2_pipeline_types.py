"""Atomic aggregate contracts for the finite isolated R14 pipeline."""
from __future__ import annotations

from dataclasses import dataclass

from .observer_synthesis_v2_types import SynthesisStatus

OBSERVER_SYNTHESIS_V2_PIPELINE_SCHEMA = (
    "veyra.observer-synthesis-v2.aggregate.r14.6.v1"
)


@dataclass(frozen=True, slots=True)
class ObserverSynthesisEvidenceV2:
    """Exact finite pins and nonclaims retained only after all six children."""

    trial_report_digest: str
    manifest_digest: str
    guarantee_digest: str
    trial_limits_digest: str
    receipt_limits_digest: str
    receipt_bundle_bytes: int
    receipt_bundle_sha256: str
    receipt_bundle_digest: str
    subjects: int
    cases: int
    required_matched: int
    required_total: int
    diagnostic_matched: int
    diagnostic_total: int
    receipt_rows: int
    taxonomy_counts: tuple[int, int, int, int]
    layers: int
    general_completeness: bool
    general_minimality: bool
    novelty: bool
    superiority: bool
    evidence_accepted: bool
    promotion_ready: bool
    taxonomy_changed: bool
    proof_complete: bool
    boundary: str


@dataclass(frozen=True, slots=True)
class ObserverSynthesisPipelineResultV2:
    """Fail-closed terminal: incomplete runs never expose partial evidence."""

    schema: str
    status: SynthesisStatus
    detail: str
    evidence: ObserverSynthesisEvidenceV2 | None
