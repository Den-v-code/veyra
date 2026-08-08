"""Hostile-input validation for bounded I1 prefix windows."""

from __future__ import annotations

import logging

from .infinity_prefix_types import PrefixAlphabet, PrefixStage, PrefixTowerWindow

logger = logging.getLogger(__name__)

MAX_PREFIX_DEPTH = 128
MAX_PREFIX_ALPHABET = 64
MAX_PREFIX_SYMBOL_BYTES = 128


class InfinityPrefixValidationError(ValueError):
    """A prefix DTO failed exact finite-shape validation."""


def snapshot_prefix_alphabet(value: PrefixAlphabet) -> PrefixAlphabet:
    """Capture and validate an exact immutable finite alphabet."""
    logger.debug("snapshot_prefix_alphabet entry")
    if type(value) is not PrefixAlphabet:
        logger.error("snapshot_prefix_alphabet invalid container type")
        raise InfinityPrefixValidationError("alphabet must be an exact PrefixAlphabet")
    try:
        symbols = value.symbols
    except AttributeError as exc:
        logger.error("snapshot_prefix_alphabet missing field")
        raise InfinityPrefixValidationError("alphabet is missing required fields") from exc
    if type(symbols) is not tuple or not 1 <= len(symbols) <= MAX_PREFIX_ALPHABET:
        logger.error("snapshot_prefix_alphabet invalid symbol container")
        raise InfinityPrefixValidationError("alphabet symbols must be a bounded nonempty exact tuple")
    captured: list[str] = []
    for symbol in symbols:
        if type(symbol) is not str:
            logger.error("snapshot_prefix_alphabet invalid symbol type")
            raise InfinityPrefixValidationError("alphabet symbols must be exact strings")
        if not symbol or len(symbol) > MAX_PREFIX_SYMBOL_BYTES:
            logger.error("snapshot_prefix_alphabet invalid symbol character bound")
            raise InfinityPrefixValidationError("alphabet symbols must be nonempty and bounded")
        encoded_bytes = len(symbol.encode("utf-8"))
        if encoded_bytes > MAX_PREFIX_SYMBOL_BYTES:
            logger.error("snapshot_prefix_alphabet invalid symbol bytes=%d", encoded_bytes)
            raise InfinityPrefixValidationError("alphabet symbols must be nonempty and bounded")
        captured.append(symbol)
    result = PrefixAlphabet(tuple(captured))
    if len(frozenset(result.symbols)) != len(result.symbols):
        logger.error("snapshot_prefix_alphabet duplicate symbols")
        raise InfinityPrefixValidationError("alphabet symbols must be unique")
    logger.debug("snapshot_prefix_alphabet exit symbols=%d", len(result.symbols))
    return result


def snapshot_prefix_stage(value: PrefixStage, alphabet: PrefixAlphabet) -> PrefixStage:
    """Capture one exact stage without imposing cross-stage coherence."""
    logger.debug("snapshot_prefix_stage entry")
    alphabet = snapshot_prefix_alphabet(alphabet)
    result = snapshot_unbound_prefix_stage(value)
    allowed = frozenset(alphabet.symbols)
    if any(symbol not in allowed for symbol in result.symbols):
        logger.error("snapshot_prefix_stage foreign symbol")
        raise InfinityPrefixValidationError("stage contains a foreign symbol")
    logger.debug("snapshot_prefix_stage exit depth=%d", result.depth)
    return result


def snapshot_unbound_prefix_stage(value: PrefixStage) -> PrefixStage:
    """Capture exact stage structure where no alphabet parameter is available."""
    logger.debug("snapshot_unbound_prefix_stage entry")
    if type(value) is not PrefixStage:
        logger.error("snapshot_unbound_prefix_stage invalid container type")
        raise InfinityPrefixValidationError("stage must be an exact PrefixStage")
    try:
        depth, symbols = value.depth, value.symbols
    except AttributeError as exc:
        logger.error("snapshot_unbound_prefix_stage missing field")
        raise InfinityPrefixValidationError("stage is missing required fields") from exc
    if type(depth) is not int or not 0 <= depth <= MAX_PREFIX_DEPTH:
        logger.error("snapshot_unbound_prefix_stage invalid depth")
        raise InfinityPrefixValidationError("stage depth must be a bounded exact integer")
    if type(symbols) is not tuple or len(symbols) != depth:
        logger.error("snapshot_unbound_prefix_stage invalid length depth=%d", depth)
        raise InfinityPrefixValidationError("stage symbols must be an exact tuple matching its depth")
    captured: list[str] = []
    for symbol in symbols:
        if type(symbol) is not str:
            logger.error("snapshot_unbound_prefix_stage nonexact symbol")
            raise InfinityPrefixValidationError("stage contains a nonexact symbol")
        if not symbol or len(symbol) > MAX_PREFIX_SYMBOL_BYTES:
            logger.error("snapshot_unbound_prefix_stage invalid symbol character bound")
            raise InfinityPrefixValidationError("stage contains an empty or unbounded symbol")
        if len(symbol.encode("utf-8")) > MAX_PREFIX_SYMBOL_BYTES:
            logger.error("snapshot_unbound_prefix_stage unbounded symbol")
            raise InfinityPrefixValidationError("stage contains an empty or unbounded symbol")
        captured.append(symbol)
    result = PrefixStage(depth, tuple(captured))
    logger.debug("snapshot_unbound_prefix_stage exit depth=%d", result.depth)
    return result


def snapshot_prefix_window(value: PrefixTowerWindow) -> PrefixTowerWindow:
    """Deep-capture a structurally valid finite candidate window."""
    logger.debug("snapshot_prefix_window entry")
    if type(value) is not PrefixTowerWindow:
        logger.error("snapshot_prefix_window invalid container type")
        raise InfinityPrefixValidationError("window must be an exact PrefixTowerWindow")
    try:
        source_alphabet, source_stages = value.alphabet, value.stages
    except AttributeError as exc:
        logger.error("snapshot_prefix_window missing field")
        raise InfinityPrefixValidationError("window is missing required fields") from exc
    alphabet = snapshot_prefix_alphabet(source_alphabet)
    if type(source_stages) is not tuple or not 1 <= len(source_stages) <= MAX_PREFIX_DEPTH + 1:
        logger.error("snapshot_prefix_window invalid stages container")
        raise InfinityPrefixValidationError("window stages must be a bounded nonempty exact tuple")
    stages = tuple(snapshot_prefix_stage(stage, alphabet) for stage in source_stages)
    if tuple(stage.depth for stage in stages) != tuple(range(len(stages))):
        logger.error("snapshot_prefix_window noncontiguous depths")
        raise InfinityPrefixValidationError("window stages must cover each depth from zero")
    result = PrefixTowerWindow(alphabet, stages)
    logger.debug("snapshot_prefix_window exit depth=%d", len(stages) - 1)
    return result
