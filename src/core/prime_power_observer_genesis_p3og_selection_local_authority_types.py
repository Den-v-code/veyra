"""Immutable DTOs for bounded local P3-OG one-shot selection authority."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class P3OGSelectionLocalAuthorityState(str, Enum):
    """Irreversible states for one protected local selection reservation."""

    RESERVED = "RESERVED"
    CLAIMED = "CLAIMED"
    CONSUMED = "CONSUMED"


P3OG_SELECTION_LOCAL_AUTHORITY_BOUNDARY = (
    "atomic one-shot selection authority only for cooperating processes sharing one "
    "protected local store; no trusted time, remote witness, operator non-bypass, "
    "cross-store uniqueness, or historical occurrence claim"
)


@dataclass(frozen=True, slots=True)
class P3OGSelectionLocalAuthorityReservation:
    """Exact pre-selection commitments for one local one-shot authority slot."""

    reservation_id: str
    pressure_source_digest: str
    selection_source_digest: str
    source_closure_digest: str
    available_capability_digest: str
    capability_id: str


@dataclass(frozen=True, slots=True)
class P3OGSelectionLocalAuthorityReceipt:
    """One hash-chained local authority transition; raw capability is never stored."""

    reservation: P3OGSelectionLocalAuthorityReservation
    state: P3OGSelectionLocalAuthorityState
    capability_digest: str
    attempt_digest: str
    selection_receipt_digest: str
    revision: int
    previous_receipt: str
    boundary: str
    receipt_digest: str


@dataclass(frozen=True, slots=True)
class P3OGSelectionLocalAuthorityEvidence:
    """Immutable chain proving one store-backed claim preceded one selection receipt."""

    reserved: P3OGSelectionLocalAuthorityReceipt
    claimed: P3OGSelectionLocalAuthorityReceipt
    terminal: P3OGSelectionLocalAuthorityReceipt
    selection_receipt_digest: str
    boundary: str
    evidence_digest: str
