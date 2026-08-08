"""Deterministic train-only counterexample-guided synthesis for R14.3b."""
from __future__ import annotations

import logging

from .observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetLedger,
    BudgetLimitExceeded,
    BudgetValidationError,
    snapshot_budget_limits,
)
from .observer_synthesis_v2_cegis_codec import (
    limits_digest_v2,
    training_digest_v2,
)
from .observer_synthesis_v2_cegis_support import (
    append_cegis_step_v2,
    build_cegis_report_v2,
    evaluate_cegis_case_v2,
)
from .observer_synthesis_v2_cegis_validation import (
    InvalidCegisV2,
    reject_cegis_v2,
    validate_cegis_catalog_v2,
    validate_cegis_train_cases_v2,
)
from .observer_synthesis_v2_cegis_types import (
    CegisEventV2,
    CegisTerminalReasonV2,
    CegisTraceStepV2,
    LockedObserverWinnerV2,
    ObserverCegisReportV2,
)
from .observer_synthesis_v2_evaluation import EvaluationCacheV2
from .observer_synthesis_v2_grammar import EXPECTED_DEFAULT_CANDIDATES
from .observer_synthesis_v2_protocol import (
    ObserverCaseV2,
    ObserverSynthesisProtocolError,
)
from .observer_synthesis_v2_types import ObserverCandidateV2, SynthesisStatus

logger = logging.getLogger(__name__)


def _terminal(
    status: SynthesisStatus,
    reason: CegisTerminalReasonV2,
    detail: str,
    catalog_digest: str,
    training_digest: str,
    limits_digest: str,
    trace: list[CegisTraceStepV2],
    winner: LockedObserverWinnerV2 | None,
    traversed: int,
    active: list[ObserverCaseV2],
    ledger: BudgetLedger | None,
) -> ObserverCegisReportV2:
    logger.debug("_terminal entry status=%s", status.value)
    result = build_cegis_report_v2(
        status,
        reason,
        detail,
        catalog_digest,
        training_digest,
        limits_digest,
        trace,
        winner,
        traversed,
        active,
        ledger,
    )
    logger.debug("_terminal exit status=%s", result.status.value)
    return result


