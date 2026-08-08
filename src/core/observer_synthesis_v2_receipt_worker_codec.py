"""Canonical request and terminal codecs for isolated R14.5 receipts."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_budget import BudgetLimits
from .observer_synthesis_v2_receipt_worker_types import (
    RECEIPT_REQUEST_SCHEMA,
    RECEIPT_RESULT_SCHEMA,
    ReceiptWorkerRequestV2,
)
from .observer_synthesis_v2_trial_worker_codec import trial_limits_data_v2
from .observer_synthesis_v2_types import SynthesisStatus
from .observer_synthesis_v2_worker_codec import MAX_WORKER_FRAME_BYTES
from .proof_core_codec import canonical_json, load_canonical

logger = logging.getLogger(__name__)

REQUEST_DOMAIN = RECEIPT_REQUEST_SCHEMA.encode() + b"\0request\0"
EXPECTED_BUNDLE_BYTES = 27_857
EXPECTED_BUNDLE_SHA256 = (
    "0afbd94886cef42dc5dda3a3b923f7766948bc53a32fca7481a1b861a3b54720"
)
EXPECTED_BUNDLE_DIGEST = (
    "740f55aa23a8372d01db506e1019cbab2bdb5990796c6c3b158ec048286b0895"
)


def receipt_request_bytes_v2(request: ReceiptWorkerRequestV2) -> bytes:
    """Encode one exact full-trial receipt request."""
    logger.debug("receipt_request_bytes_v2 entry")
    result = canonical_json(
        {
            "corpus_digest": request.corpus_digest,
            "guarantee_digest": request.guarantee_digest,
            "limits": trial_limits_data_v2(request.limits),
            "limits_digest": request.limits_digest,
            "manifest_digest": request.manifest_digest,
            "schema": request.schema,
            "trial_payload": request.trial_payload.decode("ascii"),
            "trial_payload_sha256": request.trial_payload_sha256,
            "trial_report_digest": request.trial_report_digest,
            "winner_digest": request.winner_digest,
        }
    ).encode()
    if len(result) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("receipt-request-too-large")
    logger.debug("receipt_request_bytes_v2 exit bytes=%d", len(result))
    return result


def receipt_request_digest_v2(request: ReceiptWorkerRequestV2) -> str:
    """Bind the result to the exact canonical request."""
    logger.debug("receipt_request_digest_v2 entry")
    result = sha256(REQUEST_DOMAIN + receipt_request_bytes_v2(request)).hexdigest()
    logger.debug("receipt_request_digest_v2 exit digest=%s", result[:12])
    return result


def receipt_request_from_bytes_v2(payload: object) -> ReceiptWorkerRequestV2:
    """Decode only the exact request shape; trust validation is separate."""
    logger.debug(
        "receipt_request_from_bytes_v2 entry type=%s",
        type(payload).__name__,
    )
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) > MAX_WORKER_FRAME_BYTES
    ):
        raise ValueError("invalid-receipt-request-frame")
    try:
        data = load_canonical(payload.decode())
        canonical = canonical_json(data).encode()
    except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("invalid-receipt-request-canonical") from exc
    keys = {
        "corpus_digest", "guarantee_digest", "limits", "limits_digest",
        "manifest_digest", "schema", "trial_payload", "trial_payload_sha256",
        "trial_report_digest", "winner_digest",
    }
    if (
        type(data) is not dict
        or set(data) != keys
        or canonical != payload
        or type(data["limits"]) is not dict
    ):
        raise ValueError("invalid-receipt-request-shape")
    limit_keys = {
        "candidate_limit", "canonical_bytes_limit", "evaluation_limit",
        "process_as_bytes_limit", "transcript_output_bytes_limit", "wall_seconds",
    }
    if set(data["limits"]) != limit_keys:
        raise ValueError("invalid-receipt-request-limit-shape")
    string_keys = keys - {"limits"}
    if any(type(data[key]) is not str for key in string_keys):
        raise ValueError("invalid-receipt-request-fields")
    try:
        trial_payload = data["trial_payload"].encode("ascii")
        limits = BudgetLimits(**data["limits"])
    except (TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("invalid-receipt-request-fields") from exc
    result = ReceiptWorkerRequestV2(
        data["schema"],
        trial_payload,
        data["trial_payload_sha256"],
        data["winner_digest"],
        data["corpus_digest"],
        data["manifest_digest"],
        data["guarantee_digest"],
        data["trial_report_digest"],
        limits,
        data["limits_digest"],
    )
    logger.debug("receipt_request_from_bytes_v2 exit")
    return result


def receipt_result_payload_v2(
    status: SynthesisStatus,
    detail: str,
    request_digest: str,
    limits_digest: str,
    bundle_bytes: bytes | None,
) -> bytes:
    """Encode the closed child terminal matrix."""
    logger.debug("receipt_result_payload_v2 entry status=%s", status.value)
    bundle_text: str | None = None
    bundle_sha = None if bundle_bytes is None else sha256(bundle_bytes).hexdigest()
    bundle_digest = None
    if bundle_bytes is not None:
        bundle_text = bundle_bytes.decode("ascii")
        data = load_canonical(bundle_text)
        if type(data) is not dict or type(data.get("bundle_digest")) is not str:
            raise ValueError("invalid-receipt-worker-bundle")
        bundle_digest = data["bundle_digest"]
    result = canonical_json(
        {
            "bundle": bundle_text,
            "bundle_digest": bundle_digest,
            "bundle_sha256": bundle_sha,
            "detail": detail,
            "limits_digest": limits_digest,
            "request_digest": request_digest,
            "schema": RECEIPT_RESULT_SCHEMA,
            "status": status.value,
        }
    ).encode()
    if len(result) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("receipt-result-too-large")
    logger.debug("receipt_result_payload_v2 exit bytes=%d", len(result))
    return result
