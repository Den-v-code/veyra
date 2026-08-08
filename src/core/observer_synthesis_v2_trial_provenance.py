"""Exact run-local brands for prevalidated R14 trial DTO boundaries."""
from __future__ import annotations

from dataclasses import dataclass, replace
import logging

from .observer_synthesis_v2_trial_codec import guarantee_data_v2
from .observer_synthesis_v2_trial_case_provenance import (
    require_trial_case_brand_v2,
)
from .observer_synthesis_v2_trial_types import (
    BoundedGuaranteeV2,
    ObserverTrialReportV2,
    TrialAccountingV2,
    TrialCaseResultV2,
    TrialSplitSummaryV2,
    TrialSubjectResultV2,
    TrialSubjectRoleV2,
)
from .observer_synthesis_v2_protocol import ExpectedRelation, SplitId
from .observer_synthesis_v2_trial_worker_codec import (
    full_subject_data_v2,
    trial_subject_payload_digest_v2,
)
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

_SUBJECT_SEAL = object()
_REPORT_SEAL = object()
_REPORT_BRAND_SCHEMA = "veyra.observer-synthesis-v2.trial-brand.r14.5c.v1"


@dataclass(frozen=True, slots=True)
class _SubjectBrandV2:
    """Unserialized validator provenance bound to one subject position."""

    seal: object
    subject_index: int
    payload_digest: str


@dataclass(frozen=True, slots=True)
class _ReportBrandV2:
    """Unserialized assembly provenance bound to all five full subjects."""

    seal: object
    binding_digest: str


def _subject_shape_v2(subject: object) -> bool:
    """Reject hostile/deleted fields before canonical serializers touch them."""
    logger.debug("_subject_shape_v2 entry type=%s", type(subject).__name__)
    if type(subject) is not TrialSubjectResultV2:
        return False
    try:
        scalar_ok = (
            type(subject.subject_id) is str
            and type(subject.role) is TrialSubjectRoleV2
            and type(subject.observer_digest) is str
            and type(subject.cases) is tuple
            and type(subject.splits) is tuple
            and type(subject.required_matched) is int
            and type(subject.required_total) is int
            and type(subject.diagnostic_matched) is int
            and type(subject.diagnostic_total) is int
            and type(subject.accounting) is TrialAccountingV2
            and type(subject.retained_digest) is str
        )
        case_shapes_ok = all(
            type(row) is TrialCaseResultV2
            and type(row.case_id) is int
            and type(row.case_digest) is str
            and type(row.split) is SplitId
            and type(row.required_for_winner) is bool
            and type(row.expected) is ExpectedRelation
            and type(row.actual) is ExpectedRelation
            and type(row.matched) is bool
            and type(row.outcome_digest) is str
            for row in subject.cases
        )
        splits_ok = all(
            type(row) is TrialSplitSummaryV2
            and type(row.split) is SplitId
            and all(
                type(value) is int
                for value in (
                    row.total,
                    row.required_total,
                    row.required_matched,
                    row.diagnostic_total,
                    row.diagnostic_matched,
                )
            )
            for row in subject.splits
        )
        accounting = subject.accounting
        accounting_ok = (
            type(accounting.candidates) is int
            and type(accounting.canonical_bytes) is int
            and type(accounting.evaluations) is int
            and type(accounting.retained_output_bytes) is int
            and type(accounting.cutoff) is bool
        )
        result = scalar_ok and case_shapes_ok and splits_ok and accounting_ok
    except AttributeError:
        logger.exception("_subject_shape_v2 deleted field")
        result = False
    logger.debug("_subject_shape_v2 exit valid=%s", result)
    return result


def _subject_payload_digest_v2(subject: TrialSubjectResultV2) -> str:
    logger.debug("_subject_payload_digest_v2 entry")
    if not _subject_shape_v2(subject):
        logger.error("_subject_payload_digest_v2 invalid subject")
        raise ValueError("invalid-trial-subject-shape")
    result = trial_subject_payload_digest_v2(full_subject_data_v2(subject))
    logger.debug("_subject_payload_digest_v2 exit digest=%s", result[:12])
    return result


def _brand_trial_subject_v2(
    subject: TrialSubjectResultV2,
    subject_index: int,
) -> TrialSubjectResultV2:
    """Brand one freshly evaluated or fully parsed exact subject."""
    logger.debug("_brand_trial_subject_v2 entry index=%r", subject_index)
    if not _subject_shape_v2(subject) or type(subject_index) is not int:
        logger.error("_brand_trial_subject_v2 invalid source")
        raise ValueError("invalid-trial-subject-brand-source")
    for case_index, case in enumerate(subject.cases):
        require_trial_case_brand_v2(case, subject_index, case_index)
    brand = _SubjectBrandV2(
        _SUBJECT_SEAL,
        subject_index,
        _subject_payload_digest_v2(subject),
    )
    result = replace(subject, provenance=brand)
    logger.debug("_brand_trial_subject_v2 exit digest=%s", brand.payload_digest[:12])
    return result


