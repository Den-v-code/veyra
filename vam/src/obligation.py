"""Minimal VAM obligation IR rows for theorem carriers.

The rows in this module serialize theorem obligations for transport and status
inspection.  They do not perform proof checking and never imply an accepted VAM
certificate by themselves.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any, Iterable, Protocol

from .model import Instruction

logger = logging.getLogger(__name__)

OBLIGATION_IR_VERSION = 1
OBLIGATION_OP = "OBLIGATION"
NO_CERTIFICATE_NOTE = "obligation IR is status metadata, not an accepted proof certificate"


class _ObligationLike(Protocol):
    id: str
    theorem: str
    environment: str
    role: str
    category: str
    source: str
    expected_status: str
    actual_status: str
    status: str
    obstruction: str


@dataclass(frozen=True)
class VamObligationRow:
    """Deterministic instruction-like row for one theorem obligation."""

    index: int
    id: str
    theorem: str
    environment: str
    role: str
    category: str
    source: str
    expected_status: str
    actual_status: str
    status: str
    theorem_proof_status: str
    trust_boundary: str
    obstruction: str = ""
    accepted_certificate: bool = False

    @property
    def op(self) -> str:
        """Instruction-like operation name."""
        return OBLIGATION_OP

    @property
    def is_verified(self) -> bool:
        """True only when the carried finite obligation row is verified."""
        return self.status == "verified"

    @property
    def is_open(self) -> bool:
        """True when the obligation still needs work or semantic resolution."""
        return self.status == "open"

    @property
    def is_blocked(self) -> bool:
        """True when the finite obligation has a known blocking obstruction."""
        return self.status == "blocked"

    def as_dict(self) -> dict[str, Any]:
        """Return a stable-key-order JSON-ready mapping."""
        logger.debug("VamObligationRow.as_dict id=%s status=%s", self.id, self.status)
        return {
            "version": OBLIGATION_IR_VERSION,
            "index": self.index,
            "op": self.op,
            "id": self.id,
            "theorem": self.theorem,
            "environment": self.environment,
            "role": self.role,
            "category": self.category,
            "source": self.source,
            "expected_status": self.expected_status,
            "actual_status": self.actual_status,
            "status": self.status,
            "theorem_proof_status": self.theorem_proof_status,
            "trust_boundary": self.trust_boundary,
            "obstruction": self.obstruction,
            "accepted_certificate": self.accepted_certificate,
            "no_overclaim_note": NO_CERTIFICATE_NOTE,
        }

    def as_instruction(self) -> Instruction:
        """Return a compact VAM instruction-like representation."""
        logger.debug("VamObligationRow.as_instruction id=%s", self.id)
        return Instruction(
            self.op,
            (
                self.id,
                self.theorem,
                self.environment,
                self.role,
                self.category,
                self.status,
                self.theorem_proof_status,
            ),
            self.index + 1,
        )


@dataclass(frozen=True)
class VamObligationStatus:
    """Small status summary for a finite obligation IR batch."""

    total: int
    verified: int
    open: int
    blocked: int
    accepted_certificate: bool = False

    @property
    def all_verified(self) -> bool:
        """True when every row is verified and at least one row exists."""
        return self.total > 0 and self.verified == self.total

    def as_dict(self) -> dict[str, Any]:
        """Return a stable-key-order JSON-ready mapping."""
        return {
            "total": self.total,
            "verified": self.verified,
            "open": self.open,
            "blocked": self.blocked,
            "all_verified": self.all_verified,
            "accepted_certificate": self.accepted_certificate,
            "no_overclaim_note": NO_CERTIFICATE_NOTE,
        }


def obligation_rows_from_theorem(record: Any) -> tuple[VamObligationRow, ...]:
    """Convert a VamTheoremRecord-like object into VAM obligation IR rows."""
    logger.debug("obligation_rows_from_theorem entry record=%s", getattr(record, "id", "<unknown>"))
    proof_status = str(getattr(record, "proof_status", "unknown"))
    trust_boundary = str(getattr(record, "trust_boundary", ""))
    result = obligation_rows_from_obligations(
        getattr(record, "obligations", ()),
        theorem_proof_status=proof_status,
        trust_boundary=trust_boundary,
    )
    logger.debug("obligation_rows_from_theorem exit count=%d", len(result))
    return result


def obligation_rows_from_obligations(
    obligations: Iterable[_ObligationLike],
    *,
    theorem_proof_status: str = "unknown",
    trust_boundary: str = "",
) -> tuple[VamObligationRow, ...]:
    """Convert theorem obligation-like objects into deterministic IR rows."""
    rows = tuple(obligations)
    logger.debug("obligation_rows_from_obligations entry count=%d", len(rows))
    result = tuple(
        VamObligationRow(
            index=index,
            id=str(row.id),
            theorem=str(row.theorem),
            environment=str(row.environment),
            role=str(row.role),
            category=str(row.category),
            source=str(row.source),
            expected_status=str(row.expected_status),
            actual_status=str(row.actual_status),
            status=str(row.status),
            theorem_proof_status=theorem_proof_status,
            trust_boundary=trust_boundary,
            obstruction=str(getattr(row, "obstruction", "")),
        )
        for index, row in enumerate(rows)
    )
    logger.debug("obligation_rows_from_obligations exit count=%d", len(result))
    return result


def obligation_instructions(rows: Iterable[VamObligationRow]) -> tuple[Instruction, ...]:
    """Return compact instruction-like rows without proof-certificate meaning."""
    materialized = tuple(rows)
    logger.debug("obligation_instructions entry count=%d", len(materialized))
    return tuple(row.as_instruction() for row in materialized)


def obligation_status(rows: Iterable[VamObligationRow]) -> VamObligationStatus:
    """Summarize visible obligation statuses without accepting proofs."""
    materialized = tuple(rows)
    logger.debug("obligation_status entry count=%d", len(materialized))
    return VamObligationStatus(
        total=len(materialized),
        verified=sum(row.is_verified for row in materialized),
        open=sum(row.is_open for row in materialized),
        blocked=sum(row.is_blocked for row in materialized),
        accepted_certificate=any(row.accepted_certificate for row in materialized),
    )


def obligation_batch_is_transport_only(rows: Iterable[VamObligationRow]) -> bool:
    """Gate batches that are transport-only and carry no accepted certificates."""
    materialized = tuple(rows)
    logger.debug("obligation_batch_is_transport_only entry count=%d", len(materialized))
    return bool(materialized) and not any(row.accepted_certificate for row in materialized)


def obligation_json(rows: Iterable[VamObligationRow]) -> str:
    """Serialize obligation rows deterministically for golden tests/storage."""
    materialized = tuple(rows)
    logger.debug("obligation_json entry count=%d", len(materialized))
    payload = [row.as_dict() for row in materialized]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
