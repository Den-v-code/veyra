"""Fresh mandatory counterfactual replay for finite P1-E4 histories."""

from __future__ import annotations

from dataclasses import replace
import logging

from .observer_actualization_digest import digest, history_digest, token_digest
from .observer_actualization_graph import restricted_access_reaches_past
from .observer_actualization_types import (
    AccessEdge, AccessKind, CounterfactualClass, CounterfactualEvidence,
    CounterfactualOutcome, EvidenceAvailability, HistoricalObserverSource,
)

logger = logging.getLogger(__name__)


def _case_unavailable(
    source: HistoricalObserverSource, case, table,
) -> bool:
    """Treat absent/unavailable required counterfactual provenance as OPEN."""
    logger.debug("counterfactual availability entry kind=%s", case.kind.value)
    required = (case.provider_event_id, case.consumer_event_id)
    if case.kind is CounterfactualClass.FOREIGN_PARENT_COPY:
        required += case.copied_parent_ids
    result = any(
        name not in table
        or table[name].availability is EvidenceAvailability.UNAVAILABLE
        for name in required
    )
    logger.debug("counterfactual availability exit unavailable=%s", result)
    return result


def counterfactual_evidence(
    source: HistoricalObserverSource, past_ids: tuple[str, ...],
) -> tuple[CounterfactualEvidence, ...]:
    """Replay the exact three pressures with missing evidence kept OPEN."""
    logger.debug("counterfactual evidence entry")
    table = {item.event_id: item for item in source.events}
    target = table[source.target_event_id]
    birth = table[source.birth_event_id]
    rows: list[CounterfactualEvidence] = []
    for case in source.counterfactuals:
        unavailable = _case_unavailable(source, case, table)
        passed = False
        contradicted = False
        detail: tuple[tuple[str, bytes], ...]
        if case.kind is CounterfactualClass.PREFIX_TARGET_VARIATION:
            contradicted = (
                case.provider_event_id != source.target_event_id
                or case.consumer_event_id != source.response_event_id
                or target.event_id in past_ids
                or case.alternate_target_digest == target.payload_digest
            )
            varied = tuple(
                replace(item, payload_digest=case.alternate_target_digest)
                if item.event_id == source.target_event_id else item
                for item in source.events
            )
            alternate_history = history_digest(
                source.history_id, source.historical_token_id, varied,
                source.access_edges, source.assumptions, source.counterfactuals,
            )
            passed = (
                not contradicted and alternate_history != source.history_digest
            )
            detail = (("alternate-history", alternate_history.encode("ascii")),)
        elif case.kind is CounterfactualClass.TARGET_READING_CHOOSER:
            contradicted = (
                case.provider_event_id != source.target_event_id
                or case.consumer_event_id != source.construction_event_id
            )
            if unavailable:
                detail = (("availability", b"unavailable"),)
            else:
                simulated = source.access_edges + (AccessEdge(
                    case.provider_event_id, case.consumer_event_id,
                    AccessKind.TARGET_READ,
                ),)
                passed = not contradicted and restricted_access_reaches_past(
                    source.events, simulated, past_ids,
                    (source.birth_event_id, source.construction_event_id,
                     source.oep_event_id),
                )
                detail = (("simulated-leak", str(passed).encode("ascii")),)
        else:
            copied_token = token_digest(
                source.birth_core_digest, case.copied_lineage_id, case.case_id,
            )
            contradicted = (
                case.provider_event_id != source.birth_event_id
                or case.consumer_event_id != source.response_event_id
                or case.copied_lineage_id == source.lineage_id
                or case.copied_parent_ids == birth.parent_ids
                or copied_token == source.historical_token_id
            )
            passed = (
                not contradicted
                and all(name in table for name in case.copied_parent_ids)
            )
            detail = (
                ("copied-lineage", case.copied_lineage_id.encode()),
                ("copied-parents", "\x1f".join(case.copied_parent_ids).encode()),
                ("copied-token", copied_token.encode("ascii")),
            )
        outcome = (
            CounterfactualOutcome.FAILED if contradicted
            else CounterfactualOutcome.OPEN if unavailable
            else CounterfactualOutcome.PASSED if passed
            else CounterfactualOutcome.FAILED
        )
        evidence = digest("counterfactual-evidence", (
            ("case", case.case_id.encode()), ("kind", case.kind.value.encode()),
            ("outcome", outcome.value.encode()), *detail,
        ))
        rows.append(CounterfactualEvidence(case.case_id, case.kind, outcome, evidence))
    result = tuple(rows)
    logger.debug("counterfactual evidence exit rows=%d", len(result))
    return result
