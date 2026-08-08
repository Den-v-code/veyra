"""Closed immutable types for bounded R11 observer synthesis v2."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .observer_core_types import ObserverExpr, ResponseKind


class SynthesisStatus(str, Enum):
    """Fail-closed terminal states reserved for the complete v2 protocol."""

    FOUND = "FOUND"
    EXHAUSTED = "EXHAUSTED"
    INCOMPLETE = "INCOMPLETE"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class ObserverGrammarV2:
    """Exact finite grammar limits and reviewed default identities."""

    schema: str
    grammar_id: str
    max_cost: int
    max_depth: int
    candidate_limit: int
    canonical_bytes_limit: int


@dataclass(frozen=True, slots=True)
class ObserverCandidateV2:
    """One typed ordered R11 AST with its canonical identity and rank."""

    observer: ObserverExpr
    response_kind: ResponseKind
    cost: int
    depth: int
    canonical: bytes
    digest: str


@dataclass(frozen=True, slots=True)
class ObserverGrammarStratumV2:
    """All candidates at one exact cost in deterministic byte order."""

    cost: int
    candidates: tuple[ObserverCandidateV2, ...]
    canonical_bytes: int


@dataclass(frozen=True, slots=True)
class ObserverGrammarEnumerationV2:
    """Complete finite DP result; it is not synthesis or theorem evidence."""

    grammar: ObserverGrammarV2
    strata: tuple[ObserverGrammarStratumV2, ...]
    candidates: tuple[ObserverCandidateV2, ...]
    canonical_bytes: int
    max_row_bytes: int
    catalog_digest: str
    complete: bool
    boundary: str
    provenance: object = field(default=None, compare=False, repr=False)