def fit_observer_cegis_v2(
    catalog: object,
    train_cases: object,
    limits: object = DEFAULT_BUDGET_LIMITS,
    *,
    precharged_ledger: object = None,
) -> ObserverCegisReportV2:
    """Fit only explicit TRAIN rows using the exact fully precharged catalog."""
    logger.debug("fit_observer_cegis_v2 entry")
    ledger: BudgetLedger | None = None
    trace: list[CegisTraceStepV2] = []
    active: list[ObserverCaseV2] = []
    traversed = 0
    catalog_digest = ""
    training_digest = ""
    limit_digest = ""
    try:
        valid_limits = snapshot_budget_limits(limits)
        limit_digest = limits_digest_v2(valid_limits)
        valid_catalog = (
            validate_cegis_catalog_v2(catalog)
            if precharged_ledger is None
            else validate_cegis_catalog_v2(catalog, precharged_ledger)
        )
        catalog_digest = valid_catalog.catalog_digest
        train = validate_cegis_train_cases_v2(train_cases)
        training_digest = training_digest_v2(
            tuple(case.case_digest for case in train)
        )
        if precharged_ledger is None:
            ledger = BudgetLedger(valid_limits)
            for candidate in valid_catalog.candidates:
                ledger.charge_candidate(len(candidate.canonical))
        elif type(precharged_ledger) is BudgetLedger:
            ledger = precharged_ledger
            charged = ledger.snapshot()
            if (
                charged.limits != valid_limits
                or charged.candidates != len(valid_catalog.candidates)
                or charged.canonical_bytes != valid_catalog.canonical_bytes
                or charged.evaluations != 0
                or charged.transcript_output_bytes != 0
                or charged.cutoff_reason is not None
            ):
                reject_cegis_v2("invalid-precharged-catalog-ledger")
            logger.info(
                "fit_observer_cegis_v2 reused precharged catalog candidates=%d",
                charged.candidates,
            )
        else:
            reject_cegis_v2("invalid-precharged-catalog-ledger")
        active.append(train[0])
        append_cegis_step_v2(
            trace,
            ledger,
            limit_digest,
            CegisEventV2.SEED,
            0,
            valid_catalog.candidates[0],
        )
        cache = EvaluationCacheV2()
        while True:
            viable: tuple[int, ObserverCandidateV2] | None = None
            traversed = 0
            for ordinal, candidate in enumerate(valid_catalog.candidates):
                traversed += 1
                if all(
                    evaluate_cegis_case_v2(candidate, case, ledger, cache)
                    for case in active
                ):
                    viable = ordinal, candidate
                    break
            if viable is None:
                if traversed != EXPECTED_DEFAULT_CANDIDATES:
                    reject_cegis_v2("nonexact-exhausted-traversal")
                return _terminal(
                    SynthesisStatus.EXHAUSTED,
                    CegisTerminalReasonV2.COMPLETE_TRAVERSAL,
                    "exact-catalog-exhausted",
                    catalog_digest,
                    training_digest,
                    limit_digest,
                    trace,
                    None,
                    traversed,
                    active,
                    ledger,
                )
            ordinal, candidate = viable
            active_ids = {case.case_id for case in active}
            counterexample = next(
                (
                    case
                    for case in train
                    if case.case_id not in active_ids
                    and not evaluate_cegis_case_v2(
                        candidate,
                        case,
                        ledger,
                        cache,
                    )
                ),
                None,
            )
            if counterexample is not None:
                append_cegis_step_v2(
                    trace,
                    ledger,
                    limit_digest,
                    CegisEventV2.COUNTEREXAMPLE,
                    ordinal,
                    candidate,
                    counterexample,
                )
                active.append(counterexample)
                continue
            append_cegis_step_v2(
                trace,
                ledger,
                limit_digest,
                CegisEventV2.WINNER,
                ordinal,
                candidate,
                retained_extra=len(candidate.canonical),
            )
            winner = LockedObserverWinnerV2(
                ordinal,
                candidate.cost,
                candidate.depth,
                candidate.canonical,
                candidate.digest,
            )
            return _terminal(
                SynthesisStatus.FOUND,
                CegisTerminalReasonV2.FOUND,
                "first-train-satisfying-candidate",
                catalog_digest,
                training_digest,
                limit_digest,
                trace,
                winner,
                traversed,
                active,
                ledger,
            )
    except BudgetLimitExceeded as exc:
        return _terminal(
            SynthesisStatus.INCOMPLETE,
            CegisTerminalReasonV2.BUDGET_CUTOFF,
            exc.reason.value,
            catalog_digest,
            training_digest,
            limit_digest,
            trace,
            None,
            traversed,
            active,
            ledger,
        )
    except InvalidCegisV2 as exc:
        return _terminal(
            SynthesisStatus.INVALID,
            CegisTerminalReasonV2.INVALID_INPUT,
            exc.reason,
            catalog_digest,
            training_digest,
            limit_digest,
            trace,
            None,
            traversed,
            active,
            ledger,
        )
    except BudgetValidationError:
        return _terminal(
            SynthesisStatus.INVALID,
            CegisTerminalReasonV2.INVALID_INPUT,
            "invalid-budget-configuration",
            catalog_digest,
            training_digest,
            limit_digest,
            trace,
            None,
            traversed,
            active,
            ledger,
        )
    except ObserverSynthesisProtocolError:
        return _terminal(
            SynthesisStatus.INVALID,
            CegisTerminalReasonV2.INVALID_INPUT,
            "invalid-train-protocol",
            catalog_digest,
            training_digest,
            limit_digest,
            trace,
            None,
            traversed,
            active,
            ledger,
        )
