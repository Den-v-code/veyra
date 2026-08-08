"""Finite p-adic residue-window logic for the bounded I1 experiment."""

from __future__ import annotations

import logging
from typing import Callable

from .padic_residue_types import (
    PadicCoherenceReport,
    PadicCompatibilityObstruction,
    PadicResidueStage,
    PadicResidueWindow,
    PrimeBase,
)
from .padic_residue_validation import (
    MAX_PADIC_DEPTH,
    PadicResidueValidationError,
    snapshot_padic_window,
    snapshot_padic_stage,
    snapshot_prime_base,
    validate_padic_source_integer,
)

logger = logging.getLogger(__name__)


def prime_base(prime: int) -> PrimeBase:
    """Build one exact bounded prime base."""
    logger.debug("prime_base entry")
    result = snapshot_prime_base(PrimeBase(prime))
    logger.debug("prime_base exit prime=%d", result.prime)
    return result


def padic_residue_window(
    prime: PrimeBase, residues: tuple[int, ...]
) -> PadicResidueWindow:
    """Build a structural candidate, preserving canonical incompatibilities."""
    logger.debug("padic_residue_window entry")
    prime = snapshot_prime_base(prime)
    if type(residues) is not tuple or not 1 <= len(residues) <= MAX_PADIC_DEPTH:
        logger.error("padic_residue_window invalid residues container")
        raise PadicResidueValidationError("residues must be a bounded nonempty exact tuple")
    stages: list[PadicResidueStage] = []
    for level, residue in enumerate(residues):
        if type(residue) is not int:
            logger.error("padic_residue_window nonexact residue level=%d", level)
            raise PadicResidueValidationError("residues must be exact integers")
        modulus = prime.prime ** (level + 1)
        stages.append(PadicResidueStage(level, modulus, residue))
    result = snapshot_padic_window(PadicResidueWindow(prime, tuple(stages)))
    logger.debug("padic_residue_window exit levels=%d", len(result.stages))
    return result


def padic_residue_stage(
    prime: PrimeBase, index: int, residue: int
) -> PadicResidueStage:
    """Build one canonical residue stage at an explicit prime-power level."""
    logger.debug("padic_residue_stage entry")
    prime = snapshot_prime_base(prime)
    if type(index) is not int or not 0 <= index < MAX_PADIC_DEPTH:
        logger.error("padic_residue_stage invalid index")
        raise PadicResidueValidationError("index must be a bounded exact integer")
    if type(residue) is not int:
        logger.error("padic_residue_stage invalid residue type")
        raise PadicResidueValidationError("residue must be an exact integer")
    result = snapshot_padic_stage(
        PadicResidueStage(index, prime.prime ** (index + 1), residue), prime, index
    )
    logger.debug("padic_residue_stage exit level=%d", result.level)
    return result


def project_padic_stage(
    prime: PrimeBase, stage: PadicResidueStage, target_index: int
) -> PadicResidueStage:
    """Project a canonical residue stage to a lower prime-power observer."""
    logger.debug("project_padic_stage entry")
    prime = snapshot_prime_base(prime)
    if type(stage) is not PadicResidueStage:
        logger.error("project_padic_stage invalid stage type")
        raise PadicResidueValidationError("stage must be an exact PadicResidueStage")
    try:
        source_level = stage.level
    except AttributeError as exc:
        logger.error("project_padic_stage missing stage field")
        raise PadicResidueValidationError("stage is missing required fields") from exc
    if type(source_level) is not int:
        logger.error("project_padic_stage invalid source level")
        raise PadicResidueValidationError("stage level must be an exact integer")
    stage = snapshot_padic_stage(stage, prime, source_level)
    if type(target_index) is not int or not 0 <= target_index <= stage.level:
        logger.error("project_padic_stage invalid target index")
        raise PadicResidueValidationError("projection level must be an exact in-range integer")
    modulus = prime.prime ** (target_index + 1)
    result = padic_residue_stage(prime, target_index, stage.residue % modulus)
    logger.debug("project_padic_stage exit level=%d", result.level)
    return result


