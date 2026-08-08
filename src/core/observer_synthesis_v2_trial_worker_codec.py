"""Canonical request/result codec for isolated R14.4b subjects."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_budget import BudgetLimits
from .observer_synthesis_v2_trial_codec import (
    case_result_data_v2,
    split_summary_data_v2,
)
from .observer_synthesis_v2_trial_types import TrialSubjectResultV2
from .observer_synthesis_v2_trial_worker_types import (
    TRIAL_SUBJECT_REQUEST_SCHEMA,
    TRIAL_SUBJECT_RESULT_SCHEMA,
    TrialSubjectWorkerRequestV2,
)
from .observer_synthesis_v2_types import SynthesisStatus
from .observer_synthesis_v2_worker_codec import MAX_WORKER_FRAME_BYTES
from .proof_core_codec import canonical_json, load_canonical

logger = logging.getLogger(__name__)

REQUEST_DOMAIN = TRIAL_SUBJECT_REQUEST_SCHEMA.encode() + b"\0request\0"
SUBJECT_DOMAIN = TRIAL_SUBJECT_RESULT_SCHEMA.encode() + b"\0subject\0"


def trial_limits_data_v2(limits: BudgetLimits) -> dict[str, int]:
    """Return the exact six-field active limit contract."""
    logger.debug("trial_limits_data_v2 entry")
    result = {
        "candidate_limit": limits.candidate_limit,
        "canonical_bytes_limit": limits.canonical_bytes_limit,
        "evaluation_limit": limits.evaluation_limit,
        "process_as_bytes_limit": limits.process_as_bytes_limit,
        "transcript_output_bytes_limit": limits.transcript_output_bytes_limit,
        "wall_seconds": limits.wall_seconds,
    }
    logger.debug("trial_limits_data_v2 exit")
    return result


def trial_subject_request_bytes_v2(request: TrialSubjectWorkerRequestV2) -> bytes:
    """Encode one bounded canonical subject request."""
    logger.debug(
        "trial_subject_request_bytes_v2 entry index=%d",
        request.subject_index,
    )
    result = canonical_json(
        {
            "case_digests": list(request.case_digests),
            "case_ids": list(request.case_ids),
            "corpus_digest": request.corpus_digest,
            "limits": trial_limits_data_v2(request.limits),
            "limits_digest": request.limits_digest,
            "manifest_digest": request.manifest_digest,
            "observer_digest": request.observer_digest,
            "role": request.role.value,
            "schema": request.schema,
            "subject_id": request.subject_id,
            "subject_index": request.subject_index,
            "winner_digest": request.winner_digest,
        }
    ).encode()
    if len(result) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("trial-subject-request-too-large")
    logger.debug("trial_subject_request_bytes_v2 exit bytes=%d", len(result))
    return result


def trial_subject_request_digest_v2(request: TrialSubjectWorkerRequestV2) -> str:
    """Bind a child response to the exact canonical request."""
    logger.debug("trial_subject_request_digest_v2 entry")
    result = sha256(
        REQUEST_DOMAIN + trial_subject_request_bytes_v2(request)
    ).hexdigest()
    logger.debug("trial_subject_request_digest_v2 exit digest=%s", result[:12])
    return result


def trial_subject_request_from_bytes_v2(
    payload: bytes,
) -> TrialSubjectWorkerRequestV2:
    """Decode only the exact request shape; semantic validation is separate."""
    logger.debug("trial_subject_request_from_bytes_v2 entry bytes=%d", len(payload))
    if type(payload) is not bytes or not payload or len(payload) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("invalid-trial-subject-request-frame")
    data = load_canonical(payload.decode())
    keys = {
        "case_digests", "case_ids", "corpus_digest", "limits", "limits_digest",
        "manifest_digest", "observer_digest", "role", "schema", "subject_id",
        "subject_index", "winner_digest",
    }
    if type(data) is not dict or set(data) != keys or type(data["limits"]) is not dict:
        raise ValueError("invalid-trial-subject-request-shape")
    limits = data["limits"]
    limit_keys = {
        "candidate_limit", "canonical_bytes_limit", "evaluation_limit",
        "process_as_bytes_limit", "transcript_output_bytes_limit", "wall_seconds",
    }
    if set(limits) != limit_keys:
        raise ValueError("invalid-trial-subject-limit-shape")
    from .observer_synthesis_v2_trial_types import TrialSubjectRoleV2

    result = TrialSubjectWorkerRequestV2(
        data["schema"],
        data["subject_index"],
        data["subject_id"],
        TrialSubjectRoleV2(data["role"]),
        data["observer_digest"],
        data["winner_digest"],
        data["corpus_digest"],
        data["manifest_digest"],
        tuple(data["case_ids"]),
        tuple(data["case_digests"]),
        BudgetLimits(**limits),
        data["limits_digest"],
    )
    logger.debug("trial_subject_request_from_bytes_v2 exit")
    return result


def full_subject_data_v2(subject: TrialSubjectResultV2) -> dict[str, object]:
    """Serialize every retained subject field needed for pure assembly."""
    logger.debug("full_subject_data_v2 entry subject_id=%s", subject.subject_id)
    result: dict[str, object] = {
        "accounting": {
            "candidates": subject.accounting.candidates,
            "canonical_bytes": subject.accounting.canonical_bytes,
            "cutoff": subject.accounting.cutoff,
            "evaluations": subject.accounting.evaluations,
            "retained_output_bytes": subject.accounting.retained_output_bytes,
        },
        "cases": [case_result_data_v2(row) for row in subject.cases],
        "diagnostic_matched": subject.diagnostic_matched,
        "diagnostic_total": subject.diagnostic_total,
        "observer_digest": subject.observer_digest,
        "required_matched": subject.required_matched,
        "required_total": subject.required_total,
        "retained_digest": subject.retained_digest,
        "role": subject.role.value,
        "splits": [split_summary_data_v2(row) for row in subject.splits],
        "subject_id": subject.subject_id,
    }
    logger.debug("full_subject_data_v2 exit")
    return result


def trial_subject_payload_digest_v2(subject_data: object) -> str:
    """Digest one canonical full subject payload under its own domain."""
    logger.debug("trial_subject_payload_digest_v2 entry")
    result = sha256(
        SUBJECT_DOMAIN + canonical_json(subject_data).encode()
    ).hexdigest()
    logger.debug("trial_subject_payload_digest_v2 exit digest=%s", result[:12])
    return result


def trial_subject_result_payload_v2(
    status: SynthesisStatus,
    detail: str,
    request_digest: str,
    limits_digest: str,
    subject: TrialSubjectResultV2 | None,
) -> bytes:
    """Encode one closed child terminal envelope."""
    logger.debug("trial_subject_result_payload_v2 entry status=%s", status.value)
    data = None if subject is None else full_subject_data_v2(subject)
    digest = None if data is None else trial_subject_payload_digest_v2(data)
    result = canonical_json(
        {
            "detail": detail,
            "limits_digest": limits_digest,
            "request_digest": request_digest,
            "schema": TRIAL_SUBJECT_RESULT_SCHEMA,
            "status": status.value,
            "subject": data,
            "subject_payload_digest": digest,
        }
    ).encode()
    if len(result) > MAX_WORKER_FRAME_BYTES:
        raise ValueError("trial-subject-result-too-large")
    logger.debug("trial_subject_result_payload_v2 exit bytes=%d", len(result))
    return result
