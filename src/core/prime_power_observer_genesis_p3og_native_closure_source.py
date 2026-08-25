"""Outcome-free source binding for bounded P3-OG native-state closure pressure."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_native_closure_codec import (
    native_closure_digest,
)
from .prime_power_observer_genesis_p3og_native_closure_types import (
    P3OGNativeClosureSource,
)
from .prime_power_observer_genesis_p3og_source import (
    _deterministic_select_validated,
    validate_source,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource, TransitionKind

logger = logging.getLogger(__name__)
NATIVE_CLOSURE_SOURCE_VERSION = "p3og-native-closure-source-v1"
TRANSITION_RULE_ID = "fixed-source-bound-advance-probe-v1"
PROJECTION_RULE_ID = "machine-configuration-minus-counter-and-digest-v1"
PROJECTION_EXCLUDED_FIELDS = ("transition_count", "state_digest")
CLOSURE_RULE_ID = "least-return-after-genuine-departure-v1"


def p3og_native_closure_source(source: P3OGSource) -> P3OGNativeClosureSource:
    """Bind one fixed closure probe to the existing deterministic selection."""
    logger.debug("p3og.native_closure.source entry")
    source = validate_source(source)
    selection = _deterministic_select_validated(source)
    selected = source.seeds[selection.selected_index]
    fields = (
        NATIVE_CLOSURE_SOURCE_VERSION,
        source.source_digest,
        selection,
        selected.seed_digest,
        len(selected.cycle) - 1,
        TransitionKind.ADVANCE,
        TRANSITION_RULE_ID,
        PROJECTION_RULE_ID,
        PROJECTION_EXCLUDED_FIELDS,
        CLOSURE_RULE_ID,
    )
    result = P3OGNativeClosureSource(
        *fields,
        native_closure_digest("native-closure-source", *fields),
    )
    logger.debug(
        "p3og.native_closure.source exit source=%s",
        result.source_digest[:12],
    )
    return result


def validate_native_closure_source(
    source: P3OGSource,
    closure_source: P3OGNativeClosureSource,
) -> tuple[P3OGSource, P3OGNativeClosureSource]:
    """Freshly reconstruct the exact fixed-rule closure source."""
    logger.debug("p3og.native_closure.validate_source entry")
    source = validate_source(source)
    if type(closure_source) is not P3OGNativeClosureSource:
        raise ValueError("p3og-native-closure-source-type")
    try:
        expected = p3og_native_closure_source(source)
        equal = compare_digest(
            canonical_bytes(closure_source),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.native_closure.validate_source malformed")
        raise ValueError("p3og-native-closure-source-malformed") from exc
    if not equal:
        raise ValueError("p3og-native-closure-source-drift")
    logger.debug("p3og.native_closure.validate_source exit")
    return source, replace(expected)
