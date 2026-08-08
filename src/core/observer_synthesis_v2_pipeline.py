"""Exactly-five-plus-one isolated aggregate for finite R14 audit evidence."""
from __future__ import annotations

import logging

from .observer_synthesis_v2_baselines import EXPECTED_SUBJECT_MANIFEST_DIGEST
from .observer_synthesis_v2_receipt_worker import (
    EXPECTED_UPSTREAM_TRIAL_LIMITS_DIGEST,
    run_isolated_receipts_v2,
)
from .observer_synthesis_v2_receipt_worker_codec import (
    EXPECTED_BUNDLE_BYTES,
    EXPECTED_BUNDLE_DIGEST,
    EXPECTED_BUNDLE_SHA256,
)
from .observer_synthesis_v2_trial import EXPECTED_GUARANTEE_DIGEST, EXPECTED_TRIAL_REPORT_DIGEST
from .observer_synthesis_v2_trial_worker import run_isolated_locked_trials_v2
from .observer_synthesis_v2_trial_worker_types import IsolatedObserverTrialResultV2
from .observer_synthesis_v2_types import SynthesisStatus
from .observer_synthesis_v2_pipeline_validation import (
    incomplete_or_invalid,
    validate_receipt_terminal,
    validate_trial_terminal,
)
from .observer_synthesis_v2_pipeline_types import (
    OBSERVER_SYNTHESIS_V2_PIPELINE_SCHEMA,
    ObserverSynthesisEvidenceV2,
    ObserverSynthesisPipelineResultV2,
)

logger = logging.getLogger(__name__)

PIPELINE_BOUNDARY = (
    "finite executable audit of five fixed isolated trial subjects and one "
    "fixed isolated receipt child; not a theorem, formal proof, R8 evidence, "
    "general completeness/minimality, novelty, superiority, or promotion"
)


def _terminal(
    status: SynthesisStatus,
    detail: str,
    evidence: ObserverSynthesisEvidenceV2 | None = None,
) -> ObserverSynthesisPipelineResultV2:
    """Build one atomic aggregate terminal with no partial evidence."""
    logger.debug("_terminal entry status=%s detail=%s", status.value, detail)
    result = ObserverSynthesisPipelineResultV2(
        OBSERVER_SYNTHESIS_V2_PIPELINE_SCHEMA,
        status,
        detail,
        evidence,
    )
    logger.debug("_terminal exit evidence=%s", evidence is not None)
    return result


def run_observer_synthesis_v2_pipeline() -> ObserverSynthesisPipelineResultV2:
    """Run the approved five trial children, then exactly one receipt child."""
    logger.debug("run_observer_synthesis_v2_pipeline entry")
    try:
        trial_value = run_isolated_locked_trials_v2()
    except (
        AttributeError, OSError, RecursionError, RuntimeError,
        TypeError, UnicodeError, ValueError,
    ):
        logger.exception("run_observer_synthesis_v2_pipeline trial failed")
        return _terminal(SynthesisStatus.INVALID, "aggregate-trial-invalid")
    trial = validate_trial_terminal(trial_value)
    if trial is None:
        status = incomplete_or_invalid(trial_value, IsolatedObserverTrialResultV2)
        return _terminal(status, "aggregate-trial-incomplete")
    try:
        receipt_value = run_isolated_receipts_v2(trial)
    except (
        AttributeError, OSError, RecursionError, RuntimeError,
        TypeError, UnicodeError, ValueError,
    ):
        logger.exception("run_observer_synthesis_v2_pipeline receipt failed")
        return _terminal(SynthesisStatus.INVALID, "aggregate-receipt-invalid")
    if not validate_receipt_terminal(receipt_value):
        from .observer_synthesis_v2_receipt_worker_types import IsolatedObserverReceiptResultV2
        status = incomplete_or_invalid(receipt_value, IsolatedObserverReceiptResultV2)
        return _terminal(status, "aggregate-receipt-incomplete")
    evidence = ObserverSynthesisEvidenceV2(
        EXPECTED_TRIAL_REPORT_DIGEST,
        EXPECTED_SUBJECT_MANIFEST_DIGEST,
        EXPECTED_GUARANTEE_DIGEST,
        EXPECTED_UPSTREAM_TRIAL_LIMITS_DIGEST,
        EXPECTED_UPSTREAM_TRIAL_LIMITS_DIGEST,
        EXPECTED_BUNDLE_BYTES,
        EXPECTED_BUNDLE_SHA256,
        EXPECTED_BUNDLE_DIGEST,
        5,
        10,
        8,
        8,
        0,
        2,
        10,
        (2, 4, 25, 5),
        36,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        PIPELINE_BOUNDARY,
    )
    result = _terminal(
        SynthesisStatus.FOUND,
        "observer-synthesis-v2-aggregate-complete",
        evidence,
    )
    logger.debug("run_observer_synthesis_v2_pipeline exit")
    return result
