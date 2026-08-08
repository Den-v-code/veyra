"""Exact request and result validation for isolated R14.5 receipts."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_budget import BudgetValidationError, snapshot_budget_limits
from .observer_synthesis_v2_cegis_codec import limits_digest_v2
from .observer_synthesis_v2_receipt_worker_codec import (
    EXPECTED_BUNDLE_BYTES,
    EXPECTED_BUNDLE_DIGEST,
    EXPECTED_BUNDLE_SHA256,
    receipt_request_bytes_v2,
    receipt_request_digest_v2,
    receipt_request_from_bytes_v2,
)
from .observer_synthesis_v2_receipt_worker_trial import (
    TRIAL_PAYLOAD_SHA256,
    trial_report_from_payload_v2,
)
from .observer_synthesis_v2_receipt_worker_types import (
    RECEIPT_REQUEST_SCHEMA,
    RECEIPT_RESULT_SCHEMA,
    ParsedReceiptWorkerResultV2,
    ReceiptWorkerRequestV2,
    ValidatedReceiptWorkerRequestV2,
)
from .observer_synthesis_v2_trial import (
    EXPECTED_GUARANTEE_DIGEST,
    EXPECTED_TRIAL_REPORT_DIGEST,
)
from .observer_synthesis_v2_trial_validation import (
    EXPECTED_CORPUS_DIGEST,
    EXPECTED_WINNER_DIGEST,
)
from .observer_synthesis_v2_types import SynthesisStatus
from .proof_core_codec import canonical_json, load_canonical

logger = logging.getLogger(__name__)

CHILD_INCOMPLETE_DETAILS = {
    "candidate-limit",
    "canonical-bytes-limit",
    "evaluation-limit",
    "transcript-output-bytes-limit",
    "wall-time-limit",
    "process-address-space-limit",
}


def validate_receipt_request_v2(
    request: object,
) -> ValidatedReceiptWorkerRequestV2:
    """Deep-snapshot one exact report-bound receipt request."""
    logger.debug("validate_receipt_request_v2 entry type=%s", type(request).__name__)
    if type(request) is not ReceiptWorkerRequestV2:
        raise ValueError("invalid-receipt-request-type")
    try:
        captured = (
            request.schema,
            request.trial_payload,
            request.trial_payload_sha256,
            request.winner_digest,
            request.corpus_digest,
            request.manifest_digest,
            request.guarantee_digest,
            request.trial_report_digest,
            request.limits,
            request.limits_digest,
        )
    except AttributeError as exc:
        raise ValueError("invalid-receipt-request-shape") from exc
    if (
        type(captured[0]) is not str
        or type(captured[1]) is not bytes
        or any(type(value) is not str for value in captured[2:8])
        or type(captured[9]) is not str
    ):
        raise ValueError("invalid-receipt-request-fields")
    payload = memoryview(captured[1]).tobytes()
    try:
        limits = snapshot_budget_limits(captured[8])
    except (AttributeError, BudgetValidationError) as exc:
        raise ValueError("invalid-receipt-request-shape") from exc
    if sha256(payload).hexdigest() != captured[2]:
        raise ValueError("invalid-receipt-request-payload-digest")
    trial = trial_report_from_payload_v2(payload)
    roots = (
        captured[0],
        captured[2],
        captured[3],
        captured[4],
        captured[5],
        captured[6],
        captured[7],
        captured[9],
    )
    expected = (
        RECEIPT_REQUEST_SCHEMA,
        TRIAL_PAYLOAD_SHA256,
        EXPECTED_WINNER_DIGEST,
        trial.corpus_digest,
        trial.manifest_digest,
        EXPECTED_GUARANTEE_DIGEST,
        EXPECTED_TRIAL_REPORT_DIGEST,
        limits_digest_v2(limits),
    )
    if roots != expected or captured[4] != EXPECTED_CORPUS_DIGEST:
        raise ValueError("invalid-receipt-request-binding")
    trusted = ReceiptWorkerRequestV2(
        captured[0],
        payload,
        captured[2],
        captured[3],
        captured[4],
        captured[5],
        captured[6],
        captured[7],
        limits,
        captured[9],
    )
    encoded = receipt_request_bytes_v2(trusted)
    decoded = receipt_request_from_bytes_v2(encoded)
    if decoded != trusted:
        raise ValueError("receipt-request-roundtrip-mismatch")
    result = ValidatedReceiptWorkerRequestV2(trusted, trial)
    logger.debug("validate_receipt_request_v2 exit")
    return result


def parse_receipt_result_payload_v2(
    payload: object,
    request: object,
) -> ParsedReceiptWorkerResultV2:
    """Validate the closed terminal matrix and exact opaque bundle pins."""
    logger.debug(
        "parse_receipt_result_payload_v2 entry type=%s",
        type(payload).__name__,
    )
    if type(payload) is not bytes or not payload:
        raise ValueError("invalid-receipt-result-frame")
    trusted = validate_receipt_request_v2(request).request
    try:
        data = load_canonical(payload.decode())
        canonical = canonical_json(data).encode()
    except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("invalid-receipt-result-canonical") from exc
    keys = {
        "bundle", "bundle_digest", "bundle_sha256", "detail", "limits_digest",
        "request_digest", "schema", "status",
    }
    if type(data) is not dict or set(data) != keys or canonical != payload:
        raise ValueError("invalid-receipt-result-shape")
    string_keys = {"detail", "limits_digest", "request_digest", "schema", "status"}
    if any(type(data[key]) is not str for key in string_keys):
        raise ValueError("invalid-receipt-result-fields")
    if (
        data["schema"] != RECEIPT_RESULT_SCHEMA
        or data["request_digest"] != receipt_request_digest_v2(trusted)
        or data["limits_digest"] != trusted.limits_digest
    ):
        raise ValueError("invalid-receipt-result-binding")
    try:
        status = SynthesisStatus(data["status"])
    except ValueError as exc:
        raise ValueError("invalid-receipt-result-status") from exc
    optional = (data["bundle"], data["bundle_sha256"], data["bundle_digest"])
    if status is SynthesisStatus.FOUND:
        if data["detail"] != "receipt-complete" or any(
            type(value) is not str for value in optional
        ):
            raise ValueError("invalid-receipt-complete-shape")
        try:
            bundle = data["bundle"].encode("ascii")
        except UnicodeError as exc:
            raise ValueError("invalid-receipt-bundle-encoding") from exc
        if (
            len(bundle) != EXPECTED_BUNDLE_BYTES
            or sha256(bundle).hexdigest() != EXPECTED_BUNDLE_SHA256
            or data["bundle_sha256"] != EXPECTED_BUNDLE_SHA256
            or data["bundle_digest"] != EXPECTED_BUNDLE_DIGEST
        ):
            raise ValueError("invalid-receipt-bundle-pins")
        try:
            bundle_data = load_canonical(bundle.decode())
            bundle_canonical = canonical_json(bundle_data).encode()
        except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
            raise ValueError("invalid-receipt-bundle-canonical") from exc
        if (
            bundle_canonical != bundle
            or type(bundle_data) is not dict
            or bundle_data.get("bundle_digest") != EXPECTED_BUNDLE_DIGEST
        ):
            raise ValueError("invalid-receipt-bundle-binding")
        result = ParsedReceiptWorkerResultV2(
            status,
            data["detail"],
            bundle,
            data["bundle_sha256"],
            data["bundle_digest"],
        )
    elif status is SynthesisStatus.INCOMPLETE:
        if any(value is not None for value in optional) or (
            data["detail"] not in CHILD_INCOMPLETE_DETAILS
        ):
            raise ValueError("invalid-receipt-incomplete")
        result = ParsedReceiptWorkerResultV2(status, data["detail"], None, None, None)
    elif status is SynthesisStatus.INVALID:
        if any(value is not None for value in optional) or (
            data["detail"] != "invalid-receipt"
        ):
            raise ValueError("invalid-receipt-invalid")
        result = ParsedReceiptWorkerResultV2(status, data["detail"], None, None, None)
    else:
        raise ValueError("invalid-receipt-terminal-status")
    logger.debug("parse_receipt_result_payload_v2 exit status=%s", status.value)
    return result
