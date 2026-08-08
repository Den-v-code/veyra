"""Proof-object types for intrinsic recurrence arithmetic."""
from __future__ import annotations

from dataclasses import dataclass

from .native_runtime import Mode, NativeObstruction, Tact


@dataclass(frozen=True)
class DivisionStep:
    """One successful structural removal of a divisor recurrence."""

    before: tuple[Tact, ...]
    after: tuple[Tact, ...]


@dataclass(frozen=True)
class StructuralDivisionProof:
    """Checked quotient/residual decomposition with reconstruction evidence."""

    dividend: Mode
    divisor: Mode
    quotient: Mode
    residual: Mode
    reconstructed: Mode | NativeObstruction
    steps: tuple[DivisionStep, ...]
    status: str
    reconstructs: bool
    obstruction: NativeObstruction | None = None


@dataclass(frozen=True)
class EscapeWitness:
    """Evidence that one factor leaves the unit recurrence as residue."""

    factor: Mode
    division: StructuralDivisionProof
    unit_residual: bool
    blocks_resonance: bool


@dataclass(frozen=True)
class ProductPlusOneObstructionProof:
    """Structural product-plus-one escape evidence for supplied factors."""

    factors: tuple[Mode, ...]
    product: Mode
    candidate: Mode
    witnesses: tuple[EscapeWitness, ...]
    escaped: bool
    status: str
    obstruction: NativeObstruction | None = None
