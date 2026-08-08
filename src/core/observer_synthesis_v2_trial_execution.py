"""Fresh-ledger subject execution for bounded R14.4 trials."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_budget import BudgetLedger, BudgetLimits
from .observer_synthesis_v2_corpus import LockedObserverCorpusV2
from .observer_synthesis_v2_evaluation import EvaluationCacheV2, evaluate_observer_case_v2
from .observer_synthesis_v2_protocol import CaseEvaluationV2, SplitId
from .observer_synthesis_v2_trial_codec import retained_subject_data_v2
from .observer_synthesis_v2_trial_types import (
    TrialAccountingV2,
    TrialCaseResultV2,
    TrialSplitSummaryV2,
    TrialSubjectResultV2,
    TrialSubjectV2,
)
from .observer_synthesis_v2_trial_provenance import _brand_trial_subject_v2
from .observer_synthesis_v2_trial_case_provenance import _brand_trial_case_v2
from .observer_synthesis_v2_trial_validation import InvalidTrialV2
from .proof_core_codec import canonical_json

logger = logging.getLogger(__name__)


def split_summaries_v2(
    cases: tuple[TrialCaseResultV2, ...],
) -> tuple[TrialSplitSummaryV2, ...]:
    """Summarize the four exact split IDs without reranking cases."""
    logger.debug("split_summaries_v2 entry cases=%d", len(cases))
    rows = []
    for split in SplitId:
        selected = tuple(row for row in cases if row.split is split)
        required = tuple(row for row in selected if row.required_for_winner)
        diagnostic = tuple(row for row in selected if not row.required_for_winner)
        rows.append(
            TrialSplitSummaryV2(
                split,
                len(selected),
                len(required),
                sum(row.matched for row in required),
                len(diagnostic),
                sum(row.matched for row in diagnostic),
            )
        )
    result = tuple(rows)
    logger.debug("split_summaries_v2 exit splits=%d", len(result))
    return result


def evaluate_trial_subject_v2(
    subject: TrialSubjectV2,
    corpus: LockedObserverCorpusV2,
    limits: BudgetLimits,
) -> TrialSubjectResultV2:
    """Evaluate one predeclared subject with a fresh ledger and cache."""
    logger.debug("evaluate_trial_subject_v2 entry subject_id=%s", subject.subject_id)
    subject_index = _subject_index_v2(subject.subject_id)
    ledger = BudgetLedger(limits)
    cache = EvaluationCacheV2()
    ledger.charge_candidate(len(subject.canonical))
    temporary: list[TrialCaseResultV2] = []
    for case_index, case in enumerate(corpus.cases):
        evaluation = evaluate_observer_case_v2(subject.observer, case, ledger, cache)
        if type(evaluation) is not CaseEvaluationV2:
            logger.error(
                "evaluate_trial_subject_v2 invalid subject_id=%s case_id=%d",
                subject.subject_id,
                case.case_id,
            )
            raise InvalidTrialV2("invalid-trial-evaluation")
        temporary.append(
            _brand_trial_case_v2(
                TrialCaseResultV2(
                case.case_id,
                case.case_digest,
                case.split,
                case.required_for_winner,
                evaluation.expected,
                evaluation.actual,
                evaluation.matched,
                evaluation.outcome_digest,
                ),
                subject_index,
                case_index,
            )
        )
    cases = tuple(temporary)
    splits = split_summaries_v2(cases)
    retained = canonical_json(
        retained_subject_data_v2(subject, cases, splits)
    ).encode("utf-8")
    retained_digest = sha256(
        b"veyra.observer-synthesis-v2.retained-trial.r14.4.v1\0" + retained
    ).hexdigest()
    ledger.charge_output(len(retained))
    snapshot = ledger.snapshot()
    required = tuple(row for row in cases if row.required_for_winner)
    diagnostics = tuple(row for row in cases if not row.required_for_winner)
    provisional = TrialSubjectResultV2(
        subject.subject_id,
        subject.role,
        subject.digest,
        cases,
        splits,
        sum(row.matched for row in required),
        len(required),
        sum(row.matched for row in diagnostics),
        len(diagnostics),
        TrialAccountingV2(
            snapshot.candidates,
            snapshot.canonical_bytes,
            snapshot.evaluations,
            snapshot.transcript_output_bytes,
            snapshot.cutoff_reason is not None,
        ),
        retained_digest,
    )
    result = _brand_trial_subject_v2(provisional, subject_index)
    logger.debug(
        "evaluate_trial_subject_v2 exit subject_id=%s required=%d/%d",
        subject.subject_id,
        result.required_matched,
        result.required_total,
    )
    return result


def _subject_index_v2(subject_id: str) -> int:
    """Recover the fixed manifest position without importing the manifest."""
    logger.debug("_subject_index_v2 entry subject_id=%s", subject_id)
    identifiers = (
        "synthesized-winner",
        "baseline-input",
        "baseline-tail-input",
        "baseline-crest-input",
        "baseline-pair-input-input",
    )
    try:
        result = identifiers.index(subject_id)
    except ValueError as exc:
        logger.error("_subject_index_v2 unknown subject_id=%s", subject_id)
        raise InvalidTrialV2("invalid-trial-subject-id") from exc
    logger.debug("_subject_index_v2 exit index=%d", result)
    return result
