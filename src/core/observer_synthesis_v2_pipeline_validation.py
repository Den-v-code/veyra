"""One-shot exact validators for the atomic finite R14 aggregate."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_baselines import EXPECTED_SUBJECT_MANIFEST_DIGEST
from .observer_synthesis_v2_receipt_worker import (
    EXPECTED_UPSTREAM_TRIAL_LIMITS_DIGEST,
)
from .observer_synthesis_v2_receipt_worker_codec import (
    EXPECTED_BUNDLE_BYTES,
    EXPECTED_BUNDLE_DIGEST,
    EXPECTED_BUNDLE_SHA256,
)
from .observer_synthesis_v2_receipt_worker_types import (
    ISOLATED_RECEIPT_RESULT_SCHEMA,
    IsolatedObserverReceiptResultV2,
)
from .observer_synthesis_v2_trial import (
    EXPECTED_GUARANTEE_DIGEST,
    EXPECTED_TRIAL_REPORT_DIGEST,
    TRIAL_SCHEMA,
)
from .observer_synthesis_v2_trial_types import (
    BoundedGuaranteeV2,
    ObserverTrialReportV2,
    TrialSubjectResultV2,
    TrialSubjectRoleV2,
)
from .observer_synthesis_v2_trial_worker_types import (
    ISOLATED_TRIAL_RESULT_SCHEMA,
    IsolatedObserverTrialResultV2,
)
from .observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)


def _guarantee_snapshot(value: object) -> tuple[object, ...] | None:
    """Capture every finite guarantee slot once before any comparison."""
    logger.debug("_guarantee_snapshot entry type=%s", type(value).__name__)
    if type(value) is not BoundedGuaranteeV2:
        return None
    try:
        result = (
            value.catalog_complete, value.train_prefix_minimal,
            value.train_matched, value.train_total,
            value.postfit_required_matched, value.postfit_required_total,
            value.all_required_matched, value.all_required_total,
            value.diagnostic_matched, value.diagnostic_total,
            value.resource_path_complete, value.general_completeness,
            value.general_minimality, value.novelty, value.superiority,
            value.evidence_accepted, value.promotion_ready,
            value.taxonomy_changed, value.proof_complete,
            value.guarantee_digest,
        )
    except AttributeError:
        logger.exception("_guarantee_snapshot deleted slot")
        return None
    logger.debug("_guarantee_snapshot exit")
    return result


def validate_trial_terminal(
    value: object,
) -> IsolatedObserverTrialResultV2 | None:
    """Validate the exact five-child terminal from one immutable snapshot."""
    logger.debug("validate_trial_terminal entry type=%s", type(value).__name__)
    if type(value) is not IsolatedObserverTrialResultV2:
        return None
    try:
        terminal = (
            value.schema, value.status, value.detail, value.limits_digest,
            value.report, value.report_digest,
        )
        report = terminal[4]
        if type(report) is not ObserverTrialReportV2:
            return None
        report_fields = (
            report.schema, report.report_digest, report.manifest_digest,
            report.subjects, report.guarantee,
        )
    except AttributeError:
        logger.exception("validate_trial_terminal deleted slot")
        return None
    subjects = report_fields[3]
    guarantee = _guarantee_snapshot(report_fields[4])
    if type(subjects) is not tuple or guarantee is None:
        return None
    if any(type(row) is not TrialSubjectResultV2 for row in subjects):
        return None
    try:
        subject_fields = tuple((row.role, row.cases) for row in subjects)
    except AttributeError:
        logger.exception("validate_trial_terminal malformed subject")
        return None
    if (
        any(type(role) is not TrialSubjectRoleV2 for role, _ in subject_fields)
        or any(type(cases) is not tuple for _, cases in subject_fields)
        or any(len(cases) != 10 for _, cases in subject_fields)
    ):
        return None
    terminal_types = (str, SynthesisStatus, str, str, ObserverTrialReportV2, str)
    if any(type(item) is not kind for item, kind in zip(terminal, terminal_types)):
        return None
    report_types = (str, str, str, tuple, BoundedGuaranteeV2)
    if any(type(item) is not kind for item, kind in zip(report_fields, report_types)):
        return None
    bool_indexes = (0, 1, 10, 11, 12, 13, 14, 15, 16, 17, 18)
    int_indexes = (2, 3, 4, 5, 6, 7, 8, 9)
    if (
        any(type(guarantee[index]) is not bool for index in bool_indexes)
        or any(type(guarantee[index]) is not int for index in int_indexes)
        or type(guarantee[19]) is not str
    ):
        return None
    expected = (
        True, True, 2, 2, 6, 6, 8, 8, 0, 2, True,
        False, False, False, False, False, False, False, False,
        EXPECTED_GUARANTEE_DIGEST,
    )
    valid = (
        terminal[:4] == (
            ISOLATED_TRIAL_RESULT_SCHEMA, SynthesisStatus.FOUND,
            "isolated-trial-complete", EXPECTED_UPSTREAM_TRIAL_LIMITS_DIGEST,
        )
        and terminal[5] == EXPECTED_TRIAL_REPORT_DIGEST
        and report_fields[:3] == (
            TRIAL_SCHEMA, EXPECTED_TRIAL_REPORT_DIGEST,
            EXPECTED_SUBJECT_MANIFEST_DIGEST,
        )
        and guarantee == expected
        and len(subjects) == 5
        and sum(role is TrialSubjectRoleV2.SYNTHESIZED for role, _ in subject_fields) == 1
    )
    logger.debug("validate_trial_terminal exit valid=%s", valid)
    return value if valid else None


def validate_receipt_terminal(value: object) -> bool:
    """Validate opaque receipt output from one captured exact terminal."""
    logger.debug("validate_receipt_terminal entry type=%s", type(value).__name__)
    if type(value) is not IsolatedObserverReceiptResultV2:
        return False
    try:
        fields = (
            value.schema, value.status, value.detail, value.limits_digest,
            value.trial_report_digest, value.bundle_bytes,
            value.bundle_sha256, value.bundle_digest,
        )
    except AttributeError:
        logger.exception("validate_receipt_terminal deleted slot")
        return False
    kinds = (str, SynthesisStatus, str, str, str, bytes, str, str)
    if any(type(item) is not kind for item, kind in zip(fields, kinds)):
        return False
    payload = fields[5]
    if type(payload) is not bytes:
        return False
    valid = (
        fields[:5] == (
            ISOLATED_RECEIPT_RESULT_SCHEMA, SynthesisStatus.FOUND,
            "receipt-complete", EXPECTED_UPSTREAM_TRIAL_LIMITS_DIGEST,
            EXPECTED_TRIAL_REPORT_DIGEST,
        )
        and len(payload) == EXPECTED_BUNDLE_BYTES
        and sha256(payload).hexdigest() == EXPECTED_BUNDLE_SHA256
        and fields[6:] == (EXPECTED_BUNDLE_SHA256, EXPECTED_BUNDLE_DIGEST)
    )
    logger.debug("validate_receipt_terminal exit valid=%s", valid)
    return valid


def incomplete_or_invalid(value: object, expected_type: type[object]) -> SynthesisStatus:
    """Map only an exact snapshotted INCOMPLETE terminal to INCOMPLETE."""
    logger.debug("incomplete_or_invalid entry type=%s", type(value).__name__)
    if type(value) is not expected_type:
        return SynthesisStatus.INVALID
    try:
        status = getattr(value, "status")
    except AttributeError:
        logger.exception("incomplete_or_invalid deleted status")
        return SynthesisStatus.INVALID
    result = (
        SynthesisStatus.INCOMPLETE
        if type(status) is SynthesisStatus and status is SynthesisStatus.INCOMPLETE
        else SynthesisStatus.INVALID
    )
    logger.debug("incomplete_or_invalid exit status=%s", result.value)
    return result
