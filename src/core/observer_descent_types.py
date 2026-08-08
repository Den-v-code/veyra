"""Typed finite objects for Veyra observer-descent calculus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

State = Hashable
Response = Hashable
StatePair = tuple[State, State]


@dataclass(frozen=True, slots=True)
class FiniteObserver:
    """A named total response table on one finite carrier."""

    name: str
    responses: tuple[tuple[State, Response], ...]
    cost: int


@dataclass(frozen=True, slots=True)
class FiniteObserverDoctrine:
    """A finite admitted observer join-semilattice."""

    name: str
    carrier: tuple[State, ...]
    observers: tuple[FiniteObserver, ...]


@dataclass(frozen=True, slots=True)
class FiniteTransition:
    """A total finite transformation encoded without dynamic callables."""

    name: str
    source: tuple[State, ...]
    target: tuple[State, ...]
    graph: tuple[tuple[State, State], ...]


@dataclass(frozen=True, slots=True)
class ObserverDescent:
    """Unique greatest admitted observer below one exact pullback."""

    transition: str
    target_observer: str
    descended_observer: str
    raw_distinctions: frozenset[StatePair]
    admitted_distinctions: frozenset[StatePair]
    residual: frozenset[StatePair]


@dataclass(frozen=True, slots=True)
class ResidualChainBalance:
    """Two exact decompositions of one compositional distinction debt."""

    first_transition: str
    second_transition: str
    target_observer: str
    pulled_second_residual: frozenset[StatePair]
    first_residual: frozenset[StatePair]
    composite_residual: frozenset[StatePair]
    synergy: frozenset[StatePair]
    balanced: bool


@dataclass(frozen=True, slots=True)
class CrestTact:
    """Minimal observer distinctions retained for one path tact."""

    source: State
    target: State
    crest: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CrestBraid:
    """Ordered finite crest history, including an endpoint receipt."""

    doctrine: str
    tacts: tuple[CrestTact, ...]
    endpoint_crest: tuple[str, ...]
    closed: bool
