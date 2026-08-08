"""Fresh full-subject validation without parent-side semantic evaluation."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_baselines import build_trial_subject_manifest_v2
from .observer_synthesis_v2_corpus import DEFAULT_LOCKED_CORPUS
from .observer_synthesis_v2_protocol import ExpectedRelation, ObserverCaseV2, SplitId
from .observer_synthesis_v2_trial_codec import retained_subject_data_v2
from .observer_synthesis_v2_trial_execution import split_summaries_v2
from .observer_synthesis_v2_trial_types import (
    TrialAccountingV2,
    TrialCaseResultV2,
    TrialSplitSummaryV2,
    TrialSubjectResultV2,
    TrialSubjectRoleV2,
)
from .observer_synthesis_v2_trial_provenance import _brand_trial_subject_v2
from .observer_synthesis_v2_trial_case_provenance import _brand_trial_case_v2
from .observer_synthesis_v2_trial_validation import (
    DEFAULT_LOCKED_WINNER_V2,
    snapshot_locked_corpus_for_trial_v2,
)
from .observer_synthesis_v2_trial_worker_codec import (
    full_subject_data_v2,
    trial_subject_payload_digest_v2,
)
from .observer_synthesis_v2_trial_worker_types import TrialSubjectWorkerRequestV2
from .proof_core_codec import canonical_json

logger = logging.getLogger(__name__)

EXPECTED_ACCOUNTING = (
    (1, 106, 10, 3451, False),
    (1, 62, 10, 3461, False),
    (1, 105, 10, 3499, False),
    (1, 106, 10, 3451, False),
    (1, 108, 10, 3461, False),
)
EXPECTED_RETAINED_DIGESTS = (
    "101b805ca0920511c9e2b14710157cc8170b09e59e99bea01bf08d82660ccb27",
    "08385bd6003777ecd433519e9044e5739f60339781a39e07d49cc5e37c8ce1ee",
    "851c4dd5bd13dbfa598923dd8560efa39bbd20bb4e745d29077a3fca3b29cd02",
    "101b805ca0920511c9e2b14710157cc8170b09e59e99bea01bf08d82660ccb27",
    "5bb609bdbd5b25f77b0e90b12facef7c17870887ab3331c9e6cd724790acc981",
)
EXPECTED_SUBJECT_PAYLOAD_DIGESTS = (
    "317d79bdfa03b9c5438e6513b6d3a455803ae72c75ddf5c7b1b670cfcbd179d1",
    "7fa7995bbbb6a7987809c9261a39e7e62bb81bf6e208c78d78c2a618ce5f8815",
    "710bbf1bf701cc732ab80c382192f1acff743877fb8678ae11b32e4ea95d6a2b",
    "e40b9b8b9c532290bb9d60ccfca87bb155307857fde05c41612fb7957632b989",
    "9dcfcd18cea0e8e321df00b072aa1d8a69ca206b38b15fb1c52f2b2fe437a3ad",
)


def _parse_case_v2(data: object, expected: ObserverCaseV2) -> TrialCaseResultV2:
    logger.debug("_parse_case_v2 entry")
    keys = {
        "actual", "case_digest", "case_id", "expected", "matched",
        "outcome_digest", "required_for_winner", "split",
    }
    if type(data) is not dict or set(data) != keys:
        raise ValueError("invalid-trial-subject-case-shape")
    if (
        type(data["case_id"]) is not int
        or type(data["case_digest"]) is not str
        or type(data["split"]) is not str
        or type(data["required_for_winner"]) is not bool
        or type(data["expected"]) is not str
        or type(data["actual"]) is not str
        or type(data["matched"]) is not bool
        or type(data["outcome_digest"]) is not str
    ):
        raise ValueError("invalid-trial-subject-case-fields")
    try:
        split = SplitId(data["split"])
        relation = ExpectedRelation(data["expected"])
        actual = ExpectedRelation(data["actual"])
    except ValueError as exc:
        raise ValueError("invalid-trial-subject-case-enum") from exc
    if (
        data["case_id"] != expected.case_id
        or data["case_digest"] != expected.case_digest
        or split is not expected.split
        or data["required_for_winner"] is not expected.required_for_winner
        or relation is not expected.expected
        or data["matched"] is not (actual is relation)
        or len(data["outcome_digest"]) != 64
    ):
        raise ValueError("invalid-trial-subject-case-binding")
    result = TrialCaseResultV2(
        data["case_id"],
        data["case_digest"],
        split,
        data["required_for_winner"],
        relation,
        actual,
        data["matched"],
        data["outcome_digest"],
    )
    logger.debug("_parse_case_v2 exit case_id=%d", result.case_id)
    return result


def _parse_split_v2(data: object) -> TrialSplitSummaryV2:
    logger.debug("_parse_split_v2 entry")
    keys = {
        "diagnostic_matched", "diagnostic_total", "required_matched",
        "required_total", "split", "total",
    }
    if (
        type(data) is not dict
        or set(data) != keys
        or type(data["split"]) is not str
        or any(type(data[key]) is not int for key in keys - {"split"})
    ):
        raise ValueError("invalid-trial-subject-split-shape")
    try:
        split = SplitId(data["split"])
    except ValueError as exc:
        raise ValueError("invalid-trial-subject-split-enum") from exc
    result = TrialSplitSummaryV2(
        split,
        data["total"],
        data["required_total"],
        data["required_matched"],
        data["diagnostic_total"],
        data["diagnostic_matched"],
    )
    logger.debug("_parse_split_v2 exit split=%s", result.split.value)
    return result


def _parse_accounting_v2(data: object, index: int) -> TrialAccountingV2:
    logger.debug("_parse_accounting_v2 entry index=%d", index)
    keys = {
        "candidates", "canonical_bytes", "cutoff", "evaluations",
        "retained_output_bytes",
    }
    if (
        type(data) is not dict
        or set(data) != keys
        or type(data["cutoff"]) is not bool
        or any(type(data[key]) is not int for key in keys - {"cutoff"})
    ):
        raise ValueError("invalid-trial-subject-accounting-shape")
    values = (
        data["candidates"],
        data["canonical_bytes"],
        data["evaluations"],
        data["retained_output_bytes"],
        data["cutoff"],
    )
    if values != EXPECTED_ACCOUNTING[index]:
        raise ValueError("invalid-trial-subject-accounting-binding")
    result = TrialAccountingV2(*values)
    logger.debug("_parse_accounting_v2 exit")
    return result


def validate_complete_trial_subject_data_v2(
    data: object,
    request: TrialSubjectWorkerRequestV2,
) -> TrialSubjectResultV2:
    """Rebuild and pin a complete subject without observer evaluation."""
    logger.debug("validate_complete_trial_subject_data_v2 entry")
    keys = {
        "accounting", "cases", "diagnostic_matched", "diagnostic_total",
        "observer_digest", "required_matched", "required_total",
        "retained_digest", "role", "splits", "subject_id",
    }
    integer_keys = {
        "diagnostic_matched", "diagnostic_total", "required_matched", "required_total",
    }
    string_keys = {"observer_digest", "retained_digest", "role", "subject_id"}
    if (
        type(data) is not dict
        or set(data) != keys
        or any(type(data[key]) is not int for key in integer_keys)
        or any(type(data[key]) is not str for key in string_keys)
        or type(data["cases"]) is not list
        or type(data["splits"]) is not list
    ):
        raise ValueError("invalid-trial-subject-data-shape")
    corpus = snapshot_locked_corpus_for_trial_v2(DEFAULT_LOCKED_CORPUS)
    if len(data["cases"]) != 10:
        raise ValueError("invalid-trial-subject-case-count")
    cases = tuple(
        _brand_trial_case_v2(
            _parse_case_v2(row, expected),
            request.subject_index,
            case_index,
        )
        for case_index, (row, expected) in enumerate(
            zip(data["cases"], corpus.cases, strict=True)
        )
    )
    splits = tuple(_parse_split_v2(row) for row in data["splits"])
    if splits != split_summaries_v2(cases):
        raise ValueError("invalid-trial-subject-split-binding")
    accounting = _parse_accounting_v2(data["accounting"], request.subject_index)
    required = tuple(row for row in cases if row.required_for_winner)
    diagnostic = tuple(row for row in cases if not row.required_for_winner)
    counts = (
        sum(row.matched for row in required),
        len(required),
        sum(row.matched for row in diagnostic),
        len(diagnostic),
    )
    reported = (
        data["required_matched"],
        data["required_total"],
        data["diagnostic_matched"],
        data["diagnostic_total"],
    )
    if counts != reported:
        raise ValueError("invalid-trial-subject-score-binding")
    try:
        role = TrialSubjectRoleV2(data["role"])
    except ValueError as exc:
        raise ValueError("invalid-trial-subject-role") from exc
    manifest = build_trial_subject_manifest_v2(DEFAULT_LOCKED_WINNER_V2)
    expected_subject = manifest.subjects[request.subject_index]
    retained = canonical_json(
        retained_subject_data_v2(expected_subject, cases, splits)
    ).encode()
    retained_digest = sha256(
        b"veyra.observer-synthesis-v2.retained-trial.r14.4.v1\0" + retained
    ).hexdigest()
    if (
        data["subject_id"] != request.subject_id
        or role is not request.role
        or data["observer_digest"] != request.observer_digest
        or data["retained_digest"] != retained_digest
        or retained_digest != EXPECTED_RETAINED_DIGESTS[request.subject_index]
    ):
        raise ValueError("invalid-trial-subject-identity-binding")
    provisional = TrialSubjectResultV2(
        data["subject_id"],
        role,
        data["observer_digest"],
        cases,
        splits,
        *reported,
        accounting,
        data["retained_digest"],
    )
    payload_digest = trial_subject_payload_digest_v2(full_subject_data_v2(provisional))
    if payload_digest != EXPECTED_SUBJECT_PAYLOAD_DIGESTS[request.subject_index]:
        raise ValueError("invalid-trial-subject-payload-pin")
    result = _brand_trial_subject_v2(provisional, request.subject_index)
    logger.debug("validate_complete_trial_subject_data_v2 exit index=%d", request.subject_index)
    return result
