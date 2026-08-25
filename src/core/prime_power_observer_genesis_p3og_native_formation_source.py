"""Outcome-free source binding for P3-OG native formation pressure v2."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_source import (
    validate_autonomous_tick_source,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_native_formation_codec import (
    native_formation_digest,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_source import (
    _deterministic_select_validated,
)
from .prime_power_observer_genesis_p3og_types import (
    DeterministicSelectionReceipt,
    P3OGSource,
)

SOURCE_VERSION = "p3og-native-formation-source-v2"
FORMATION_STATE_RULE_ID = "operational-q-plus-departure-memory-v1"
FORMATION_RULE_ID = "autonomous-first-return-derives-native-formation-v1"
RESOURCE_RULE_ID = "active-feedback-orbit-period-plus-credit-minus-one-v1"
MAX_FORMATION_TICKS = 126


def p3og_native_formation_source(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
) -> P3OGNativeFormationSource:
    """Bind the exact autonomous law and deterministic selected seed, but no outcome."""
    source, autonomous_source = validate_autonomous_tick_source(source, autonomous_source)
    selection = _deterministic_select_validated(source)
    fields = (
        SOURCE_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        selection,
        selection.selected_seed_digest,
        FORMATION_STATE_RULE_ID,
        FORMATION_RULE_ID,
        RESOURCE_RULE_ID,
        MAX_FORMATION_TICKS,
    )
    return P3OGNativeFormationSource(
        *fields,
        native_formation_digest("native-formation-source", *fields),
    )


def validate_native_formation_source(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_source: P3OGNativeFormationSource,
) -> tuple[P3OGSource, P3OGAutonomousTickSource, P3OGNativeFormationSource]:
    """Freshly reconstruct the complete outcome-free formation source."""
    source, autonomous_source = validate_autonomous_tick_source(source, autonomous_source)
    if type(formation_source) is not P3OGNativeFormationSource:
        raise ValueError("p3og-native-formation-source-type")
    try:
        # Fail closed before canonical traversal can inspect an attacker-supplied
        # dataclass-like nested selection value.
        if type(formation_source.selection) is not DeterministicSelectionReceipt:
            raise ValueError("p3og-native-formation-source-selection-type")
        expected = p3og_native_formation_source(source, autonomous_source)
        equal = compare_digest(
            canonical_bytes(formation_source),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-native-formation-source-malformed") from exc
    if not equal:
        raise ValueError("p3og-native-formation-source-drift")
    return source, autonomous_source, replace(expected)
