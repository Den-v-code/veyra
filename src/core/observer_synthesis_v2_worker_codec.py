"""Strict bounded canonical framing for the R14.2b worker."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_budget import BudgetLimits
from .observer_synthesis_v2_types import SynthesisStatus
from .observer_synthesis_v2_worker_types import (
    WORKER_RESULT_SCHEMA,
    ObserverWorkerRequestV2,
)
from .proof_core_codec import canonical_json, load_canonical

logger = logging.getLogger(__name__)

MAX_WORKER_FRAME_BYTES = 64 * 1024
FRAME_BYTES = 8


def _limits_data(limits: BudgetLimits) -> dict[str, int]:
    logger.debug("_limits_data entry")
    result = {
        "candidate_limit": limits.candidate_limit,
        "canonical_bytes_limit": limits.canonical_bytes_limit,
        "evaluation_limit": limits.evaluation_limit,
        "process_as_bytes_limit": limits.process_as_bytes_limit,
        "transcript_output_bytes_limit": limits.transcript_output_bytes_limit,
        "wall_seconds": limits.wall_seconds,
    }
    logger.debug("_limits_data exit")
    return result


def request_bytes_v2(request: ObserverWorkerRequestV2) -> bytes:
    logger.debug("request_bytes_v2 entry")
    result = canonical_json(
        {
            "catalog_digest": request.catalog_digest,
            "corpus_digest": request.corpus_digest,
            "limits": _limits_data(request.limits),
            "schema": request.schema,
            "train_case_digests": list(request.train_case_digests),
            "train_case_ids": list(request.train_case_ids),
        }
    ).encode()
    if len(result) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("worker-request-too-large")
    logger.debug("request_bytes_v2 exit bytes=%d", len(result))
    return result


def request_from_bytes_v2(payload: bytes) -> ObserverWorkerRequestV2:
    logger.debug("request_from_bytes_v2 entry bytes=%d", len(payload))
    if type(payload) is not bytes or not payload or len(payload) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("invalid-worker-request-frame")
    data = load_canonical(payload.decode())
    keys = {
        "catalog_digest", "corpus_digest", "limits", "schema",
        "train_case_digests", "train_case_ids",
    }
    if type(data) is not dict or set(data) != keys or type(data["limits"]) is not dict:
        raise ValueError("invalid-worker-request-shape")
    limits = data["limits"]
    limit_keys = {
        "candidate_limit", "canonical_bytes_limit", "evaluation_limit",
        "process_as_bytes_limit", "transcript_output_bytes_limit", "wall_seconds",
    }
    if set(limits) != limit_keys:
        raise ValueError("invalid-worker-limit-shape")
    result = ObserverWorkerRequestV2(
        data["schema"],
        data["catalog_digest"],
        data["corpus_digest"],
        tuple(data["train_case_ids"]),
        tuple(data["train_case_digests"]),
        BudgetLimits(**limits),
    )
    logger.debug("request_from_bytes_v2 exit")
    return result


def frame_bytes_v2(payload: bytes) -> bytes:
    logger.debug("frame_bytes_v2 entry bytes=%d", len(payload))
    if type(payload) is not bytes or len(payload) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("invalid-worker-frame")
    result = len(payload).to_bytes(FRAME_BYTES, "big") + payload
    logger.debug("frame_bytes_v2 exit bytes=%d", len(result))
    return result


def result_payload_v2(status: SynthesisStatus, detail: str, report: object) -> bytes:
    logger.debug("result_payload_v2 entry status=%s", status.value)
    result = canonical_json(
        {
            "detail": detail,
            "report": report,
            "schema": WORKER_RESULT_SCHEMA,
            "status": status.value,
        }
    ).encode()
    if len(result) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("worker-result-too-large")
    logger.debug("result_payload_v2 exit bytes=%d", len(result))
    return result


def payload_digest_v2(payload: bytes) -> str:
    logger.debug("payload_digest_v2 entry bytes=%d", len(payload))
    result = sha256(WORKER_RESULT_SCHEMA.encode() + b"\0" + payload).hexdigest()
    logger.debug("payload_digest_v2 exit digest=%s", result[:12])
    return result
