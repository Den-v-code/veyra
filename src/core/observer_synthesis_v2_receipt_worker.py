"""Parent orchestration for exactly one isolated R14.5 receipt child."""
from __future__ import annotations

from hashlib import sha256
import logging
import os
import subprocess
import time

from .observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetValidationError,
    snapshot_budget_limits,
)
from .observer_synthesis_v2_cegis_codec import limits_digest_v2
from .observer_synthesis_v2_receipt_worker_codec import (
    receipt_request_bytes_v2,
)
from .observer_synthesis_v2_receipt_worker_trial import (
    snapshot_receipt_trial_v2,
    trial_report_payload_v2,
)
from .observer_synthesis_v2_receipt_worker_types import (
    ISOLATED_RECEIPT_RESULT_SCHEMA,
    RECEIPT_REQUEST_SCHEMA,
    IsolatedObserverReceiptResultV2,
    ReceiptWorkerRequestV2,
)
from .observer_synthesis_v2_receipt_worker_validation import (
    parse_receipt_result_payload_v2,
    validate_receipt_request_v2,
)
from .observer_synthesis_v2_trial import (
    EXPECTED_GUARANTEE_DIGEST,
    EXPECTED_TRIAL_REPORT_DIGEST,
)
from .observer_synthesis_v2_trial_worker_types import (
    ISOLATED_TRIAL_RESULT_SCHEMA,
    IsolatedObserverTrialResultV2,
)
from .observer_synthesis_v2_trial_types import ObserverTrialReportV2
from .observer_synthesis_v2_types import SynthesisStatus
from .observer_synthesis_v2_worker_codec import (
    FRAME_BYTES,
    MAX_WORKER_FRAME_BYTES,
    frame_bytes_v2,
)
from .observer_synthesis_v2_worker_runtime import (
    FixedWorkerKindV2,
    apply_verified_limits_v2,
    run_fixed_child_v2,
    unframe_exact_result_v2,
)

logger = logging.getLogger(__name__)

_apply_limits = apply_verified_limits_v2
EXPECTED_UPSTREAM_TRIAL_LIMITS_DIGEST = (
    "7a9511755e8d00c5e91de1bc137b7e310876d06cf8ce8ea08164a588264b07cb"
)


def _terminal(
    status: SynthesisStatus,
    detail: str,
    limits_digest: str,
    trial_report_digest: str | None = None,
    bundle_bytes: bytes | None = None,
    bundle_sha256: str | None = None,
    bundle_digest: str | None = None,
) -> IsolatedObserverReceiptResultV2:
    logger.debug("_terminal entry status=%s detail=%s", status.value, detail)
    result = IsolatedObserverReceiptResultV2(
        ISOLATED_RECEIPT_RESULT_SCHEMA,
        status,
        detail,
        limits_digest,
        trial_report_digest,
        bundle_bytes,
        bundle_sha256,
        bundle_digest,
    )
    logger.debug("_terminal exit")
    return result


