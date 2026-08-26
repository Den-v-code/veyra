"""Bounded AVAILABLE -> CONSUMED runtime for P3-OG one-shot selection."""

from __future__ import annotations

from .prime_power_observer_genesis_p3og_codec import digest
from .prime_power_observer_genesis_p3og_one_shot_selection_source import (
    validate_p3og_one_shot_selection_source,
)
from .prime_power_observer_genesis_p3og_one_shot_selection_types import (
    P3OGOneShotSelectionReceipt,
    P3OGOneShotSelectionSource,
    P3OGSelectionCapability,
    SelectionCapabilityState,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource, PrimitiveModeSeed


def _capability(
    selection_source: P3OGOneShotSelectionSource,
    state: SelectionCapabilityState,
) -> P3OGSelectionCapability:
    """Construct one exact capability value for the committed trace."""
    fields = (
        selection_source.source_digest,
        selection_source.capability_id,
        state,
    )
    return P3OGSelectionCapability(
        *fields,
        digest("one-shot-selection-capability", *fields),
    )


def p3og_initial_selection_capability(
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
) -> P3OGSelectionCapability:
    """Construct the exact AVAILABLE value for one committed selection trace."""
    _, selection_source = validate_p3og_one_shot_selection_source(
        source,
        selection_source,
    )
    return _capability(selection_source, SelectionCapabilityState.AVAILABLE)


def _selected_index(selection_source: P3OGOneShotSelectionSource) -> int:
    """Evaluate the committed Pool x BlindSeed selector without outcome inputs."""
    selector_digest = digest(
        "one-shot-selector",
        selection_source.selector_rule_id,
        selection_source.pool_digest,
        selection_source.blind_seed_digest,
    )
    return int(selector_digest, 16) % selection_source.pool_size


def _consume_validated(
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
    capability: P3OGSelectionCapability,
) -> tuple[PrimitiveModeSeed, P3OGSelectionCapability, P3OGOneShotSelectionReceipt]:
    """Consume one already validated AVAILABLE capability value."""
    if capability.state is not SelectionCapabilityState.AVAILABLE:
        raise ValueError("p3og-one-shot-selection-capability-consumed")
    selected_index = _selected_index(selection_source)
    selected_seed = source.seeds[selected_index]
    after = _capability(selection_source, SelectionCapabilityState.CONSUMED)
    receipt_fields = (
        selection_source.source_digest,
        capability.capability_digest,
        after.capability_digest,
        selected_index,
        selected_seed.label,
        selected_seed.seed_digest,
    )
    receipt = P3OGOneShotSelectionReceipt(
        *receipt_fields,
        digest("one-shot-selection-receipt", *receipt_fields),
    )
    return selected_seed, after, receipt
