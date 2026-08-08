"""Exact finite causal/access/assumption graph checks for P1-E4."""

from __future__ import annotations

from collections import deque
import logging

from .observer_actualization_types import (
    AccessEdge, AccessKind, EventKind, EvidenceAvailability, HistoryEvent,
    HistoricalAssumption,
)

logger = logging.getLogger(__name__)


class ObserverActualizationValidationError(ValueError):
    """A P1-E4 input violated the closed finite grammar."""


def reject(reason: str) -> None:
    logger.error("observer actualization rejected reason=%s", reason)
    raise ObserverActualizationValidationError(reason)


def identifier(value: object, label: str) -> str:
    logger.debug("identifier entry label=%s", label)
    if type(value) is not str or not value or len(value) > 128:
        reject(f"invalid-{label}")
    try:
        value.encode("utf-8", "strict")
    except UnicodeError:
        reject(f"invalid-{label}")
    logger.debug("identifier exit label=%s", label)
    return value


def hex_digest(value: object, label: str) -> str:
    logger.debug("hex_digest entry label=%s", label)
    if type(value) is not str or len(value) != 64:
        reject(f"invalid-{label}")
    try:
        int(value, 16)
    except ValueError:
        reject(f"invalid-{label}")
    logger.debug("hex_digest exit label=%s", label)
    return value


def snapshot_event(value: HistoryEvent) -> HistoryEvent:
    logger.debug("snapshot_event entry")
    if type(value) is not HistoryEvent:
        reject("history-event-must-be-exact")
    try:
        event_id, kind, parents = value.event_id, value.kind, value.parent_ids
        logical_time, payload = value.logical_time, value.payload_digest
        lineage, availability = value.lineage_id, value.availability
    except AttributeError:
        reject("history-event-fields-missing")
    event_id = identifier(event_id, "event-id")
    lineage = identifier(lineage, "lineage-id")
    payload = hex_digest(payload, "event-payload-digest")
    if type(kind) is not EventKind or type(availability) is not EvidenceAvailability:
        reject("invalid-history-event-enum")
    if type(logical_time) is not int or logical_time < 0 or logical_time > 10**9:
        reject("invalid-logical-time")
    if type(parents) is not tuple or len(parents) > 64:
        reject("invalid-parent-ids")
    captured = tuple(identifier(item, "parent-event-id") for item in parents)
    if len(captured) != len(set(captured)) or event_id in captured:
        reject("duplicate-or-self-parent")
    result = HistoryEvent(
        event_id, kind, captured, logical_time, payload, lineage, availability,
    )
    logger.debug("snapshot_event exit event=%s", event_id)
    return result


def snapshot_access(value: AccessEdge) -> AccessEdge:
    logger.debug("snapshot_access entry")
    if type(value) is not AccessEdge:
        reject("access-edge-must-be-exact")
    try:
        provider, consumer, kind = (
            value.provider_event_id, value.consumer_event_id, value.kind,
        )
    except AttributeError:
        reject("access-edge-fields-missing")
    if type(kind) is not AccessKind:
        reject("invalid-access-kind")
    result = AccessEdge(
        identifier(provider, "access-provider"),
        identifier(consumer, "access-consumer"), kind,
    )
    logger.debug("snapshot_access exit")
    return result


def snapshot_assumption(value: HistoricalAssumption) -> HistoricalAssumption:
    logger.debug("snapshot_assumption entry")
    if type(value) is not HistoricalAssumption:
        reject("historical-assumption-must-be-exact")
    try:
        assumption_id = identifier(value.assumption_id, "assumption-id")
        source = identifier(value.source_event_id, "assumption-source-event")
        depends = value.depends_on
    except AttributeError:
        reject("historical-assumption-fields-missing")
    if type(depends) is not tuple or len(depends) > 64:
        reject("invalid-assumption-dependencies")
    captured = tuple(identifier(item, "assumption-dependency") for item in depends)
    if len(captured) != len(set(captured)) or assumption_id in captured:
        reject("duplicate-or-self-assumption-dependency")
    result = HistoricalAssumption(assumption_id, source, captured)
    logger.debug("snapshot_assumption exit")
    return result