def build_receipt_request_v2(
    trial_result: object,
    limits: object = DEFAULT_BUDGET_LIMITS,
) -> ReceiptWorkerRequestV2:
    """Build one request only from a complete independently validated trial."""
    logger.debug("build_receipt_request_v2 entry")
    if type(trial_result) is not IsolatedObserverTrialResultV2:
        raise ValueError("invalid-isolated-trial-result-type")
    try:
        captured = (
            trial_result.schema,
            trial_result.status,
            trial_result.detail,
            trial_result.limits_digest,
            trial_result.report,
            trial_result.report_digest,
        )
    except AttributeError as exc:
        raise ValueError("invalid-isolated-trial-result-shape") from exc
    if (
        type(captured[0]) is not str
        or type(captured[1]) is not SynthesisStatus
        or type(captured[2]) is not str
        or type(captured[3]) is not str
        or type(captured[4]) is not ObserverTrialReportV2
        or type(captured[5]) is not str
    ):
        raise ValueError("invalid-isolated-trial-result-fields")
    if (
        captured[0] != ISOLATED_TRIAL_RESULT_SCHEMA
        or captured[1] is not SynthesisStatus.FOUND
        or captured[2] != "isolated-trial-complete"
        or captured[3] != EXPECTED_UPSTREAM_TRIAL_LIMITS_DIGEST
        or captured[5] != EXPECTED_TRIAL_REPORT_DIGEST
    ):
        raise ValueError("invalid-isolated-trial-result-binding")
    trial = snapshot_receipt_trial_v2(captured[4])
    try:
        trusted_limits = snapshot_budget_limits(limits)
    except BudgetValidationError as exc:
        raise ValueError("invalid-receipt-limits") from exc
    trial_payload = trial_report_payload_v2(trial)
    provisional = ReceiptWorkerRequestV2(
        RECEIPT_REQUEST_SCHEMA,
        trial_payload,
        sha256(trial_payload).hexdigest(),
        trial.winner_digest,
        trial.corpus_digest,
        trial.manifest_digest,
        EXPECTED_GUARANTEE_DIGEST,
        trial.report_digest,
        trusted_limits,
        limits_digest_v2(trusted_limits),
    )
    result = validate_receipt_request_v2(provisional).request
    logger.debug("build_receipt_request_v2 exit")
    return result


def run_isolated_receipts_v2(
    trial_result: object,
    limits: object = DEFAULT_BUDGET_LIMITS,
) -> IsolatedObserverReceiptResultV2:
    """Run one fixed receipt child; parent checks bytes but never replays semantics."""
    logger.debug("run_isolated_receipts_v2 entry")
    try:
        request = build_receipt_request_v2(trial_result, limits)
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError):
        return _terminal(
            SynthesisStatus.INVALID,
            "invalid-isolated-receipt-request",
            "",
        )
    outcome = run_fixed_child_v2(
        FixedWorkerKindV2.RECEIPT,
        frame_bytes_v2(receipt_request_bytes_v2(request)),
        request.limits,
        popen=subprocess.Popen,
        pipe=os.pipe,
        write=os.write,
        clock=time.monotonic_ns,
        apply_limits=_apply_limits,
    )
    state_details = {
        "limit-bootstrap": "receipt-worker-limit-bootstrap",
        "pipe-bootstrap": "receipt-worker-pipe-bootstrap",
        "wall": "receipt-worker-wall",
        "output": "receipt-worker-output",
        "child": "receipt-worker-child",
        "runtime": "receipt-worker-runtime",
        "cancelled": "receipt-worker-cancelled",
    }
    if outcome.state == "invalid":
        return _terminal(
            SynthesisStatus.INVALID,
            "invalid-receipt-worker-result",
            request.limits_digest,
            request.trial_report_digest,
        )
    if outcome.state != "ok":
        return _terminal(
            SynthesisStatus.INCOMPLETE,
            state_details[outcome.state],
            request.limits_digest,
            request.trial_report_digest,
        )
    try:
        payload = unframe_exact_result_v2(
            outcome.framed_result,
            FRAME_BYTES,
            MAX_WORKER_FRAME_BYTES,
        )
        parsed = parse_receipt_result_payload_v2(payload, request)
    except (EOFError, OSError, subprocess.SubprocessError):
        return _terminal(
            SynthesisStatus.INCOMPLETE,
            "receipt-worker-runtime",
            request.limits_digest,
            request.trial_report_digest,
        )
    except (RecursionError, TypeError, UnicodeError, ValueError):
        return _terminal(
            SynthesisStatus.INVALID,
            "invalid-receipt-worker-result",
            request.limits_digest,
            request.trial_report_digest,
        )
    result = _terminal(
        parsed.status,
        parsed.detail,
        request.limits_digest,
        request.trial_report_digest,
        parsed.bundle_bytes,
        parsed.bundle_sha256,
        parsed.bundle_digest,
    )
    logger.debug("run_isolated_receipts_v2 exit status=%s", result.status.value)
    return result
