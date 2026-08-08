"""Canonical retained/report data for deterministic R14.4 trials."""
from __future__ import annotations

import logging

from .observer_synthesis_v2_trial_types import (
    BoundedGuaranteeV2,
    TrialCaseResultV2,
    TrialSplitSummaryV2,
    TrialSubjectResultV2,
    TrialSubjectV2,
)

logger = logging.getLogger(__name__)


def case_result_data_v2(row: TrialCaseResultV2) -> dict[str, object]:
    logger.debug("case_result_data_v2 entry case_id=%d", row.case_id)
    result: dict[str, object] = {
        "actual": row.actual.value,
        "case_digest": row.case_digest,
        "case_id": row.case_id,
        "expected": row.expected.value,
        "matched": row.matched,
        "outcome_digest": row.outcome_digest,
        "required_for_winner": row.required_for_winner,
        "split": row.split.value,
    }
    logger.debug("case_result_data_v2 exit case_id=%d", row.case_id)
    return result


def split_summary_data_v2(row: TrialSplitSummaryV2) -> dict[str, object]:
    logger.debug("split_summary_data_v2 entry split=%s", row.split.value)
    result: dict[str, object] = {
        "diagnostic_matched": row.diagnostic_matched,
        "diagnostic_total": row.diagnostic_total,
        "required_matched": row.required_matched,
        "required_total": row.required_total,
        "split": row.split.value,
        "total": row.total,
    }
    logger.debug("split_summary_data_v2 exit split=%s", row.split.value)
    return result


def retained_subject_data_v2(
    subject: TrialSubjectV2,
    cases: tuple[TrialCaseResultV2, ...],
    splits: tuple[TrialSplitSummaryV2, ...],
) -> dict[str, object]:
    """Data atomically precharged before a subject result is retained."""
    logger.debug(
        "retained_subject_data_v2 entry subject_id=%s cases=%d",
        subject.subject_id,
        len(cases),
    )
    result: dict[str, object] = {
        "cases": [case_result_data_v2(row) for row in cases],
        "observer_digest": subject.digest,
        "schema": "veyra.observer-synthesis-v2.retained-trial.r14.4.v1",
        "splits": [split_summary_data_v2(row) for row in splits],
    }
    logger.debug("retained_subject_data_v2 exit subject_id=%s", subject.subject_id)
    return result


def guarantee_data_v2(report: BoundedGuaranteeV2) -> dict[str, object]:
    logger.debug("guarantee_data_v2 entry")
    result: dict[str, object] = {
        "all_required": [report.all_required_matched, report.all_required_total],
        "boundary": report.boundary,
        "catalog_complete": report.catalog_complete,
        "diagnostic": [report.diagnostic_matched, report.diagnostic_total],
        "evidence_accepted": report.evidence_accepted,
        "general_completeness": report.general_completeness,
        "general_minimality": report.general_minimality,
        "novelty": report.novelty,
        "postfit_required": [
            report.postfit_required_matched,
            report.postfit_required_total,
        ],
        "promotion_ready": report.promotion_ready,
        "proof_complete": report.proof_complete,
        "resource_path_complete": report.resource_path_complete,
        "superiority": report.superiority,
        "taxonomy_changed": report.taxonomy_changed,
        "train": [report.train_matched, report.train_total],
        "train_prefix_minimal": report.train_prefix_minimal,
    }
    logger.debug("guarantee_data_v2 exit")
    return result


def subject_result_data_v2(report: TrialSubjectResultV2) -> dict[str, object]:
    logger.debug("subject_result_data_v2 entry subject_id=%s", report.subject_id)
    result: dict[str, object] = {
        "accounting": {
            "candidates": report.accounting.candidates,
            "canonical_bytes": report.accounting.canonical_bytes,
            "cutoff": report.accounting.cutoff,
            "evaluations": report.accounting.evaluations,
            "retained_output_bytes": report.accounting.retained_output_bytes,
        },
        "diagnostic": [report.diagnostic_matched, report.diagnostic_total],
        "observer_digest": report.observer_digest,
        "required": [report.required_matched, report.required_total],
        "retained_digest": report.retained_digest,
        "role": report.role.value,
        "subject_id": report.subject_id,
    }
    logger.debug("subject_result_data_v2 exit subject_id=%s", report.subject_id)
    return result
