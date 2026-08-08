"""Validation, evaluation, transcript, and terminal helpers for R14.3b."""
from __future__ import annotations

import logging

from .observer_synthesis_v2_budget import BudgetLedger
from .observer_synthesis_v2_cegis_codec import (
    build_trace_step_v2,
    trace_digest_v2,
    trace_step_bytes_v2,
)
from .observer_synthesis_v2_cegis_types import (
    CegisEventV2,
    CegisTerminalReasonV2,
    CegisTraceStepV2,
    LockedObserverWinnerV2,
    ObserverCegisReportV2,
)
from .observer_synthesis_v2_cegis_validation import reject_cegis_v2
from .observer_synthesis_v2_evaluation import (
    EvaluationCacheV2,
    evaluate_observer_case_v2,
)
from .observer_synthesis_v2_protocol import (
    CaseEvaluationV2,
    ObserverCaseV2,
)
from .observer_synthesis_v2_types import (
    ObserverCandidateV2,
    SynthesisStatus,
)

logger = logging.getLogger(__name__)

BOUNDARY = (
    "complete or minimal only for the exact 1,565-row R14.1 grammar and the "
    "explicit ordered TRAIN obligations under the declared ledger; no "
    "holdout, unseen, adversarial, general-synthesis, or promotion claim"
)


def append_cegis_step_v2(
    trace: list[CegisTraceStepV2],
    ledger: BudgetLedger,
    limits_digest: str,
    event: CegisEventV2,
    ordinal: int,
    candidate: ObserverCandidateV2,
    counterexample: ObserverCaseV2 | None = None,
    retained_extra: int = 0,
) -> None:
    logger.debug(
        "append_cegis_step_v2 entry event=%s ordinal=%d",
        event.value,
        ordinal,
    )
    snapshot = ledger.snapshot()
    case_id = None if counterexample is None else counterexample.case_id
    case_digest = None if counterexample is None else counterexample.case_digest
    canonical = trace_step_bytes_v2(
        len(trace) + 1,
        event,
        ordinal,
        candidate.digest,
        case_id,
        case_digest,
        snapshot,
        limits_digest,
    )
    if type(retained_extra) is not int or retained_extra < 0:
        reject_cegis_v2("invalid-trace-retained-extra")
    ledger.charge_output(len(canonical) + retained_extra)
    trace.append(
        build_trace_step_v2(
            len(trace) + 1,
            event,
            ordinal,
            candidate.digest,
            case_id,
            case_digest,
            snapshot,
            limits_digest,
            canonical,
        )
    )
    logger.info(
        "R14.3b trace state=retained event=%s sequence=%d",
        event.value,
        len(trace),
    )
    logger.debug("append_cegis_step_v2 exit")


def evaluate_cegis_case_v2(
    candidate: ObserverCandidateV2,
    case: ObserverCaseV2,
    ledger: BudgetLedger,
    cache: EvaluationCacheV2,
) -> bool:
    logger.debug(
        "evaluate_cegis_case_v2 entry candidate=%s case_id=%d",
        candidate.digest[:12],
        case.case_id,
    )
    result = evaluate_observer_case_v2(candidate.observer, case, ledger, cache)
    if type(result) is not CaseEvaluationV2:
        reject_cegis_v2(f"invalid-case-evaluation:{result.reason.value}")
    logger.debug("evaluate_cegis_case_v2 exit matched=%s", result.matched)
    return result.matched


def build_cegis_report_v2(
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
    logger.debug(
        "build_cegis_report_v2 entry status=%s detail=%s",
        status.value,
        detail,
    )
    locked_trace = tuple(trace)
    result = ObserverCegisReportV2(
        status,
        reason,
        detail,
        catalog_digest,
        training_digest,
        limits_digest,
        locked_trace,
        trace_digest_v2(locked_trace),
        winner,
        traversed,
        tuple(case.case_id for case in active),
        None if ledger is None else ledger.snapshot(),
        BOUNDARY,
    )
    logger.info(
        "R14.3b terminal status=%s detail=%s traversed=%d",
        status.value,
        detail,
        traversed,
    )
    logger.debug("build_cegis_report_v2 exit")
    return result
