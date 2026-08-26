"""Outcome-free source binding for bounded P3-OG blind one-shot selection."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_codec import canonical_bytes, digest
from .prime_power_observer_genesis_p3og_one_shot_selection_types import (
    P3OGOneShotSelectionSource,
)
from .prime_power_observer_genesis_p3og_source import validate_source
from .prime_power_observer_genesis_p3og_types import P3OGSource

ONE_SHOT_SELECTION_SOURCE_VERSION = "p3og-one-shot-selection-source-v1"
ONE_SHOT_SELECTOR_RULE_ID = "blind-pool-seed-mod-v1"
ONE_SHOT_CAPABILITY_RULE_ID = "available-to-consumed-no-return-v1"
_HEX = frozenset("0123456789abcdef")


def _require_digest(value: str, code: str) -> str:
    """Require one canonical lower-case SHA-256 hex digest."""
    if type(value) is not str or len(value) != 64 or any(char not in _HEX for char in value):
        raise ValueError(code)
    return value


def _pool_digest(source: P3OGSource) -> str:
    """Bind the exact canonical ordered candidate pool."""
    return digest("pool", tuple(seed.seed_digest for seed in source.seeds))


def p3og_one_shot_selection_source(
    source: P3OGSource,
    blind_seed_digest: str,
) -> P3OGOneShotSelectionSource:
    """Commit Pool, BlindSeed, selector law, and one bounded capability identity."""
    source = validate_source(source)
    blind_seed_digest = _require_digest(
        blind_seed_digest,
        "p3og-one-shot-selection-blind-seed-digest",
    )
    pool_digest = _pool_digest(source)
    capability_id = digest(
        "one-shot-selection-capability-id",
        source.source_digest,
        pool_digest,
        blind_seed_digest,
        ONE_SHOT_SELECTOR_RULE_ID,
        ONE_SHOT_CAPABILITY_RULE_ID,
    )
    fields = (
        ONE_SHOT_SELECTION_SOURCE_VERSION,
        source.source_digest,
        pool_digest,
        len(source.seeds),
        blind_seed_digest,
        ONE_SHOT_SELECTOR_RULE_ID,
        ONE_SHOT_CAPABILITY_RULE_ID,
        capability_id,
    )
    return P3OGOneShotSelectionSource(
        *fields,
        digest("one-shot-selection-source", *fields),
    )


def validate_p3og_one_shot_selection_source(
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
) -> tuple[P3OGSource, P3OGOneShotSelectionSource]:
    """Freshly reconstruct the exact source-bound selection commitment."""
    source = validate_source(source)
    if type(selection_source) is not P3OGOneShotSelectionSource:
        raise ValueError("p3og-one-shot-selection-source-type")
    try:
        expected = p3og_one_shot_selection_source(
            source,
            _require_digest(
                selection_source.blind_seed_digest,
                "p3og-one-shot-selection-blind-seed-digest",
            ),
        )
        equal = compare_digest(
            canonical_bytes(selection_source),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-one-shot-selection-source-malformed") from exc
    if not equal:
        raise ValueError("p3og-one-shot-selection-source-drift")
    return source, replace(expected)