def require_trial_subject_brand_v2(
    subject: object,
    subject_index: int,
) -> TrialSubjectResultV2:
    """Reject copied official digests after any subject/case transplantation."""
    logger.debug("require_trial_subject_brand_v2 entry index=%r", subject_index)
    if type(subject) is not TrialSubjectResultV2 or type(subject_index) is not int:
        logger.error("require_trial_subject_brand_v2 invalid source")
        raise ValueError("invalid-trial-subject-provenance")
    try:
        brand = subject.provenance
        valid = (
            type(brand) is _SubjectBrandV2
            and brand.seal is _SUBJECT_SEAL
            and brand.subject_index == subject_index
            and type(brand.payload_digest) is str
            and brand.payload_digest == _subject_payload_digest_v2(subject)
        )
        if valid:
            for case_index, case in enumerate(subject.cases):
                require_trial_case_brand_v2(case, subject_index, case_index)
    except (AttributeError, TypeError, ValueError):
        logger.exception("require_trial_subject_brand_v2 malformed subject")
        valid = False
    if not valid:
        logger.error("require_trial_subject_brand_v2 provenance mismatch")
        raise ValueError("invalid-trial-subject-provenance")
    logger.debug("require_trial_subject_brand_v2 exit")
    return subject


def _report_brand_data_v2(report: ObserverTrialReportV2) -> dict[str, object]:
    logger.debug("_report_brand_data_v2 entry")
    if (
        type(report.schema) is not str
        or type(report.winner_digest) is not str
        or type(report.corpus_digest) is not str
        or type(report.manifest_digest) is not str
        or type(report.subjects) is not tuple
        or type(report.guarantee) is not BoundedGuaranteeV2
        or type(report.report_digest) is not str
        or type(report.boundary) is not str
    ):
        logger.error("_report_brand_data_v2 invalid report shape")
        raise ValueError("invalid-trial-report-shape")
    guarantee = report.guarantee
    boolean_fields = (
        guarantee.catalog_complete,
        guarantee.train_prefix_minimal,
        guarantee.resource_path_complete,
        guarantee.general_completeness,
        guarantee.general_minimality,
        guarantee.novelty,
        guarantee.superiority,
        guarantee.evidence_accepted,
        guarantee.promotion_ready,
        guarantee.taxonomy_changed,
        guarantee.proof_complete,
    )
    integer_fields = (
        guarantee.train_matched,
        guarantee.train_total,
        guarantee.postfit_required_matched,
        guarantee.postfit_required_total,
        guarantee.all_required_matched,
        guarantee.all_required_total,
        guarantee.diagnostic_matched,
        guarantee.diagnostic_total,
    )
    if (
        any(type(value) is not bool for value in boolean_fields)
        or any(type(value) is not int for value in integer_fields)
        or type(guarantee.guarantee_digest) is not str
        or type(guarantee.boundary) is not str
    ):
        logger.error("_report_brand_data_v2 invalid guarantee shape")
        raise ValueError("invalid-trial-guarantee-shape")
    subject_digests = tuple(
        _subject_payload_digest_v2(row) for row in report.subjects
    )
    result: dict[str, object] = {
        "boundary": report.boundary,
        "corpus_digest": report.corpus_digest,
        "guarantee": {
            **guarantee_data_v2(report.guarantee),
            "guarantee_digest": report.guarantee.guarantee_digest,
        },
        "manifest_digest": report.manifest_digest,
        "report_digest": report.report_digest,
        "schema": report.schema,
        "subject_payload_digests": list(subject_digests),
        "winner_digest": report.winner_digest,
    }
    logger.debug("_report_brand_data_v2 exit subjects=%d", len(subject_digests))
    return result


def _brand_trial_report_v2(report: ObserverTrialReportV2) -> ObserverTrialReportV2:
    """Seal a report only after all five exact subject brands are present."""
    logger.debug("_brand_trial_report_v2 entry")
    if type(report) is not ObserverTrialReportV2 or type(report.subjects) is not tuple:
        logger.error("_brand_trial_report_v2 invalid source")
        raise ValueError("invalid-trial-report-brand-source")
    for index, subject in enumerate(report.subjects):
        require_trial_subject_brand_v2(subject, index)
    brand = _ReportBrandV2(
        _REPORT_SEAL,
        digest_data(_report_brand_data_v2(report), _REPORT_BRAND_SCHEMA),
    )
    result = replace(report, provenance=brand)
    logger.debug("_brand_trial_report_v2 exit digest=%s", brand.binding_digest[:12])
    return result


def require_trial_report_brand_v2(report: object) -> ObserverTrialReportV2:
    """Require exact assembly provenance and unchanged full subject content."""
    logger.debug("require_trial_report_brand_v2 entry type=%s", type(report).__name__)
    if type(report) is not ObserverTrialReportV2 or type(report.subjects) is not tuple:
        logger.error("require_trial_report_brand_v2 invalid source")
        raise ValueError("invalid-trial-report-provenance")
    try:
        for index, subject in enumerate(report.subjects):
            require_trial_subject_brand_v2(subject, index)
        brand = report.provenance
        valid = (
            type(brand) is _ReportBrandV2
            and brand.seal is _REPORT_SEAL
            and type(brand.binding_digest) is str
            and brand.binding_digest
            == digest_data(_report_brand_data_v2(report), _REPORT_BRAND_SCHEMA)
        )
    except (AttributeError, TypeError, ValueError):
        logger.exception("require_trial_report_brand_v2 malformed report")
        valid = False
    if not valid:
        logger.error("require_trial_report_brand_v2 provenance mismatch")
        raise ValueError("invalid-trial-report-provenance")
    logger.debug("require_trial_report_brand_v2 exit")
    return report
