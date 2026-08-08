"""Closed theorem, replay, and post-birth evidence DTOs for isolated P3-N0."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class N0TheoremSource:
    version: str
    artifact_path: str
    artifact_sha256: str
    toolchain_id: str
    theorem_ids: tuple[str, ...]
    axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    source_digest: str


@dataclass(frozen=True)
class N0PhaseReceipt:
    phase_index: int
    artifact_name: str
    captured_sha256: str
    return_code: int
    output_sha256: str
    receipt_digest: str


@dataclass(frozen=True)
class N0FormalAttestation:
    theorem_source_digest: str
    captured_hashes: tuple[str, str, str, str]
    receipts: tuple[N0PhaseReceipt, N0PhaseReceipt, N0PhaseReceipt, N0PhaseReceipt]
    attestation_digest: str


@dataclass(frozen=True)
class N0ReplayEvidence:
    selector: str
    package_digest: str
    network_source_digest: str
    network_judgment_digest: str
    n2_judgment_digest: str
    arrow_judgment_digest: str
    producer_digests: tuple[str, ...]
    outcome_digest: str


@dataclass(frozen=True)
class N0BoundPostbirthLedger:
    row_payloads: tuple[tuple[str, str], tuple[str, str], tuple[str, str]]
    strict_outcome_digest: str
    open_outcome_digest: str
    strict_efficacy_digest: str
    open_efficacy_digest: str
    ledger_digest: str
