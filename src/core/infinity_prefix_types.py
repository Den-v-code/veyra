"""Immutable finite DTOs for the bounded I1 prefix experiment."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrefixAlphabet:
    """A finite exact alphabet used by prefix observers."""

    symbols: tuple[str, ...]


@dataclass(frozen=True)
class PrefixStage:
    """The declared finite observation at one exact depth."""

    depth: int
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class PrefixTowerWindow:
    """A bounded candidate window; coherence is checked separately."""

    alphabet: PrefixAlphabet
    stages: tuple[PrefixStage, ...]


@dataclass(frozen=True)
class PrefixRestrictionObstruction:
    """The first witnessed failure of a longer prefix to restrict."""

    lower_depth: int
    upper_depth: int
    mismatch_index: int
    lower_symbol: str
    projected_symbol: str


@dataclass(frozen=True)
class PrefixCoherenceReport:
    """Finite-only coherence status for one captured prefix window."""

    maximum_depth: int
    checked_links: int
    coherent: bool
    first_obstruction: PrefixRestrictionObstruction | None
    scope: str = "finite-window"
