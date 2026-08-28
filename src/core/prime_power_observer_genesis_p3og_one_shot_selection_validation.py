"""Fresh validation for bounded P3-OG one-shot selection traces."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_one_shot_selection_runtime import (
    _capability,
    _consume_validated,
)
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


def validate_p3og_selection_capability(
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
    capability: P3OGSelectionCapability,
) -> P3OGSelectionCapability:
    """Accept only one exact AVAILABLE or CONSUMED value from this commitment."""
    _, selection_source = validate_p3og_one_shot_selection_source(
        source,
        selection_source,
    )
    if type(capability) is not P3OGSelectionCapability:
        raise ValueError("p3og-one-shot-selection-capability-type")
    try:
        if type(capability.state) is not SelectionCapabilityState:
            raise ValueError("p3og-one-shot-selection-capability-state")
        expected = _capability(selection_source, capability.state)
        equal = compare_digest(
            canonical_bytes(capability),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-one-shot-selection-capability-malformed") from exc
    if not equal:
        raise ValueError("p3og-one-shot-selection-capability-drift")
    return replace(expected)


def consume_p3og_selection_capability(
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
    capability: P3OGSelectionCapability,
) -> tuple[PrimitiveModeSeed, P3OGSelectionCapability, P3OGOneShotSelectionReceipt]:
    """Validate then consume one bounded AVAILABLE capability trace value."""
    source, selection_source = validate_p3og_one_shot_selection_source(
        source,
        selection_source,
    )
    capability = validate_p3og_selection_capability(
        source,
        selection_source,
        capability,
    )
    return _consume_validated(source, selection_source, capability)


def validate_p3og_one_shot_selection_receipt(
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
    before: P3OGSelectionCapability,
    after: P3OGSelectionCapability,
    receipt: P3OGOneShotSelectionReceipt,
) -> tuple[PrimitiveModeSeed, P3OGSelectionCapability, P3OGOneShotSelectionReceipt]:
    """Freshly reconstruct the exact AVAILABLE -> CONSUMED selection trace."""
    source, selection_source = validate_p3og_one_shot_selection_source(
        source,
        selection_source,
    )
    before = validate_p3og_selection_capability(source, selection_source, before)
    after = validate_p3og_selection_capability(source, selection_source, after)
    if type(receipt) is not P3OGOneShotSelectionReceipt:
        raise ValueError("p3og-one-shot-selection-receipt-type")
    try:
        expected_seed, expected_after, expected_receipt = _consume_validated(
            source,
            selection_source,
            before,
        )
        equal_after = compare_digest(
            canonical_bytes(after),
            canonical_bytes(expected_after),
        )
        equal_receipt = compare_digest(
            canonical_bytes(receipt),
            canonical_bytes(expected_receipt),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-one-shot-selection-receipt-malformed") from exc
    if not equal_after or not equal_receipt:
        raise ValueError("p3og-one-shot-selection-receipt-drift")
    return expected_seed, replace(expected_after), replace(expected_receipt)
