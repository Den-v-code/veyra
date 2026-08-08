"""Request and terminal-envelope validation for isolated R14.4b subjects."""
from __future__ import annotations

import logging

from .observer_synthesis_v2_baselines import build_trial_subject_manifest_v2
from .observer_synthesis_v2_budget import BudgetValidationError, snapshot_budget_limits
from .observer_synthesis_v2_cegis_codec import limits_digest_v2
from .observer_synthesis_v2_trial_validation import (
    DEFAULT_LOCKED_WINNER_V2,
    EXPECTED_CASE_DIGESTS,
    EXPECTED_CASE_IDS,
    EXPECTED_CORPUS_DIGEST,
    EXPECTED_WINNER_DIGEST,
)
from .observer_synthesis_v2_trial_worker_codec import (
    full_subject_data_v2,
    trial_subject_payload_digest_v2,
    trial_subject_request_bytes_v2,
    trial_subject_request_digest_v2,
    trial_subject_request_from_bytes_v2,
)
from .observer_synthesis_v2_trial_worker_subject_validation import (
    validate_complete_trial_subject_data_v2,
)
from .observer_synthesis_v2_trial_worker_types import (
    TRIAL_SUBJECT_REQUEST_SCHEMA,
    TRIAL_SUBJECT_RESULT_SCHEMA,
    ParsedTrialSubjectResultV2,
    TrialSubjectWorkerRequestV2,
)
from .observer_synthesis_v2_trial_types import TrialSubjectRoleV2
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


def validate_trial_subject_request_v2(
    request: object,
) -> TrialSubjectWorkerRequestV2:
    """Snapshot and require one exact index-to-manifest request binding."""
    logger.debug(
        "validate_trial_subject_request_v2 entry type=%s",
        type(request).__name__,
    )
    if type(request) is not TrialSubjectWorkerRequestV2:
        raise ValueError("invalid-trial-subject-request-type")
    manifest = build_trial_subject_manifest_v2(DEFAULT_LOCKED_WINNER_V2)
    try:
        types_ok = (
            type(request.schema) is str
            and type(request.subject_index) is int
            and type(request.subject_id) is str
            and type(request.role) is TrialSubjectRoleV2
            and type(request.observer_digest) is str
            and type(request.winner_digest) is str
            and type(request.corpus_digest) is str
            and type(request.manifest_digest) is str
            and type(request.case_ids) is tuple
            and type(request.case_digests) is tuple
            and type(request.limits_digest) is str
        )
    except AttributeError as exc:
        raise ValueError("invalid-trial-subject-request-shape") from exc
    if not types_ok or not 0 <= request.subject_index < 5:
        raise ValueError("invalid-trial-subject-request-shape")
    if (
        any(type(value) is not int for value in request.case_ids)
        or any(type(value) is not str for value in request.case_digests)
    ):
        raise ValueError("invalid-trial-subject-request-items")
    expected = manifest.subjects[request.subject_index]
    try:
        limits = snapshot_budget_limits(request.limits)
    except (AttributeError, BudgetValidationError) as exc:
        raise ValueError("invalid-trial-subject-request-limits") from exc
    if (
        request.schema != TRIAL_SUBJECT_REQUEST_SCHEMA
        or request.subject_id != expected.subject_id
        or request.role is not expected.role
        or request.observer_digest != expected.digest
        or request.winner_digest != EXPECTED_WINNER_DIGEST
        or request.corpus_digest != EXPECTED_CORPUS_DIGEST
        or request.manifest_digest != manifest.manifest_digest
        or request.case_ids != EXPECTED_CASE_IDS
        or request.case_digests != EXPECTED_CASE_DIGESTS
        or request.limits_digest != limits_digest_v2(limits)
    ):
        raise ValueError("invalid-trial-subject-request-binding")
    trusted = TrialSubjectWorkerRequestV2(
        request.schema,
        request.subject_index,
        request.subject_id,
        request.role,
        request.observer_digest,
        request.winner_digest,
        request.corpus_digest,
        request.manifest_digest,
        tuple(request.case_ids),
        tuple(request.case_digests),
        limits,
        request.limits_digest,
    )
    encoded = trial_subject_request_bytes_v2(trusted)
    if trial_subject_request_from_bytes_v2(encoded) != trusted:
        raise ValueError("trial-subject-request-roundtrip-mismatch")
    logger.debug("validate_trial_subject_request_v2 exit index=%d", trusted.subject_index)
    return trusted


def parse_trial_subject_result_payload_v2(
    payload: bytes,
    request: object,
) -> ParsedTrialSubjectResultV2:
    """Parse a closed terminal matrix and validate complete subject data."""
    logger.debug("parse_trial_subject_result_payload_v2 entry bytes=%d", len(payload))
    if type(payload) is not bytes or not payload:
        raise ValueError("invalid-trial-subject-result-frame")
    trusted_request = validate_trial_subject_request_v2(request)
    try:
        data = load_canonical(payload.decode())
        canonical = canonical_json(data).encode()
    except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.debug(
            "parse_trial_subject_result_payload_v2 invalid canonical payload",
            exc_info=True,
        )
        raise ValueError("invalid-trial-subject-result-shape") from exc
    keys = {
        "detail", "limits_digest", "request_digest", "schema", "status",
        "subject", "subject_payload_digest",
    }
    if type(data) is not dict or set(data) != keys or canonical != payload:
        raise ValueError("invalid-trial-subject-result-shape")
    string_keys = {
        "detail", "limits_digest", "request_digest", "schema", "status",
    }
    if any(type(data[key]) is not str for key in string_keys):
        raise ValueError("invalid-trial-subject-result-fields")
    if (
        data["schema"] != TRIAL_SUBJECT_RESULT_SCHEMA
        or data["request_digest"] != trial_subject_request_digest_v2(trusted_request)
        or data["limits_digest"] != trusted_request.limits_digest
    ):
        raise ValueError("invalid-trial-subject-result-binding")
    try:
        status = SynthesisStatus(data["status"])
    except ValueError as exc:
        raise ValueError("invalid-trial-subject-result-status") from exc
    subject = data["subject"]
    digest = data["subject_payload_digest"]
    if status is SynthesisStatus.FOUND:
        if data["detail"] != "trial-subject-complete" or type(digest) is not str:
            raise ValueError("invalid-trial-subject-complete-shape")
        trusted = validate_complete_trial_subject_data_v2(subject, trusted_request)
        if digest != trial_subject_payload_digest_v2(full_subject_data_v2(trusted)):
            raise ValueError("invalid-trial-subject-envelope-digest")
        result = ParsedTrialSubjectResultV2(status, data["detail"], trusted, digest)
    elif status is SynthesisStatus.INCOMPLETE:
        if (
            subject is not None
            or digest is not None
            or data["detail"] not in CHILD_INCOMPLETE_DETAILS
        ):
            raise ValueError("invalid-trial-subject-incomplete")
        result = ParsedTrialSubjectResultV2(status, data["detail"], None, None)
    elif status is SynthesisStatus.INVALID:
        if (
            subject is not None
            or digest is not None
            or data["detail"] != "invalid-trial-subject"
        ):
            raise ValueError("invalid-trial-subject-invalid")
        result = ParsedTrialSubjectResultV2(status, data["detail"], None, None)
    else:
        raise ValueError("invalid-trial-subject-terminal-status")
    logger.debug("parse_trial_subject_result_payload_v2 exit status=%s", status.value)
    return result