def integer_padic_window(
    prime: PrimeBase, source: int, depth: int
) -> PadicResidueWindow:
    """Return the finite classical residue shadows of one integer."""
    logger.debug("integer_padic_window entry")
    prime = snapshot_prime_base(prime)
    source = validate_padic_source_integer(source)
    if type(depth) is not int or not 1 <= depth <= MAX_PADIC_DEPTH:
        logger.error("integer_padic_window invalid depth")
        raise PadicResidueValidationError("depth must be a bounded positive exact integer")
    residues = tuple(source % (prime.prime ** (level + 1)) for level in range(depth))
    result = padic_residue_window(prime, residues)
    logger.debug("integer_padic_window exit levels=%d", len(result.stages))
    return result


def first_padic_obstruction(
    window: PadicResidueWindow,
) -> PadicCompatibilityObstruction | None:
    """Return the first failed adjacent residue restriction."""
    logger.debug("first_padic_obstruction entry")
    window = snapshot_padic_window(window)
    for upper_level in range(1, len(window.stages)):
        lower = window.stages[upper_level - 1]
        upper = window.stages[upper_level]
        actual = upper.residue % lower.modulus
        if actual != lower.residue:
            result = PadicCompatibilityObstruction(
                lower.level, upper.level, lower.residue, actual
            )
            logger.debug("first_padic_obstruction exit result=%r", result)
            return result
    logger.debug("first_padic_obstruction exit result=None")
    return None


def padic_coherence_report(window: PadicResidueWindow) -> PadicCoherenceReport:
    """Report compatibility only across the supplied finite residue stages."""
    logger.debug("padic_coherence_report entry")
    window = snapshot_padic_window(window)
    obstruction = first_padic_obstruction(window)
    depth = len(window.stages)
    checked_links = depth - 1 if obstruction is None else obstruction.upper_index
    result = PadicCoherenceReport(
        window.prime.prime, depth, checked_links, obstruction is None, obstruction
    )
    logger.debug("padic_coherence_report exit coherent=%s", result.coherent)
    return result


def add_padic_windows(
    left: PadicResidueWindow, right: PadicResidueWindow
) -> PadicResidueWindow:
    """Add equal coherent finite p-adic windows componentwise."""
    logger.debug("add_padic_windows entry")
    result = _combine_padic_windows(left, right, lambda a, b: a + b, "addition")
    logger.debug("add_padic_windows exit levels=%d", len(result.stages))
    return result


def multiply_padic_windows(
    left: PadicResidueWindow, right: PadicResidueWindow
) -> PadicResidueWindow:
    """Multiply equal coherent finite p-adic windows componentwise."""
    logger.debug("multiply_padic_windows entry")
    result = _combine_padic_windows(left, right, lambda a, b: a * b, "multiplication")
    logger.debug("multiply_padic_windows exit levels=%d", len(result.stages))
    return result


def _combine_padic_windows(
    left: PadicResidueWindow,
    right: PadicResidueWindow,
    operation: Callable[[int, int], int],
    name: str,
) -> PadicResidueWindow:
    logger.debug("_combine_padic_windows entry operation=%s", name)
    left = snapshot_padic_window(left)
    right = snapshot_padic_window(right)
    if left.prime != right.prime or len(left.stages) != len(right.stages):
        logger.error("_combine_padic_windows incompatible shape operation=%s", name)
        raise PadicResidueValidationError("p-adic operations require equal prime and depth")
    if first_padic_obstruction(left) is not None or first_padic_obstruction(right) is not None:
        logger.error("_combine_padic_windows incoherent input operation=%s", name)
        raise PadicResidueValidationError("p-adic operations require coherent input windows")
    residues = tuple(
        operation(a.residue, b.residue) % a.modulus
        for a, b in zip(left.stages, right.stages, strict=True)
    )
    result = padic_residue_window(left.prime, residues)
    if first_padic_obstruction(result) is not None:
        logger.error("_combine_padic_windows internal coherence failure operation=%s", name)
        raise RuntimeError("componentwise p-adic operation broke compatibility")
    logger.debug("_combine_padic_windows exit operation=%s levels=%d", name, len(result.stages))
    return result
