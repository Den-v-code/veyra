"""Finite executable prefix coherence for the bounded I1 experiment."""

from __future__ import annotations

import logging

from .infinity_prefix_types import (
    PrefixAlphabet,
    PrefixCoherenceReport,
    PrefixRestrictionObstruction,
    PrefixStage,
    PrefixTowerWindow,
)
from .infinity_prefix_validation import (
    InfinityPrefixValidationError,
    MAX_PREFIX_DEPTH,
    snapshot_prefix_alphabet,
    snapshot_prefix_stage,
    snapshot_unbound_prefix_stage,
    snapshot_prefix_window,
)

logger = logging.getLogger(__name__)


def prefix_alphabet(symbols: tuple[str, ...]) -> PrefixAlphabet:
    """Build an exact bounded prefix alphabet."""
    logger.debug("prefix_alphabet entry")
    result = snapshot_prefix_alphabet(PrefixAlphabet(symbols))
    logger.debug("prefix_alphabet exit symbols=%d", len(result.symbols))
    return result


def prefix_tower_window(
    alphabet: PrefixAlphabet, rows: tuple[tuple[str, ...], ...]
) -> PrefixTowerWindow:
    """Build a structurally valid candidate, including incoherent candidates."""
    logger.debug("prefix_tower_window entry")
    alphabet = snapshot_prefix_alphabet(alphabet)
    if type(rows) is not tuple or not 1 <= len(rows) <= MAX_PREFIX_DEPTH + 1:
        logger.error("prefix_tower_window invalid row container")
        raise InfinityPrefixValidationError("rows must be a bounded nonempty exact tuple")
    stages: list[PrefixStage] = []
    for depth, row in enumerate(rows):
        if type(row) is not tuple:
            logger.error("prefix_tower_window invalid row type depth=%d", depth)
            raise InfinityPrefixValidationError("each prefix row must be an exact tuple")
        stages.append(PrefixStage(depth, row))
    result = snapshot_prefix_window(PrefixTowerWindow(alphabet, tuple(stages)))
    logger.debug("prefix_tower_window exit depth=%d", len(result.stages) - 1)
    return result


def prefix_stage(
    alphabet: PrefixAlphabet, depth: int, symbols: tuple[str, ...]
) -> PrefixStage:
    """Build one canonical finite stage at its explicit observer depth."""
    logger.debug("prefix_stage entry")
    alphabet = snapshot_prefix_alphabet(alphabet)
    if type(depth) is not int:
        logger.error("prefix_stage invalid depth type")
        raise InfinityPrefixValidationError("stage depth must be an exact integer")
    if type(symbols) is not tuple:
        logger.error("prefix_stage invalid symbols container")
        raise InfinityPrefixValidationError("stage symbols must be an exact tuple")
    result = snapshot_prefix_stage(PrefixStage(depth, symbols), alphabet)
    logger.debug("prefix_stage exit depth=%d", result.depth)
    return result


def restrict_prefix(
    stage: PrefixStage, target_depth: int
) -> PrefixStage:
    """Project one finite prefix stage to an explicitly smaller depth."""
    logger.debug("restrict_prefix entry")
    stage = snapshot_unbound_prefix_stage(stage)
    if type(target_depth) is not int or not 0 <= target_depth <= stage.depth:
        logger.error("restrict_prefix invalid target depth")
        raise InfinityPrefixValidationError("restriction depth must be an exact in-range integer")
    result = PrefixStage(target_depth, stage.symbols[:target_depth])
    logger.debug("restrict_prefix exit depth=%d", result.depth)
    return result


def periodic_prefix_window(
    alphabet: PrefixAlphabet, period: tuple[str, ...], depth: int
) -> PrefixTowerWindow:
    """Construct all finite prefixes of one periodic stream through depth."""
    logger.debug("periodic_prefix_window entry")
    alphabet = snapshot_prefix_alphabet(alphabet)
    if type(depth) is not int or not 0 <= depth <= MAX_PREFIX_DEPTH:
        logger.error("periodic_prefix_window invalid depth")
        raise InfinityPrefixValidationError("depth must be a bounded exact integer")
    if type(period) is not tuple or not period:
        logger.error("periodic_prefix_window invalid period container")
        raise InfinityPrefixValidationError("period must be a nonempty exact tuple")
    allowed = frozenset(alphabet.symbols)
    if any(type(symbol) is not str or symbol not in allowed for symbol in period):
        logger.error("periodic_prefix_window foreign or nonexact period symbol")
        raise InfinityPrefixValidationError("period contains a foreign or nonexact symbol")
    stream = tuple(period[index % len(period)] for index in range(depth))
    rows = tuple(stream[:stage_depth] for stage_depth in range(depth + 1))
    result = prefix_tower_window(alphabet, rows)
    logger.debug("periodic_prefix_window exit depth=%d", depth)
    return result


def first_prefix_obstruction(
    window: PrefixTowerWindow,
) -> PrefixRestrictionObstruction | None:
    """Return the first finite restriction conflict, if one is witnessed."""
    logger.debug("first_prefix_obstruction entry")
    window = snapshot_prefix_window(window)
    for upper_depth in range(1, len(window.stages)):
        lower = window.stages[upper_depth - 1]
        upper = window.stages[upper_depth]
        for index, lower_symbol in enumerate(lower.symbols):
            projected_symbol = upper.symbols[index]
            if projected_symbol != lower_symbol:
                result = PrefixRestrictionObstruction(
                    lower.depth, upper.depth, index, lower_symbol, projected_symbol
                )
                logger.debug("first_prefix_obstruction exit result=%r", result)
                return result
    logger.debug("first_prefix_obstruction exit result=None")
    return None


def prefix_coherence_report(window: PrefixTowerWindow) -> PrefixCoherenceReport:
    """Report only the declared finite window's restriction coherence."""
    logger.debug("prefix_coherence_report entry")
    window = snapshot_prefix_window(window)
    obstruction = first_prefix_obstruction(window)
    depth = len(window.stages) - 1
    checked_links = depth if obstruction is None else obstruction.upper_depth
    result = PrefixCoherenceReport(
        depth, checked_links, obstruction is None, obstruction
    )
    logger.debug("prefix_coherence_report exit coherent=%s", result.coherent)
    return result