def causal_sets(
    events: tuple[HistoryEvent, ...], birth_event_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, HistoryEvent]]:
    """Derive strict past/future from parent edges, never timestamps alone."""
    logger.debug("causal_sets entry events=%d", len(events))
    table = {item.event_id: item for item in events}
    if len(table) != len(events) or birth_event_id not in table:
        reject("duplicate-event-or-missing-birth")
    children = {name: [] for name in table}
    for item in events:
        for parent in item.parent_ids:
            if parent not in table:
                reject("unknown-parent-event")
            if table[parent].logical_time >= item.logical_time:
                reject("nonmonotone-parent-edge")
            children[parent].append(item.event_id)
    def walk(starts: tuple[str, ...], adjacency) -> set[str]:
        logger.debug("causal walk entry starts=%d", len(starts))
        seen: set[str] = set()
        queue = deque(starts)
        while queue:
            current = queue.popleft()
            for nxt in adjacency[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        logger.debug("causal walk exit seen=%d", len(seen))
        return seen
    past = walk(table[birth_event_id].parent_ids, {
        name: list(table[name].parent_ids) for name in table
    }) | set(table[birth_event_id].parent_ids)
    future = walk((birth_event_id,), children)
    future.discard(birth_event_id)
    order = {item.event_id: index for index, item in enumerate(events)}
    result = (
        tuple(sorted(past, key=order.__getitem__)),
        tuple(sorted(future, key=order.__getitem__)), table,
    )
    logger.debug("causal_sets exit past=%d future=%d", len(past), len(future))
    return result


def restricted_access_reaches_past(
    events: tuple[HistoryEvent, ...], access: tuple[AccessEdge, ...],
    past_ids: tuple[str, ...], protected_ids: tuple[str, ...] = (),
) -> bool:
    """Detect restricted reachability into strict past or birth dependencies."""
    logger.debug("restricted_access_reaches_past entry")
    table = {item.event_id: item for item in events}
    adjacency = {name: [] for name in table}
    for item in events:
        for parent in item.parent_ids:
            adjacency[parent].append(item.event_id)
    for edge in access:
        if edge.provider_event_id not in table or edge.consumer_event_id not in table:
            reject("access-edge-unknown-event")
        adjacency[edge.provider_event_id].append(edge.consumer_event_id)
    restricted = {
        item.event_id for item in events if item.kind in {
            EventKind.TARGET, EventKind.ORACLE, EventKind.EXPECTED_RESPONSE,
            EventKind.LATER_RESULT,
        }
    }
    protected = set(past_ids) | set(protected_ids)
    if not protected.issubset(table):
        reject("target-seal-unknown-protected-event")
    queue = deque(restricted)
    seen = set(restricted)
    if restricted & protected:
        logger.debug("restricted_access_reaches_past exit leak=true direct")
        return True
    while queue:
        current = queue.popleft()
        for nxt in adjacency[current]:
            if nxt in protected:
                logger.debug("restricted_access_reaches_past exit leak=true")
                return True
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    logger.debug("restricted_access_reaches_past exit leak=false")
    return False


def assumption_source_closure(
    assumptions: tuple[HistoricalAssumption, ...], roots: tuple[str, ...],
    events: dict[str, HistoryEvent], lineage_id: str,
) -> tuple[str, ...]:
    """Close named assumptions and reject circular actualization sources."""
    logger.debug("assumption_source_closure entry")
    table = {item.assumption_id: item for item in assumptions}
    if len(table) != len(assumptions) or any(root not in table for root in roots):
        reject("invalid-assumption-table-or-root")
    visiting: set[str] = set()
    closed: list[str] = []
    seen: set[str] = set()
    def visit(name: str) -> None:
        logger.debug("assumption visit entry name=%s", name)
        if name in visiting:
            reject("cyclic-historical-assumptions")
        if name in seen:
            return
        visiting.add(name)
        node = table[name]
        if node.source_event_id not in events:
            reject("assumption-source-unknown-event")
        for dependency in node.depends_on:
            if dependency not in table:
                reject("unknown-assumption-dependency")
            visit(dependency)
        visiting.remove(name)
        seen.add(name)
        closed.append(name)
        logger.debug("assumption visit exit name=%s", name)
    for root in roots:
        visit(root)
    forbidden = {
        EventKind.ACTUALIZATION_JUDGMENT, EventKind.ACTUALIZATION_CERTIFICATE,
    }
    for name in closed:
        event = events[table[name].source_event_id]
        if event.kind in forbidden or (
            event.kind in {EventKind.BIRTH, EventKind.COPIED_BIRTH}
            and event.lineage_id == lineage_id
        ):
            reject("circular-actualization-source-closure")
    logger.debug("assumption_source_closure exit size=%d", len(closed))
    return tuple(closed)
