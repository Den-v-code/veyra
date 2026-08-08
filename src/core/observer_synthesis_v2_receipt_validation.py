"""Independent rebuild-only validation for finite R14.5 receipt bundles."""
from __future__ import annotations

import logging
from typing import cast

from .intrinsic_vam_values import IntrinsicVamLoweringError
from .observer_synthesis_v2_receipt_codec import (
    InvalidObserverSynthesisReceiptV2,
    receipt_bundle_bytes_v2,
    reject_receipt_v2,
)
from .observer_synthesis_v2_receipt_types import (
    ObserverSynthesisReceiptBundleV2,
)
from .observer_synthesis_v2_receipts import build_observer_synthesis_receipts_v2
from .observer_synthesis_v2_trial_validation import (
    EXPECTED_WINNER_CANONICAL,
    EXPECTED_WINNER_COST,
    EXPECTED_WINNER_DEPTH,
    EXPECTED_WINNER_DIGEST,
    EXPECTED_WINNER_ORDINAL,
)
from .shadow_effect_branding import ShadowEffectError

logger = logging.getLogger(__name__)


def validate_observer_synthesis_receipts_v2(
    bundle: object,
) -> ObserverSynthesisReceiptBundleV2:
    """Rebuild all ten expected rows and return only fresh trusted values."""
    logger.debug(
        "validate_observer_synthesis_receipts_v2 entry type=%s",
        type(bundle).__name__,
    )
    if type(bundle) is not ObserverSynthesisReceiptBundleV2:
        reject_receipt_v2("invalid-receipt-bundle-type")
    trusted = cast(ObserverSynthesisReceiptBundleV2, bundle)
    try:
        winner_binding = (
            trusted.winner_ordinal,
            trusted.winner_cost,
            trusted.winner_depth,
            trusted.winner_canonical,
            trusted.winner_digest,
        )
    except AttributeError:
        reject_receipt_v2("invalid-receipt-bundle")
    if tuple(type(value) for value in winner_binding) != (
        int,
        int,
        int,
        bytes,
        str,
    ):
        reject_receipt_v2("invalid-receipt-winner-fields")
    if winner_binding != (
        EXPECTED_WINNER_ORDINAL,
        EXPECTED_WINNER_COST,
        EXPECTED_WINNER_DEPTH,
        EXPECTED_WINNER_CANONICAL,
        EXPECTED_WINNER_DIGEST,
    ):
        reject_receipt_v2("invalid-receipt-winner-binding")
    expected = build_observer_synthesis_receipts_v2()
    try:
        actual_bytes = receipt_bundle_bytes_v2(bundle)
    except (
        AttributeError,
        InvalidObserverSynthesisReceiptV2,
        IntrinsicVamLoweringError,
        ShadowEffectError,
        TypeError,
        ValueError,
        UnicodeError,
        RecursionError,
    ):
        reject_receipt_v2("invalid-receipt-bundle")
    expected_bytes = receipt_bundle_bytes_v2(expected)
    if actual_bytes != expected_bytes:
        reject_receipt_v2("receipt-bundle-replay-mismatch")
    logger.debug(
        "validate_observer_synthesis_receipts_v2 exit digest=%s",
        expected.bundle_digest[:12],
    )
    return expected
