"""Finite, transport-only proof-object rows for VAM.

This module is deliberately separate from theorem and shell lowering.  It folds
already-finite carrier rows into explicit proof-object-shaped data, but it does
not invoke a proof assistant and never accepts a VAM certificate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
from typing import Any, Iterable, Mapping

logger = logging.getLogger(__name__)

STATUS_VERIFIED = "verified"
STATUS_BLOCKED = "blocked"
STATUS_OPEN = "open"
PROOF_OBJECT_STATUSES = frozenset({STATUS_VERIFIED, STATUS_BLOCKED, STATUS_OPEN})
NO_OVERCLAIM_BOUNDARY = (
    "finite VAM proof-object row only; not proof-assistant proof; "
    "not an accepted VAM certificate"
)


@dataclass(frozen=True)
class ProofBoundary:
    """Human-readable boundary for transport-only proof objects."""

    source: str = "vam.finite_transport"
    detail: str = NO_OVERCLAIM_BOUNDARY
    certificate_claim_rejected: bool = False

    def as_string(self) -> str:
        """Return a deterministic no-overclaim boundary string."""
        logger.debug("ProofBoundary.as_string source=%s rejected=%s", self.source, self.certificate_claim_rejected)
        suffix = "external certificate claim rejected" if self.certificate_claim_rejected else "no certificate claim accepted"
        return f"{self.source}: {self.detail}; {suffix}"

    def as_dict(self) -> dict[str, Any]:
        """Return a stable mapping without raw rejected claim text."""
        logger.debug("ProofBoundary.as_dict source=%s", self.source)
        return {
            "source": self.source,
            "detail": self.detail,
            "certificate_claim_rejected": self.certificate_claim_rejected,
            "boundary": self.as_string(),
        }


@dataclass(frozen=True)
class ProofAtom:
    """One finite theorem/shell case represented as a non-PA proof-object row."""

    id: str
    source: str
    kind: str
    status: str
    obstruction: str = ""
    boundary: ProofBoundary = field(default_factory=ProofBoundary)
    payload: Mapping[str, Any] = field(default_factory=dict)
    certificate_claim: str | None = None

    def __post_init__(self) -> None:
        """Normalize visible row status and mark rejected certificate claims."""
        logger.debug("ProofAtom.__post_init__ id=%s status=%s", self.id, self.status)
        rejected = self.certificate_claim is not None or self.boundary.certificate_claim_rejected
        boundary = ProofBoundary(self.boundary.source, self.boundary.detail, rejected)
        object.__setattr__(self, "id", str(self.id))
        object.__setattr__(self, "source", str(self.source))
        object.__setattr__(self, "kind", str(self.kind))
        object.__setattr__(self, "obstruction", str(self.obstruction))
        object.__setattr__(self, "boundary", boundary)
        object.__setattr__(self, "status", normalize_status(self.status, self.obstruction, rejected))

    @property
    def accepted_certificate(self) -> bool:
        """VAM proof objects are status rows only, never accepted certificates."""
        logger.debug("ProofAtom.accepted_certificate id=%s", self.id)
        return False

    def as_dict(self) -> dict[str, Any]:
        """Return stable-key row data suitable for tests and audit output."""
        logger.debug("ProofAtom.as_dict id=%s status=%s", self.id, self.status)
        return {
            "id": self.id,
            "source": self.source,
            "kind": self.kind,
            "status": self.status,
            "obstruction": self.obstruction,
            "boundary": self.boundary.as_string(),
            "certificate_claim_rejected": self.boundary.certificate_claim_rejected,
            "accepted_certificate": self.accepted_certificate,
            "payload": _stable_payload(self.payload),
        }


@dataclass(frozen=True)
class ProofConjunction:
    """Finite conjunction of proof atoms with deterministic status folding."""

    id: str
    children: tuple[ProofAtom, ...]
    source: str = "finite conjunction"
    boundary: ProofBoundary = field(default_factory=ProofBoundary)

    @property
    def status(self) -> str:
        """Fold child statuses: blocked dominates, then all-verified, else open."""
        logger.debug("ProofConjunction.status id=%s children=%d", self.id, len(self.children))
        return fold_status(child.status for child in self.children)

    @property
    def accepted_certificate(self) -> bool:
        """Conjunctions also never accept proof/certificate evidence."""
        logger.debug("ProofConjunction.accepted_certificate id=%s", self.id)
        return False

    def as_dict(self) -> dict[str, Any]:
        """Return stable conjunction data with explicit boundary notes."""
        logger.debug("ProofConjunction.as_dict id=%s status=%s", self.id, self.status)
        return {
            "id": self.id,
            "source": self.source,
            "status": self.status,
            "boundary": self.boundary.as_string(),
            "certificate_claim_rejected": self.boundary.certificate_claim_rejected,
            "accepted_certificate": self.accepted_certificate,
            "children": tuple(child.as_dict() for child in self.children),
        }


def normalize_status(status: object, obstruction: object = "", certificate_claim_rejected: bool = False) -> str:
    """Map carrier status vocabulary into verified/blocked/open deterministically."""
    raw = str(status or "").strip().lower()
    blocked_hint = bool(str(obstruction or "").strip()) or certificate_claim_rejected
    logger.debug("normalize_status raw=%s blocked_hint=%s", raw, blocked_hint)
    if certificate_claim_rejected:
        return STATUS_BLOCKED
    if raw in {"verified", "ready", "transported", "ok", "passed"} and not blocked_hint:
        return STATUS_VERIFIED
    if raw in {"blocked", "failed", "failure", "unsupported", "error", "rejected"}:
        return STATUS_BLOCKED
    if raw == "unknown" and blocked_hint:
        return STATUS_BLOCKED
    return STATUS_OPEN


def fold_status(statuses: Iterable[object]) -> str:
    """Fold finite child statuses with no empty-conjunction overclaim."""
    normalized = tuple(normalize_status(status) for status in statuses)
    logger.debug("fold_status statuses=%s", normalized)
    if any(status == STATUS_BLOCKED for status in normalized):
        return STATUS_BLOCKED
    if normalized and all(status == STATUS_VERIFIED for status in normalized):
        return STATUS_VERIFIED
    return STATUS_OPEN


def proof_atom_from_case(case: Any, *, index: int = 0, boundary: ProofBoundary | None = None) -> ProofAtom:
    """Build a proof atom from a VamFiniteTheoremCase-like dict/object."""
    logger.debug("proof_atom_from_case entry index=%d", index)
    row_id = _field(case, "id", f"finite-case:{index}")
    result = ProofAtom(
        id=row_id,
        source=_field(case, "source", _field(case, "environment", row_id)),
        kind="finite_theorem_case",
        status=_field(case, "status", STATUS_OPEN),
        obstruction=_field(case, "obstruction", ""),
        boundary=boundary or ProofBoundary("vam.theorem.finite_case"),
        payload={"environment": _field(case, "environment", ""), "index": index},
    )
    logger.debug("proof_atom_from_case exit id=%s status=%s", result.id, result.status)
    return result


def proof_conjunction_from_cases(cases: Iterable[Any], *, id: str = "theorem-cases", source: str = "finite theorem cases") -> ProofConjunction:
    """Wrap finite theorem cases in a conjunction proof object."""
    materialized = tuple(cases)
    logger.debug("proof_conjunction_from_cases entry count=%d", len(materialized))
    boundary = ProofBoundary("vam.theorem.finite_cases")
    children = tuple(proof_atom_from_case(case, index=index, boundary=boundary) for index, case in enumerate(materialized))
    result = ProofConjunction(id, children, source, boundary)
    logger.debug("proof_conjunction_from_cases exit status=%s", result.status)
    return result


def proof_atom_from_shell_row(row: Any, *, index: int = 0, boundary: ProofBoundary | None = None, certificate_claim: str | None = None) -> ProofAtom:
    """Build a proof atom from a shell-carrier child row dict/object."""
    logger.debug("proof_atom_from_shell_row entry index=%d", index)
    obstruction = _field(row, "obstruction", "") or _field(row, "obstruction_register", "") or ""
    source = _field(row, "source", f"shell-row:{index}")
    result = ProofAtom(
        id=_field(row, "id", f"shell-row:{index}"),
        source=source,
        kind="finite_shell_child",
        status=_field(row, "status", STATUS_OPEN),
        obstruction=obstruction,
        boundary=boundary or ProofBoundary("vam.shell.carrier"),
        payload={"register": _field(row, "register", ""), "index": index},
        certificate_claim=certificate_claim,
    )
    logger.debug("proof_atom_from_shell_row exit id=%s status=%s", result.id, result.status)
    return result


def proof_conjunction_from_shell_carrier(carrier: Any, *, id: str = "shell-carrier") -> ProofConjunction:
    """Wrap shell carrier rows into a transport-only proof conjunction."""
    rows = tuple(_field(carrier, "rows", ()))
    claim = _field(carrier, "certificate_claim", None)
    shell_boundary = str(_field(carrier, "boundary", "finite shell carrier"))
    logger.debug("proof_conjunction_from_shell_carrier entry rows=%d claim=%s", len(rows), claim is not None)
    boundary = ProofBoundary("vam.shell.carrier", f"{NO_OVERCLAIM_BOUNDARY}; shell boundary: {shell_boundary}", claim is not None)
    if rows:
        children = tuple(proof_atom_from_shell_row(row, index=index, boundary=boundary, certificate_claim=claim) for index, row in enumerate(rows))
    else:
        children = (ProofAtom(id=f"{id}:status", source=_field(carrier, "source", id), kind="finite_shell_carrier", status=_field(carrier, "status", STATUS_OPEN), boundary=boundary, certificate_claim=claim),)
    result = ProofConjunction(id, children, _field(carrier, "source", "finite shell carrier"), boundary)
    logger.debug("proof_conjunction_from_shell_carrier exit status=%s", result.status)
    return result


def proof_object_json(obj: ProofAtom | ProofConjunction) -> str:
    """Serialize proof-object data deterministically."""
    logger.debug("proof_object_json type=%s", type(obj).__name__)
    return json.dumps(obj.as_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _field(obj: Any, key: str, default: Any = None) -> Any:
    """Read key from either a mapping or an attribute-bearing object."""
    logger.debug("_field key=%s type=%s", key, type(obj).__name__)
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _stable_payload(payload: Mapping[str, Any]) -> dict[str, str]:
    """Return deterministic stringified payload values."""
    logger.debug("_stable_payload keys=%d", len(payload))
    return {str(key): str(payload[key]) for key in sorted(payload, key=str)}
