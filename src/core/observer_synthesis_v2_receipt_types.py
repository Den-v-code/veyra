"""Frozen finite R14.5 receipt wrappers over exact R12 transports."""
from __future__ import annotations

from dataclasses import dataclass

from .intrinsic_vam_lowering_types import TransportedIntrinsicIR
from .observer_synthesis_v2_protocol import ExpectedRelation, SplitId
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope


@dataclass(frozen=True, slots=True)
class ObserverSynthesisReceiptRowV2:
    """One exact corpus case bound to its replayed R11/R12 outcome."""

    ordinal: int
    case_id: int
    group_id: int
    case_digest: str
    case_payload_digest: str
    clone_digest: str
    split: SplitId
    expected: ExpectedRelation
    required_for_winner: bool
    actual: ExpectedRelation
    matched: bool
    outcome_digest: str
    source_digests: tuple[str, str]
    observer_digest: str
    response_kind_digest: str
    r12_payload_digest: str
    ir_digest: str
    r12_binding_digest: str
    envelope_digest: str
    transport: TransportedIntrinsicIR
    row_digest: str


@dataclass(frozen=True, slots=True)
class ObserverSynthesisReceiptBundleV2:
    """The exact ten-row finite receipt bundle; never proof authority."""

    schema: str
    catalog_digest: str
    winner_ordinal: int
    winner_cost: int
    winner_depth: int
    winner_canonical: bytes
    winner_digest: str
    corpus_digest: str
    trial_report_digest: str
    manifest_digest: str
    guarantee_digest: str
    winner_retained_digest: str
    capabilities: tuple[BridgeCapability, ...]
    evidence_class: EvidenceClass
    evidence_scope: EvidenceScope
    taxonomy_counts: tuple[int, int, int, int]
    rows: tuple[ObserverSynthesisReceiptRowV2, ...]
    general_completeness: bool
    general_minimality: bool
    novelty: bool
    superiority: bool
    evidence_accepted: bool
    promotion_ready: bool
    taxonomy_changed: bool
    proof_complete: bool
    boundary: str
    bundle_digest: str
