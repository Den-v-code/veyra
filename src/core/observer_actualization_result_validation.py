"""Hostile-safe fresh result validation for finite P1-E4 judgments."""

from __future__ import annotations

import logging

from .observer_actualization_graph import hex_digest, identifier, reject
from .observer_actualization_runtime import historical_actualization_judgment
from .observer_actualization_types import (
    ActualizationOperationStatus, ActualizationStatus, ConsciousnessStatus,
    CounterfactualClass, CounterfactualEvidence, CounterfactualOutcome,
    HistoricalActualization, HistoricalActualizationJudgment,
    HistoricalObserverSource, PhysicalInstantiation, ActualizationResourcePolicy,
)

logger = logging.getLogger(__name__)


def _result_envelope(
    source: HistoricalObserverSource, value: HistoricalActualizationJudgment,
) -> tuple:
    """Exact-type and shallow-size gate with no semantic replay or equality."""
    logger.debug("actualization result envelope entry")
    if type(value) is not HistoricalActualizationJudgment:
        reject("historical-actualization-judgment-must-be-exact")
    try:
        digests = (
            value.source_digest, value.birth_core_digest,
            value.historical_token_id, value.history_digest,
            value.doctrine_digest, value.scope_digest,
            value.actualization_judgment_digest,
        )
        past, future, rows = (
            value.past_event_ids, value.future_event_ids,
            value.counterfactual_evidence,
        )
        statuses = (
            value.oep_role, value.prior_construction, value.birth_event,
            value.target_independence, value.post_birth_efficacy,
        )
        tail = (
            value.historical_actualization, value.operation_status,
            value.physical_instantiation, value.consciousness, value.scope,
        )
    except AttributeError:
        reject("historical-actualization-judgment-fields-missing")
    if type(source) is not HistoricalObserverSource:
        reject("historical-observer-source-must-be-exact")
    try:
        policy = source.policy
    except AttributeError:
        reject("historical-observer-source-fields-missing")
    if type(policy) is not ActualizationResourcePolicy:
        reject("actualization-policy-must-be-exact")
    try:
        max_events, max_cases = policy.max_events, policy.max_counterfactuals
    except AttributeError:
        reject("actualization-policy-fields-missing")
    if (
        type(max_events) is not int or type(max_cases) is not int
        or type(past) is not tuple or type(future) is not tuple
        or type(rows) is not tuple
        or len(past) > max_events or len(future) > max_events
        or len(rows) > max_cases
        or any(type(item) is not str for item in digests)
        or any(type(item) is not ActualizationStatus for item in statuses)
        or type(tail[0]) is not HistoricalActualization
        or type(tail[1]) is not ActualizationOperationStatus
        or type(tail[2]) is not PhysicalInstantiation
        or type(tail[3]) is not ConsciousnessStatus
        or type(tail[4]) is not str
    ):
        reject("historical-actualization-judgment-envelope")
    if (
        any(type(item) is not str for item in past)
        or any(type(item) is not str for item in future)
        or any(type(item) is not CounterfactualEvidence for item in rows)
    ):
        reject("historical-actualization-judgment-envelope-element-type")
    if len(rows) != 3:
        reject("historical-actualization-judgment-envelope")
    for item in digests:
        hex_digest(item, "historical-actualization-result-digest")
    if (
        tail[1] is not ActualizationOperationStatus.JUDGED
        or tail[2] is not PhysicalInstantiation.NOT_ESTABLISHED
        or tail[3] is not ConsciousnessStatus.NOT_CLAIMED
        or tail[4] != "finite-history-relative-observer-actualization-only"
    ):
        reject("historical-actualization-judgment-envelope")
    logger.debug("actualization result envelope exit")
    return digests, past, future, rows, statuses, tail


def _counterfactual(
    value: CounterfactualEvidence, expected: CounterfactualEvidence,
) -> CounterfactualEvidence:
    logger.debug("validate counterfactual evidence entry")
    if type(value) is not CounterfactualEvidence:
        reject("counterfactual-evidence-must-be-exact")
    try:
        case_id, kind, outcome, evidence = (
            value.case_id, value.kind, value.outcome, value.evidence_digest,
        )
    except AttributeError:
        reject("counterfactual-evidence-fields-missing")
    case_id = identifier(case_id, "counterfactual-evidence-id")
    evidence = hex_digest(evidence, "counterfactual-evidence-digest")
    if (
        type(kind) is not CounterfactualClass
        or type(outcome) is not CounterfactualOutcome
        or case_id != expected.case_id or kind is not expected.kind
        or outcome is not expected.outcome or evidence != expected.evidence_digest
    ):
        reject("counterfactual-evidence-drift")
    result = CounterfactualEvidence(case_id, kind, outcome, evidence)
    logger.debug("validate counterfactual evidence exit")
    return result


def validate_actualization_result(
    source: HistoricalObserverSource, value: HistoricalActualizationJudgment,
) -> HistoricalActualizationJudgment:
    """Replay raw source evidence and return a fresh exact result."""
    logger.debug("validate_actualization_result entry")
    digests, past, future, rows, statuses, tail = _result_envelope(source, value)
    historical, operation, physical, consciousness, scope = tail
    expected = historical_actualization_judgment(source)
    expected_digests = (
        expected.source_digest, expected.birth_core_digest,
        expected.historical_token_id, expected.history_digest,
        expected.doctrine_digest, expected.scope_digest,
        expected.actualization_judgment_digest,
    )
    if (
        digests != expected_digests
        or type(past) is not tuple or len(past) != len(expected.past_event_ids)
        or type(future) is not tuple or len(future) != len(expected.future_event_ids)
        or statuses != (
            expected.oep_role, expected.prior_construction,
            expected.birth_event, expected.target_independence,
            expected.post_birth_efficacy,
        )
        or historical is not expected.historical_actualization
        or operation is not ActualizationOperationStatus.JUDGED
        or physical is not PhysicalInstantiation.NOT_ESTABLISHED
        or consciousness is not ConsciousnessStatus.NOT_CLAIMED
        or scope != "finite-history-relative-observer-actualization-only"
    ):
        reject("historical-actualization-judgment-outer-drift")
    captured_past = tuple(identifier(item, "past-event-id") for item in past)
    captured_future = tuple(identifier(item, "future-event-id") for item in future)
    if captured_past != expected.past_event_ids or captured_future != expected.future_event_ids:
        reject("historical-actualization-causal-set-drift")
    for item, wanted in zip(rows, expected.counterfactual_evidence, strict=True):
        _counterfactual(item, wanted)
    logger.debug("validate_actualization_result exit")
    return expected
