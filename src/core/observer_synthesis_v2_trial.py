"""Bounded deterministic in-process R14.4 split/baseline trial facade."""
from __future__ import annotations

import logging

from .observer_synthesis_v2_baselines import build_trial_subject_manifest_v2
from .observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetValidationError,
    snapshot_budget_limits,
)
from .observer_synthesis_v2_corpus import DEFAULT_LOCKED_CORPUS
from .observer_synthesis_v2_grammar import enumerate_observer_grammar_v2
from .observer_synthesis_v2_trial_assembly import (
    BOUNDARY,
    EXPECTED_GUARANTEE_DIGEST,
    EXPECTED_TRIAL_REPORT_DIGEST,
    EXPECTED_WINNER_MATCHES,
    EXPECTED_WINNER_RELATIONS,
    GUARANTEE_SCHEMA,
    TRIAL_SCHEMA,
    assemble_locked_trial_report_v2,
    build_bounded_guarantee_v2,
    verify_winner_pins_v2,
)
from .observer_synthesis_v2_trial_execution import evaluate_trial_subject_v2
from .observer_synthesis_v2_trial_types import ObserverTrialReportV2
from .observer_synthesis_v2_trial_validation import (
    DEFAULT_LOCKED_WINNER_V2,
    InvalidTrialV2,
    snapshot_locked_corpus_for_trial_v2,
    snapshot_locked_winner_v2,
)

logger = logging.getLogger(__name__)

__all__ = (
    "BOUNDARY",
    "EXPECTED_GUARANTEE_DIGEST",
    "EXPECTED_TRIAL_REPORT_DIGEST",
    "EXPECTED_WINNER_MATCHES",
    "EXPECTED_WINNER_RELATIONS",
    "GUARANTEE_SCHEMA",
    "TRIAL_SCHEMA",
    "run_locked_trials_v2",
)

_evaluate_subject = evaluate_trial_subject_v2
_build_guarantee = build_bounded_guarantee_v2
_verify_winner_pins = verify_winner_pins_v2


def run_locked_trials_v2(
    winner: object = DEFAULT_LOCKED_WINNER_V2,
    corpus: object = DEFAULT_LOCKED_CORPUS,
    limits: object = DEFAULT_BUDGET_LIMITS,
) -> ObserverTrialReportV2:
    """Evaluate the exact winner and controls; cutoffs propagate to the worker."""
    logger.debug("run_locked_trials_v2 entry")
    trusted_winner = snapshot_locked_winner_v2(winner)
    trusted_corpus = snapshot_locked_corpus_for_trial_v2(corpus)
    try:
        trusted_limits = snapshot_budget_limits(limits)
    except BudgetValidationError as exc:
        logger.error("run_locked_trials_v2 invalid limits")
        raise InvalidTrialV2("invalid-trial-limits") from exc
    manifest = build_trial_subject_manifest_v2(trusted_winner)
    try:
        subjects = tuple(
            evaluate_trial_subject_v2(row, trusted_corpus, trusted_limits)
            for row in manifest.subjects
        )
    except BudgetValidationError as exc:
        logger.error("run_locked_trials_v2 invalid runtime budget")
        raise InvalidTrialV2("invalid-trial-budget-runtime") from exc
    result = assemble_locked_trial_report_v2(
        trusted_winner,
        trusted_corpus,
        manifest,
        subjects,
        enumerate_observer_grammar_v2,
    )
    logger.debug("run_locked_trials_v2 exit digest=%s", result.report_digest[:12])
    return result
