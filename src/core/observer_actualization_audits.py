"""Target-seal and same-token efficacy audits for finite P1-E4 histories."""

from __future__ import annotations

from collections import deque
import logging

from .observer_actualization_digest import token_digest
from .observer_actualization_graph import restricted_access_reaches_past
from .observer_actualization_types import (
    EventKind, EvidenceAvailability, HistoricalObserverSource, HistoryEvent,
)
from .observer_genesis_types import GenesisJudgment, PremiseStatus

logger = logging.getLogger(__name__)


def target_seal_breached(
    source: HistoricalObserverSource, past_ids: tuple[str, ...],
    assumption_source_ids: set[str],
) -> bool:
    """Seal strict past, birth, and every declared birth-core dependency."""
    logger.debug("target seal audit entry")
    protected = (
        source.birth_event_id, source.construction_event_id, source.oep_event_id,
        *sorted(assumption_source_ids),
    )
    result = restricted_access_reaches_past(
        source.events, source.access_edges, past_ids, protected,
    )
    logger.debug("target seal audit exit breached=%s", result)
    return result


def assumption_sources_outside_past(
    assumption_source_ids: set[str], past_ids: tuple[str, ...],
) -> bool:
    """Report a concrete provenance contradiction at the birth cut."""
    logger.debug("assumption strict-past audit entry")
    result = not assumption_source_ids.issubset(set(past_ids))
    logger.debug("assumption strict-past audit exit outside=%s", result)
    return result


def _ancestors(event_id: str, table: dict[str, HistoryEvent]) -> set[str]:
    logger.debug("efficacy ancestor walk entry event=%s", event_id)
    seen: set[str] = set()
    queue = deque(table[event_id].parent_ids)
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(table[current].parent_ids)
    logger.debug("efficacy ancestor walk exit event=%s count=%d", event_id, len(seen))
    return seen


def efficacy_pressure(
    source: HistoricalObserverSource, future_ids: tuple[str, ...],
    table: dict[str, HistoryEvent], genesis,
) -> tuple[bool, bool]:
    """Bind every claimed efficacy trace to the exact birth token and scope."""
    logger.debug("same-token efficacy audit entry")
    if type(genesis) is not GenesisJudgment:
        logger.debug("same-token efficacy audit exit unavailable raw-e1-result")
        return False, True
    intervention = table[source.intervention_event_id]
    response = table[source.response_event_id]
    expected_response = (
        genesis.premises[5].evidence_digest
        if type(genesis) is GenesisJudgment else None
    )
    traces = tuple(
        item for item in source.events
        if item.kind in {EventKind.INTERVENTION, EventKind.RESPONSE}
    )
    trace_contradiction = False
    for event in traces:
        ancestors = _ancestors(event.event_id, table)
        birth_ancestors = {
            name for name in ancestors
            if table[name].kind in {EventKind.BIRTH, EventKind.COPIED_BIRTH}
        }
        same_token = birth_ancestors == {source.birth_event_id} and token_digest(
            source.birth_core_digest, event.lineage_id, source.birth_event_id,
        ) == source.historical_token_id
        lineage_closed = all(
            table[name].lineage_id == source.lineage_id
            for name in ancestors
            if name in future_ids or name == source.birth_event_id
        )
        response_has_intervention = (
            event.kind is not EventKind.RESPONSE
            or any(table[name].kind is EventKind.INTERVENTION for name in ancestors)
        )
        payload_matches_scope = (
            event.payload_digest == source.e1_witness.witness_digest
            if event.kind is EventKind.INTERVENTION
            else expected_response is not None
            and event.payload_digest == expected_response
        )
        trace_contradiction = trace_contradiction or (
            event.lineage_id != source.lineage_id
            or not same_token
            or not lineage_closed
            or not response_has_intervention
            or event.event_id not in future_ids
            or not payload_matches_scope
        )
    contradicted = trace_contradiction or (
        type(genesis) is GenesisJudgment
        and genesis.residue_efficacy is PremiseStatus.REFUTED
    ) or (
        intervention.kind is not EventKind.INTERVENTION
        or response.kind is not EventKind.RESPONSE
        or source.intervention_event_id not in response.parent_ids
    )
    unavailable = (
        type(genesis) is not GenesisJudgment
        or genesis.residue_efficacy is PremiseStatus.OPEN
        or any(item.availability is EvidenceAvailability.UNAVAILABLE for item in traces)
    )
    logger.debug(
        "same-token efficacy audit exit contradicted=%s unavailable=%s",
        contradicted, unavailable,
    )
    return contradicted, unavailable
