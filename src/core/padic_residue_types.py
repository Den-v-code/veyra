"""Immutable finite DTOs for the classical p-adic shadow in I1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrimeBase:
    """One exact bounded prime used by a residue window."""

    prime: int


@dataclass(frozen=True)
class PadicResidueStage:
    """A canonical residue modulo ``p^(level + 1)``."""

    level: int
    modulus: int
    residue: int


@dataclass(frozen=True)
class PadicResidueWindow:
    """A finite candidate inverse-system window over one prime."""

    prime: PrimeBase
    stages: tuple[PadicResidueStage, ...]


@dataclass(frozen=True)
class PadicCompatibilityObstruction:
    """The first residue that fails to restrict to its predecessor."""

    lower_index: int
    upper_index: int
    expected_residue: int
    projected_residue: int


@dataclass(frozen=True)
class PadicCoherenceReport:
    """Finite compatibility status; it makes no completed-limit claim."""

    prime: int
    depth: int
    checked_links: int
    coherent: bool
    first_obstruction: PadicCompatibilityObstruction | None
    scope: str = "finite-prime-power-window"
