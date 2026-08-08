"""Closed data types for the R11 observer/echo core."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .proof_core_types import CoreTerm


class PrimitiveId(str, Enum):
    """The complete, non-extensible R11 primitive set."""

    TAIL = "tail"
    CREST = "crest"


class Mark(Enum):
    """Native two-way recurrence crest, not a Boolean payload."""

    SILENT = "silent"
    PULSE = "pulse"


class LeafKind(str, Enum):
    """Leaf response kinds inferred from observer structure."""

    RECURRENCE = "recurrence"
    MARK = "mark"


@dataclass(frozen=True)
class PairKind:
    """Product response kind."""

    left: "ResponseKind"
    right: "ResponseKind"


ResponseKind: TypeAlias = LeafKind | PairKind


@dataclass(frozen=True)
class Input:
    """The recurrence supplied to an observer."""


@dataclass(frozen=True)
class Apply:
    """Apply one closed primitive to an observer response."""

    primitive: PrimitiveId
    child: "ObserverExpr"


@dataclass(frozen=True)
class Pair:
    """Observe the same recurrence through two branches."""

    left: "ObserverExpr"
    right: "ObserverExpr"


ObserverExpr: TypeAlias = Input | Apply | Pair


@dataclass(frozen=True)
class RecurrenceValue:
    """Branded recurrence response."""

    recurrence: CoreTerm


@dataclass(frozen=True)
class MarkValue:
    """Branded crest response."""

    mark: Mark


@dataclass(frozen=True)
class PairValue:
    """Branded product response."""

    left: "ResponseValue"
    right: "ResponseValue"


ResponseValue: TypeAlias = RecurrenceValue | MarkValue | PairValue


class PathStep(str, Enum):
    """Exact structural path through an observer program."""

    APPLY_TAIL = "apply-tail"
    APPLY_CREST = "apply-crest"
    PAIR_LEFT = "pair-left"
    PAIR_RIGHT = "pair-right"


class ObstructionCode(str, Enum):
    """The complete first-slice obstruction vocabulary."""

    TAIL_OF_SILENCE = "tail-of-silence"


@dataclass(frozen=True)
class ObserverObstruction:
    """A domain obstruction and its outer-to-inner observer path."""

    code: ObstructionCode
    path: tuple[PathStep, ...]


@dataclass(frozen=True)
class Ready:
    """A defined observer response."""

    value: ResponseValue


@dataclass(frozen=True)
class Blocked:
    """One or more deterministic domain obstructions."""

    obstructions: tuple[ObserverObstruction, ...]


Observation: TypeAlias = Ready | Blocked


@dataclass(frozen=True)
class Echo:
    """Two defined observations share this exact native response."""

    value: ResponseValue


@dataclass(frozen=True)
class Mismatch:
    """Both observations are defined but differ."""

    left: ResponseValue
    right: ResponseValue


@dataclass(frozen=True)
class DomainBlocked:
    """At least one side lies outside the observer domain."""

    left_obstructions: tuple[ObserverObstruction, ...]
    right_obstructions: tuple[ObserverObstruction, ...]


EchoOutcome: TypeAlias = Echo | Mismatch | DomainBlocked
