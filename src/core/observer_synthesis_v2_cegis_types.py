"""Frozen terminal, trace, and winner types for deterministic R14.3b CEGIS."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .observer_synthesis_v2_budget import BudgetLedgerSnapshot
from .observer_synthesis_v2_types import SynthesisStatus


class CegisEventV2(str, Enum):
    """The complete retained R14.3b trace-event vocabulary."""

    SEED = "SEED"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    WINNER = "WINNER"


class CegisTerminalReasonV2(str, Enum):
    """Coarse terminal classes; deterministic detail carries exact rejection."""

    FOUND = "FOUND"
    COMPLETE_TRAVERSAL = "COMPLETE_TRAVERSAL"
    BUDGET_CUTOFF = "BUDGET_CUTOFF"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True, slots=True)
class CegisTraceStepV2:
    """One output-precharged deterministic trace row."""

    sequence: int
    event: CegisEventV2
    candidate_ordinal: int
    candidate_digest: str
    counterexample_case_id: int | None
    counterexample_case_digest: str | None
    charged_candidates: int
    charged_canonical_bytes: int
    charged_evaluations: int
    limits_digest: str
    canonical: bytes
    step_digest: str


@dataclass(frozen=True, slots=True)
class LockedObserverWinnerV2:
    """The first satisfying catalog row, locked without post-fit reranking."""

    ordinal: int
    cost: int
    depth: int
    canonical: bytes
    digest: str


@dataclass(frozen=True, slots=True)
class ObserverCegisReportV2:
    """One closed report; traversed_candidates counts the terminal scan pass."""

    status: SynthesisStatus
    terminal_reason: CegisTerminalReasonV2
    detail: str
    catalog_digest: str
    training_digest: str
    limits_digest: str
    trace: tuple[CegisTraceStepV2, ...]
    trace_digest: str
    winner: LockedObserverWinnerV2 | None
    traversed_candidates: int
    active_case_ids: tuple[int, ...]
    ledger: BudgetLedgerSnapshot | None
    boundary: str
