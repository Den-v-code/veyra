"""Immutable protocol types for bounded observer synthesis."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

Canonical = str | int | float | bool | None | tuple["Canonical", ...]


@dataclass(frozen=True)
class ObserverPrimitive:
    name: str
    input_kind: str
    output_kind: str
    cost: int
    evaluator: Callable[[object], object]
    semantic_id: str = ""


@dataclass(frozen=True)
class ObserverTerm:
    op: str
    output_kind: str
    primitive: str = ""
    children: tuple["ObserverTerm", ...] = ()


@dataclass(frozen=True)
class ObserverGrammar:
    grammar_id: str
    input_kind: str
    accepted_output_kinds: tuple[str, ...]
    primitives: tuple[ObserverPrimitive, ...]
    max_depth: int
    max_cost: int


@dataclass(frozen=True)
class ObserverResponse:
    status: str
    value: Canonical = None
    obstruction: str = ""
    trace: tuple[str, ...] = ()


@dataclass(frozen=True)
class ObserverCase:
    case_id: str
    group_id: str
    left: object
    right: object
    expected: str
    expected_obstruction: str = ""
    payload_key: str = ""


@dataclass(frozen=True)
class SynthesisConfig:
    min_train_fit: float = 1.0
    min_holdout_fit: float = 1.0
    complexity_penalty: float = 0.01
    determinism_checks: int = 2


@dataclass(frozen=True)
class ObserverCaseEvidence:
    case_id: str
    passed: bool
    left_status: str
    right_status: str
    left_value: Canonical
    right_value: Canonical
    reason: str


@dataclass(frozen=True)
class CandidateEvaluation:
    term: ObserverTerm
    fingerprint: str
    passed: int
    total: int
    fit: float
    obstruction_rate: float
    complexity: int
    objective: float
    evidence: tuple[ObserverCaseEvidence, ...]


@dataclass(frozen=True)
class NamedBaseline:
    name: str
    observer_class: str
    term: ObserverTerm
    boundary: str


@dataclass(frozen=True)
class SynthesisObstruction:
    reason: str
    detail: str


@dataclass(frozen=True)
class FittedObserver:
    grammar_id: str
    protocol_digest: str
    evaluation_digest: str
    runtime_evaluator_ids: tuple[int, ...]
    train_payload_digests: tuple[str, ...]
    winner: CandidateEvaluation | None
    alternatives: tuple[CandidateEvaluation, ...]
    status: str
    train_case_ids: tuple[str, ...]
    train_group_ids: tuple[str, ...]
    obstructions: tuple[SynthesisObstruction, ...] = ()


@dataclass(frozen=True)
class HoldoutReport:
    fit_digest: str
    holdout_digest: str
    winner_evaluation: CandidateEvaluation | None
    baseline_evaluations: tuple[CandidateEvaluation, ...]
    status: str
    witnesses: tuple[ObserverCaseEvidence, ...]
    obstructions: tuple[SynthesisObstruction, ...] = ()


@dataclass(frozen=True)
class ObserverSynthesisResult:
    fitted: FittedObserver
    holdout: HoldoutReport
    status: str
    boundary: str
