"""Bounded typed-DAG pressure around one witnessed native P3-OG formation."""

from __future__ import annotations

from collections import deque
from dataclasses import fields, is_dataclass, replace
from enum import Enum
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_source import (
    validate_autonomous_tick_source,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes
from .prime_power_observer_genesis_p3og_formation_history_codec import (
    formation_history_digest,
)
from .prime_power_observer_genesis_p3og_formation_history_types import (
    FormationHistoryEvent,
    FormationHistoryEventKind,
    FormationHistoryStatus,
    P3OGFormationHistoryEvidence,
    P3OGFormationHistoryPlan,
    P3OG_FORMATION_HISTORY_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_native_formation_source import (
    FORMATION_RULE_ID,
    FORMATION_STATE_RULE_ID,
    MAX_FORMATION_TICKS,
    RESOURCE_RULE_ID,
    SOURCE_VERSION as NATIVE_FORMATION_SOURCE_VERSION,
    validate_native_formation_source,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    NativeFormationStatus,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_native_formation_validation import (
    validate_p3og_native_formation_evidence,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

PLAN_VERSION = "p3og-formation-history-plan-v2"
EVIDENCE_VERSION = "p3og-formation-history-evidence-v2"
GRAPH_RULE_ID = (
    "precommitted-formation-contract-linear-ticks-closure-future-seal-v2"
)
MAX_EVENTS = 256
MAX_PARENTS_PER_EVENT = 8


def _hex_digest(value: object, reason: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(reason)
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(reason) from exc
    return value


def _formation_contract_digest(
    autonomous_source: P3OGAutonomousTickSource,
) -> str:
    """Commit the closure/state/resource contract before selection."""
    return formation_history_digest(
        "formation-contract",
        NATIVE_FORMATION_SOURCE_VERSION,
        FORMATION_STATE_RULE_ID,
        FORMATION_RULE_ID,
        RESOURCE_RULE_ID,
        MAX_FORMATION_TICKS,
        autonomous_source.projection_rule_id,
        autonomous_source.closure_rule_id,
    )


def _digest_inventory(*values: object) -> frozenset[str]:
    """Collect exact digest spellings from freshly validated trusted DTOs."""
    found: set[str] = set()
    stack = list(values)
    while stack:
        value = stack.pop()
        if type(value) is str:
            if len(value) == 64:
                try:
                    int(value, 16)
                except ValueError:
                    pass
                else:
                    found.add(value)
        elif type(value) is tuple:
            stack.extend(value)
        elif isinstance(value, Enum):
            stack.append(value.value)
        elif is_dataclass(value) and not isinstance(value, type):
            stack.extend(getattr(value, field.name) for field in fields(value))
    return frozenset(found)


def _preflight_history_evidence(evidence: P3OGFormationHistoryEvidence) -> None:
    """Reject hostile nested values before evidence_bytes traverses them."""
    try:
        events = evidence.events
        past = evidence.strict_past_event_ids
        future = evidence.future_event_ids
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-formation-history-evidence-fields") from exc
    if (
        type(events) is not tuple
        or len(events) > MAX_EVENTS
        or type(past) is not tuple
        or len(past) > MAX_EVENTS
        or type(future) is not tuple
        or len(future) > MAX_EVENTS
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-formation-history-evidence-shape")
    for event in events:
        if type(event) is not FormationHistoryEvent:
            raise ValueError("p3og-formation-history-evidence-event-type")
        if (
            type(event.parent_ids) is not tuple
            or len(event.parent_ids) > MAX_PARENTS_PER_EVENT
            or any(type(item) is not str for item in event.parent_ids)
            or type(event.event_id) is not str
            or type(event.kind) is not FormationHistoryEventKind
            or type(event.logical_time) is not int
            or type(event.lineage_id) is not str
            or type(event.scope_digest) is not str
            or type(event.payload_digest) is not str
            or type(event.event_digest) is not str
        ):
            raise ValueError("p3og-formation-history-evidence-event-shape")
    if any(type(item) is not str for item in past + future):
        raise ValueError("p3og-formation-history-evidence-id-shape")


def p3og_formation_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
) -> P3OGFormationHistoryPlan:
    """Create an outcome-free history plan with no selected seed or verdict."""
    source, autonomous_source = validate_autonomous_tick_source(
        source,
        autonomous_source,
    )
    formation_contract_digest = _formation_contract_digest(autonomous_source)
    lineage_id = formation_history_digest(
        "formation-lineage",
        source.source_digest,
        autonomous_source.source_digest,
        formation_contract_digest,
        GRAPH_RULE_ID,
    )
    scope_digest = formation_history_digest(
        "formation-history-scope",
        source.source_digest,
        autonomous_source.source_digest,
        formation_contract_digest,
        GRAPH_RULE_ID,
    )
    fields = (
        PLAN_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        formation_contract_digest,
        lineage_id,
        scope_digest,
        GRAPH_RULE_ID,
        MAX_EVENTS,
        MAX_PARENTS_PER_EVENT,
    )
    return P3OGFormationHistoryPlan(
        *fields,
        formation_history_digest("formation-history-plan", *fields),
    )


def validate_formation_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    plan: P3OGFormationHistoryPlan,
) -> tuple[P3OGSource, P3OGAutonomousTickSource, P3OGFormationHistoryPlan]:
    source, autonomous_source = validate_autonomous_tick_source(
        source,
        autonomous_source,
    )
    if type(plan) is not P3OGFormationHistoryPlan:
        raise ValueError("p3og-formation-history-plan-type")
    try:
        expected = p3og_formation_history_plan(source, autonomous_source)
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-formation-history-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-formation-history-plan-drift")
    return source, autonomous_source, replace(expected)


def _event(
    plan: P3OGFormationHistoryPlan,
    event_id: str,
    kind: FormationHistoryEventKind,
    parents: tuple[str, ...],
    logical_time: int,
    payload_digest: str,
) -> FormationHistoryEvent:
    if type(event_id) is not str or not event_id or len(event_id) > 128:
        raise ValueError("p3og-formation-history-event-id")
    if type(kind) is not FormationHistoryEventKind:
        raise ValueError("p3og-formation-history-event-kind")
    if (
        type(parents) is not tuple
        or len(parents) > plan.max_parents_per_event
        or len(parents) != len(set(parents))
    ):
        raise ValueError("p3og-formation-history-event-parents")
    if event_id in parents or type(logical_time) is not int or logical_time < 0:
        raise ValueError("p3og-formation-history-event-shape")
    payload_digest = _hex_digest(
        payload_digest,
        "p3og-formation-history-event-payload",
    )
    fields = (
        event_id,
        kind,
        parents,
        logical_time,
        plan.lineage_id,
        plan.scope_digest,
        payload_digest,
    )
    return FormationHistoryEvent(
        *fields,
        formation_history_digest("formation-history-event", *fields),
    )


def _causal_sets(
    events: tuple[FormationHistoryEvent, ...],
    closure_event_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    table = {event.event_id: event for event in events}
    if len(table) != len(events) or closure_event_id not in table:
        raise ValueError("p3og-formation-history-event-table")
    children = {name: [] for name in table}
    for event in events:
        for parent in event.parent_ids:
            if parent not in table:
                raise ValueError("p3og-formation-history-unknown-parent")
            if table[parent].logical_time >= event.logical_time:
                raise ValueError("p3og-formation-history-nonmonotone-parent")
            children[parent].append(event.event_id)

    def walk(starts, adjacency):
        seen = set()
        queue = deque(starts)
        while queue:
            current = queue.popleft()
            for nxt in adjacency[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    closure = table[closure_event_id]
    parent_map = {name: list(table[name].parent_ids) for name in table}
    past = walk(closure.parent_ids, parent_map) | set(closure.parent_ids)
    future = walk((closure_event_id,), children)
    future.discard(closure_event_id)
    order = {event.event_id: index for index, event in enumerate(events)}
    return (
        tuple(sorted(past, key=order.__getitem__)),
        tuple(sorted(future, key=order.__getitem__)),
    )


def build_p3og_formation_history_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    plan: P3OGFormationHistoryPlan,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    criterion_payload_digest: str,
    later_result_payload_digest: str,
) -> P3OGFormationHistoryEvidence:
    """Build one typed DAG around a freshly validated witnessed closure."""
    source, autonomous_source, plan = validate_formation_history_plan(
        source,
        autonomous_source,
        plan,
    )
    source, autonomous_source, formation_source = validate_native_formation_source(
        source,
        autonomous_source,
        formation_source,
    )
    formation_evidence = validate_p3og_native_formation_evidence(
        source,
        autonomous_source,
        formation_source,
        formation_evidence,
    )
    if formation_evidence.status is not NativeFormationStatus.WITNESSED:
        raise ValueError("p3og-formation-history-requires-witnessed-formation")
    criterion_payload_digest = _hex_digest(
        criterion_payload_digest,
        "p3og-formation-history-criterion-digest",
    )
    later_result_payload_digest = _hex_digest(
        later_result_payload_digest,
        "p3og-formation-history-result-digest",
    )
    if len(formation_evidence.ticks) > formation_source.max_formation_ticks:
        raise ValueError("p3og-formation-history-tick-limit")
    required_events = len(formation_evidence.ticks) + 9
    if required_events > plan.max_events:
        raise ValueError("p3og-formation-history-event-limit")

    # The future seals must not already occur anywhere in the freshly replayed
    # pre-closure contract/source/evidence closure. This is exact digest-spelling
    # nonoccurrence only; it is not a semantic non-derivability theorem.
    preclosure_digests = _digest_inventory(
        source,
        autonomous_source,
        plan,
        formation_source,
        formation_evidence,
    )
    if (
        criterion_payload_digest in preclosure_digests
        or later_result_payload_digest in preclosure_digests
    ):
        raise ValueError("p3og-formation-history-future-seal-preloaded")

    events: list[FormationHistoryEvent] = []

    def add(event_id, kind, parents, payload):
        event = _event(plan, event_id, kind, parents, len(events), payload)
        events.append(event)
        return event.event_id

    source_id = add(
        "source",
        FormationHistoryEventKind.SOURCE_COMMIT,
        (),
        source.source_digest,
    )
    autonomous_id = add(
        "autonomous-law",
        FormationHistoryEventKind.AUTONOMOUS_LAW_COMMIT,
        (source_id,),
        autonomous_source.source_digest,
    )
    formation_contract_id = add(
        "formation-contract",
        FormationHistoryEventKind.FORMATION_CONTRACT_COMMIT,
        (autonomous_id,),
        plan.formation_contract_digest,
    )
    plan_id = add(
        "history-plan",
        FormationHistoryEventKind.HISTORY_PLAN_COMMIT,
        (formation_contract_id,),
        plan.plan_digest,
    )
    selection_id = add(
        "selection",
        FormationHistoryEventKind.SELECTION,
        (plan_id,),
        formation_source.selection.receipt_digest,
    )
    formation_source_id = add(
        "formation-source",
        FormationHistoryEventKind.FORMATION_SOURCE_BIND,
        (selection_id,),
        formation_source.source_digest,
    )
    previous = formation_source_id
    for index, tick in enumerate(formation_evidence.ticks, start=1):
        previous = add(
            f"formation-tick-{index}",
            FormationHistoryEventKind.FORMATION_TICK,
            (previous,),
            tick.receipt_digest,
        )
    closure_id = add(
        "first-closure",
        FormationHistoryEventKind.FIRST_CLOSURE,
        (previous,),
        formation_evidence.evidence_digest,
    )
    criterion_id = add(
        "decisive-criterion",
        FormationHistoryEventKind.DECISIVE_CRITERION,
        (closure_id,),
        criterion_payload_digest,
    )
    result_id = add(
        "later-result",
        FormationHistoryEventKind.LATER_RESULT,
        (closure_id, criterion_id),
        later_result_payload_digest,
    )
    captured = tuple(events)
    if len(captured) > plan.max_events:
        raise ValueError("p3og-formation-history-event-limit")
    past, future = _causal_sets(captured, closure_id)
    if criterion_id in past or result_id in past:
        raise ValueError("p3og-formation-history-future-leak")
    required_past = {
        source_id,
        autonomous_id,
        formation_contract_id,
        plan_id,
        selection_id,
        formation_source_id,
    }
    required_past.update(
        f"formation-tick-{i}"
        for i in range(1, len(formation_evidence.ticks) + 1)
    )
    if not required_past.issubset(past):
        raise ValueError("p3og-formation-history-missing-formation-ancestry")
    if criterion_id not in future or result_id not in future:
        raise ValueError("p3og-formation-history-future-placement")

    ancestry = formation_history_digest(
        "formation-history-ancestry",
        plan.plan_digest,
        formation_source.source_digest,
        formation_evidence.evidence_digest,
        captured,
        closure_id,
        past,
        future,
    )
    fields = (
        EVIDENCE_VERSION,
        plan.plan_digest,
        formation_source.source_digest,
        formation_evidence.evidence_digest,
        criterion_payload_digest,
        later_result_payload_digest,
        captured,
        closure_id,
        criterion_id,
        result_id,
        past,
        future,
        FormationHistoryStatus.WITNESSED,
        ancestry,
        0,
        P3OG_FORMATION_HISTORY_NONCLAIMS,
    )
    return P3OGFormationHistoryEvidence(
        *fields,
        formation_history_digest("formation-history-evidence", *fields),
    )


def validate_p3og_formation_history_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    plan: P3OGFormationHistoryPlan,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    criterion_payload_digest: str,
    later_result_payload_digest: str,
    evidence: P3OGFormationHistoryEvidence,
) -> P3OGFormationHistoryEvidence:
    """Freshly rebuild the DAG against external future seal digests."""
    if type(evidence) is not P3OGFormationHistoryEvidence:
        raise ValueError("p3og-formation-history-evidence-type")
    _preflight_history_evidence(evidence)
    try:
        expected = build_p3og_formation_history_evidence(
            source,
            autonomous_source,
            plan,
            formation_source,
            formation_evidence,
            criterion_payload_digest,
            later_result_payload_digest,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-formation-history-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-formation-history-evidence-drift")
    return replace(expected)
