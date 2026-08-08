"""Precharged semantic execution confined to the isolated receipt child."""
from __future__ import annotations

from hashlib import sha256
import logging
from typing import Callable

from .observer_synthesis_v2_budget import BudgetLedger, BudgetLimits
from .observer_synthesis_v2_receipt_codec import receipt_bundle_bytes_v2
from .observer_synthesis_v2_receipt_worker_codec import (
    EXPECTED_BUNDLE_BYTES,
    EXPECTED_BUNDLE_DIGEST,
    EXPECTED_BUNDLE_SHA256,
)
from .observer_synthesis_v2_receipt_worker_trial import TRIAL_PAYLOAD_BYTES
from .observer_synthesis_v2_receipt_types import ObserverSynthesisReceiptBundleV2
from .observer_synthesis_v2_receipts import build_receipts_from_validated_trial_v2
from .observer_synthesis_v2_trial_types import ObserverTrialReportV2
from .proof_core_codec import canonical_json, load_canonical

logger = logging.getLogger(__name__)

ReceiptBuilderV2 = Callable[[object], ObserverSynthesisReceiptBundleV2]


def build_precharged_receipt_bytes_v2(
    trial: ObserverTrialReportV2,
    limits: BudgetLimits,
    builder: ReceiptBuilderV2 = build_receipts_from_validated_trial_v2,
) -> bytes:
    """Precharge all retained work, replay, then require the exact bundle."""
    logger.debug("build_precharged_receipt_bytes_v2 entry")
    ledger = BudgetLedger(limits)
    ledger.charge_candidate(TRIAL_PAYLOAD_BYTES + EXPECTED_BUNDLE_BYTES)
    ledger.charge_evaluations(10)
    ledger.charge_output(EXPECTED_BUNDLE_BYTES)
    bundle = builder(trial)
    payload = receipt_bundle_bytes_v2(bundle)
    if (
        len(payload) != EXPECTED_BUNDLE_BYTES
        or sha256(payload).hexdigest() != EXPECTED_BUNDLE_SHA256
    ):
        logger.error("build_precharged_receipt_bytes_v2 byte pin drift")
        raise RuntimeError("r14.5b-receipt-byte-pin-drift")
    try:
        data = load_canonical(payload.decode())
        canonical = canonical_json(data).encode()
    except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("build_precharged_receipt_bytes_v2 invalid canonical")
        raise RuntimeError("r14.5b-receipt-canonical-drift") from exc
    if (
        canonical != payload
        or type(data) is not dict
        or data.get("bundle_digest") != EXPECTED_BUNDLE_DIGEST
    ):
        logger.error("build_precharged_receipt_bytes_v2 binding drift")
        raise RuntimeError("r14.5b-receipt-binding-drift")
    logger.debug("build_precharged_receipt_bytes_v2 exit bytes=%d", len(payload))
    return payload
