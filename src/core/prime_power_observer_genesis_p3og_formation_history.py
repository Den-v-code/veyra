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
    FormationHistoryEventSourceClosure,
    FormationHistoryPostClosureBindings,
    FormationHistoryPrecommitment,
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
from .prime_power_observer_genesis_p3og_one_shot_selection_types import (
    P3OGOneShotSelectionSource,
    P3OGSelectionCapability,
    SelectionCapabilityState,
)
from .prime_power_observer_genesis_p3og_one_shot_selection_validation import (
    validate_p3og_selection_capability,
)
from .prime_power_observer_genesis_p3og_selection_source_closure import (
    selector_law_digest,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

PLAN_VERSION = "p3og-formation-history-plan-v6"
EVIDENCE_VERSION = "p3og-formation-history-evidence-v6"
GRAPH_RULE_ID = (
    "preselection-commitments-event-source-closure-available-consume-terminal-v6"
)
MAX_EVENTS = 256
MAX_PARENTS_PER_EVENT = 8
MAX_SOURCES_PER_EVENT = 8
MAX_PRESELECTION_COMMITMENTS = 4

_RESERVED_PRECOMMITMENT_EVENT_IDS = frozenset({
    "source",
    "autonomous-law",
    "formation-contract",
    "selection-pool",
    "blind-seed",
    "selector-law",
    "selection-source-closure",
    "selection-source",
    "selection-capability-available",
    "history-plan",
    "selection-consume",
    "selection-capability-consumed",
    "formation-source",
    "first-closure",
    "formation-refutation",
    "semantic-first-closure",
    "arithmetic-input-source",
    "arithmetic-coupling",
    "retained-difference",
    "residue-phase-effect",
    "typed-ablation",
    "removal-dependence",
    "decisive-criterion",
    "later-result",
})


def _hex_digest(value: object, reason: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(reason)
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(reason) from exc
    return value


def _validated_postclosure_bindings(
    bindings: FormationHistoryPostClosureBindings | None,
) -> FormationHistoryPostClosureBindings | None:
    """Validate one fixed post-closure payload bundle without inventing a new DAG."""
    if bindings is None:
        return None
    if type(bindings) is not FormationHistoryPostClosureBindings:
        raise ValueError("p3og-formation-history-postclosure-bindings-type")
    fields = (
        ("semantic-first-closure", bindings.semantic_first_closure_digest),
        ("arithmetic-input-source", bindings.arithmetic_input_source_digest),
        ("arithmetic-coupling", bindings.arithmetic_coupling_digest),
        ("retained-difference", bindings.retained_difference_digest),
        ("residue-phase-effect", bindings.residue_phase_effect_digest),
        ("typed-ablation", bindings.typed_ablation_digest),
        ("removal-dependence", bindings.removal_dependence_digest),
    )
    for label, digest_value in fields:
        _hex_digest(
            digest_value,
            f"p3og-formation-history-postclosure-{label}-digest",
        )
    return bindings


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
        terminal = evidence.formation_terminal_event_id
        closure = evidence.closure_event_id
        criterion_id = evidence.criterion_event_id
        result_id = evidence.later_result_event_id
        criterion_digest = evidence.criterion_payload_digest
        result_digest = evidence.later_result_payload_digest
        plan_digest = evidence.plan_digest
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
        or type(terminal) is not str
        or (closure is not None and type(closure) is not str)
        or (criterion_id is not None and type(criterion_id) is not str)
        or (result_id is not None and type(result_id) is not str)
        or (criterion_digest is not None and type(criterion_digest) is not str)
        or (result_digest is not None and type(result_digest) is not str)
        or type(evidence.status) is not FormationHistoryStatus
        or type(evidence.promotions) is not int
        or type(plan_digest) is not str
    ):
        raise ValueError("p3og-formation-history-evidence-shape")
    for event in events:
        if type(event) is not FormationHistoryEvent:
            raise ValueError("p3og-formation-history-evidence-event-type")
        if type(event.source_closure) is not FormationHistoryEventSourceClosure:
            raise ValueError("p3og-formation-history-evidence-source-closure-type")
        closure = event.source_closure
        if (
            type(closure.plan_digest) is not str
            or type(closure.event_id) is not str
            or type(closure.direct_source_event_ids) is not tuple
            or len(closure.direct_source_event_ids) > MAX_SOURCES_PER_EVENT
            or any(type(item) is not str for item in closure.direct_source_event_ids)
            or type(closure.transitive_source_event_ids) is not tuple
            or len(closure.transitive_source_event_ids) > MAX_EVENTS
            or any(type(item) is not str for item in closure.transitive_source_event_ids)
            or type(closure.closure_digest) is not str
            or type(event.parent_ids) is not tuple
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
    _validate_event_source_closures(events, plan_digest)


def p3og_formation_history_precommitment(
    commitment_id: str,
    payload_digest: str,
    direct_source_event_ids: tuple[str, ...],
) -> FormationHistoryPrecommitment:
    """Build one bounded generic commitment for the preselection history cut."""
    if (
        type(commitment_id) is not str
        or not commitment_id
        or len(commitment_id) > 128
        or commitment_id in _RESERVED_PRECOMMITMENT_EVENT_IDS
        or commitment_id.startswith("formation-tick-")
    ):
        raise ValueError("p3og-formation-history-precommitment-id")
    payload_digest = _hex_digest(
        payload_digest,
        "p3og-formation-history-precommitment-payload",
    )
    if (
        type(direct_source_event_ids) is not tuple
        or len(direct_source_event_ids) > MAX_SOURCES_PER_EVENT
        or len(direct_source_event_ids) != len(set(direct_source_event_ids))
        or any(
            type(item) is not str or not item
            for item in direct_source_event_ids
        )
        or commitment_id in direct_source_event_ids
    ):
        raise ValueError("p3og-formation-history-precommitment-sources")
    fields = (commitment_id, payload_digest, direct_source_event_ids)
    return FormationHistoryPrecommitment(
        *fields,
        formation_history_digest("formation-history-precommitment", *fields),
    )


def _validated_preselection_commitments(
    commitments: tuple[FormationHistoryPrecommitment, ...],
) -> tuple[FormationHistoryPrecommitment, ...]:
    if (
        type(commitments) is not tuple
        or len(commitments) > MAX_PRESELECTION_COMMITMENTS
        or any(type(item) is not FormationHistoryPrecommitment for item in commitments)
    ):
        raise ValueError("p3og-formation-history-precommitments-shape")
    ids = tuple(item.commitment_id for item in commitments)
    if len(ids) != len(set(ids)):
        raise ValueError("p3og-formation-history-precommitments-duplicate")
    available_sources = {"source", "autonomous-law", "formation-contract"}
    canonical: list[FormationHistoryPrecommitment] = []
    for item in commitments:
        if any(name not in available_sources for name in item.direct_source_event_ids):
            raise ValueError("p3og-formation-history-precommitment-future-source")
        expected = p3og_formation_history_precommitment(
            item.commitment_id,
            item.payload_digest,
            item.direct_source_event_ids,
        )
        if not compare_digest(canonical_bytes(item), canonical_bytes(expected)):
            raise ValueError("p3og-formation-history-precommitment-drift")
        canonical.append(expected)
        available_sources.add(expected.commitment_id)
    return tuple(canonical)


def p3og_formation_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    selection_source: P3OGOneShotSelectionSource,
    available_capability: P3OGSelectionCapability,
    preselection_commitments: tuple[FormationHistoryPrecommitment, ...] = (),
) -> P3OGFormationHistoryPlan:
    """Commit the blind source and AVAILABLE cut before selection or verdict."""
    source, autonomous_source = validate_autonomous_tick_source(
        source,
        autonomous_source,
    )
    available_capability = validate_p3og_selection_capability(
        source,
        selection_source,
        available_capability,
    )
    if available_capability.state is not SelectionCapabilityState.AVAILABLE:
        raise ValueError("p3og-formation-history-plan-capability-consumed")
    preselection_commitments = _validated_preselection_commitments(
        preselection_commitments,
    )
    preselection_commitments_digest = formation_history_digest(
        "formation-history-preselection-commitments",
        preselection_commitments,
    )
    formation_contract_digest = _formation_contract_digest(autonomous_source)
    lineage_id = formation_history_digest(
        "formation-lineage",
        source.source_digest,
        autonomous_source.source_digest,
        formation_contract_digest,
        selection_source.source_digest,
        available_capability.capability_digest,
        preselection_commitments_digest,
        GRAPH_RULE_ID,
    )
    scope_digest = formation_history_digest(
        "formation-history-scope",
        source.source_digest,
        autonomous_source.source_digest,
        formation_contract_digest,
        selection_source.source_digest,
        available_capability.capability_digest,
        preselection_commitments_digest,
        GRAPH_RULE_ID,
    )
    fields = (
        PLAN_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        formation_contract_digest,
        selection_source.source_digest,
        selection_source.pool_digest,
        selection_source.blind_seed_digest,
        selection_source.source_closure.closure_digest,
        available_capability.capability_digest,
        preselection_commitments,
        preselection_commitments_digest,
        lineage_id,
        scope_digest,
        GRAPH_RULE_ID,
        MAX_EVENTS,
        MAX_PARENTS_PER_EVENT,
        MAX_SOURCES_PER_EVENT,
        MAX_PRESELECTION_COMMITMENTS,
    )
    return P3OGFormationHistoryPlan(
        *fields,
        formation_history_digest("formation-history-plan", *fields),
    )


def validate_formation_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    selection_source: P3OGOneShotSelectionSource,
    available_capability: P3OGSelectionCapability,
    plan: P3OGFormationHistoryPlan,
) -> tuple[P3OGSource, P3OGAutonomousTickSource, P3OGFormationHistoryPlan]:
    source, autonomous_source = validate_autonomous_tick_source(
        source,
        autonomous_source,
    )
    if type(plan) is not P3OGFormationHistoryPlan:
        raise ValueError("p3og-formation-history-plan-type")
    try:
        expected = p3og_formation_history_plan(
            source,
            autonomous_source,
            selection_source,
            available_capability,
            plan.preselection_commitments,
        )
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-formation-history-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-formation-history-plan-drift")
    return source, autonomous_source, replace(expected)


def _event_source_closure(
    plan_digest: str,
    event_id: str,
    direct_source_event_ids: tuple[str, ...],
    prior_events: tuple[FormationHistoryEvent, ...],
    max_sources_per_event: int,
) -> FormationHistoryEventSourceClosure:
    if (
        type(direct_source_event_ids) is not tuple
        or len(direct_source_event_ids) > max_sources_per_event
        or len(direct_source_event_ids) != len(set(direct_source_event_ids))
        or any(type(item) is not str or not item for item in direct_source_event_ids)
        or event_id in direct_source_event_ids
    ):
        raise ValueError("p3og-formation-history-event-source-ids")
    table = {event.event_id: event for event in prior_events}
    if len(table) != len(prior_events):
        raise ValueError("p3og-formation-history-event-source-table")
    if any(name not in table for name in direct_source_event_ids):
        raise ValueError("p3og-formation-history-source-future-or-unknown")
    order = {event.event_id: index for index, event in enumerate(prior_events)}
    closed: set[str] = set()
    for name in direct_source_event_ids:
        closed.add(name)
        closed.update(table[name].source_closure.transitive_source_event_ids)
    transitive = tuple(sorted(closed, key=order.__getitem__))
    fields = (plan_digest, event_id, direct_source_event_ids, transitive)
    return FormationHistoryEventSourceClosure(
        *fields,
        formation_history_digest("formation-history-event-source-closure", *fields),
    )


def _validate_event_source_closures(
    events: tuple[FormationHistoryEvent, ...],
    plan_digest: str,
) -> None:
    prior: list[FormationHistoryEvent] = []
    for event in events:
        closure = event.source_closure
        if closure.plan_digest != plan_digest or closure.event_id != event.event_id:
            raise ValueError("p3og-formation-history-source-closure-context-drift")
        expected = _event_source_closure(
            plan_digest,
            event.event_id,
            closure.direct_source_event_ids,
            tuple(prior),
            MAX_SOURCES_PER_EVENT,
        )
        if not compare_digest(canonical_bytes(closure), canonical_bytes(expected)):
            raise ValueError("p3og-formation-history-source-closure-drift")
        prior.append(event)


def _event(
    plan: P3OGFormationHistoryPlan,
    event_id: str,
    kind: FormationHistoryEventKind,
    parents: tuple[str, ...],
    source_event_ids: tuple[str, ...],
    logical_time: int,
    payload_digest: str,
    prior_events: tuple[FormationHistoryEvent, ...],
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
    source_closure = _event_source_closure(
        plan.plan_digest,
        event_id,
        source_event_ids,
        prior_events,
        plan.max_sources_per_event,
    )
    fields = (
        event_id,
        kind,
        parents,
        source_closure,
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
    terminal_event_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    table = {event.event_id: event for event in events}
    if len(table) != len(events) or terminal_event_id not in table:
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

    terminal = table[terminal_event_id]
    parent_map = {name: list(table[name].parent_ids) for name in table}
    past = walk(terminal.parent_ids, parent_map) | set(terminal.parent_ids)
    future = walk((terminal_event_id,), children)
    future.discard(terminal_event_id)
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
    criterion_payload_digest: str | None,
    later_result_payload_digest: str | None,
    postclosure_bindings: FormationHistoryPostClosureBindings | None = None,
) -> P3OGFormationHistoryEvidence:
    """Preserve one consumed choice through witnessed or refuted formation."""
    source, autonomous_source, formation_source = validate_native_formation_source(
        source,
        autonomous_source,
        formation_source,
    )
    source, autonomous_source, plan = validate_formation_history_plan(
        source,
        autonomous_source,
        formation_source.selection_source,
        formation_source.selection_before,
        plan,
    )
    formation_evidence = validate_p3og_native_formation_evidence(
        source,
        autonomous_source,
        formation_source,
        formation_evidence,
    )
    witnessed = formation_evidence.status is NativeFormationStatus.WITNESSED
    refuted = formation_evidence.status is NativeFormationStatus.REFUTED
    if not witnessed and not refuted:
        raise ValueError("p3og-formation-history-formation-status")
    postclosure_bindings = _validated_postclosure_bindings(postclosure_bindings)
    if refuted and postclosure_bindings is not None:
        raise ValueError("p3og-formation-history-refuted-postclosure")
    if witnessed:
        criterion_payload_digest = _hex_digest(
            criterion_payload_digest,
            "p3og-formation-history-criterion-digest",
        )
        later_result_payload_digest = _hex_digest(
            later_result_payload_digest,
            "p3og-formation-history-result-digest",
        )
    elif criterion_payload_digest is not None or later_result_payload_digest is not None:
        raise ValueError("p3og-formation-history-refuted-future-seal")
    if len(formation_evidence.ticks) > formation_source.max_formation_ticks:
        raise ValueError("p3og-formation-history-tick-limit")
    required_events = (
        len(formation_evidence.ticks)
        + len(plan.preselection_commitments)
        + (16 if witnessed else 14)
        + (7 if postclosure_bindings is not None else 0)
    )
    if required_events > plan.max_events:
        raise ValueError("p3og-formation-history-event-limit")

    # On the witnessed branch, future seals must not occur anywhere in the
    # freshly replayed pre-terminal closure. This is exact digest-spelling
    # nonoccurrence only, not a semantic non-derivability theorem.
    preterminal_digests = _digest_inventory(
        source,
        autonomous_source,
        plan,
        formation_source.selection_source,
        formation_source.selection_before,
        formation_source.selection_after,
        formation_source.selection,
        formation_source,
        formation_evidence,
    )
    if witnessed and (
        criterion_payload_digest in preterminal_digests
        or later_result_payload_digest in preterminal_digests
    ):
        raise ValueError("p3og-formation-history-future-seal-preloaded")
    if postclosure_bindings is not None:
        postclosure_digests = (
            postclosure_bindings.semantic_first_closure_digest,
            postclosure_bindings.arithmetic_input_source_digest,
            postclosure_bindings.arithmetic_coupling_digest,
            postclosure_bindings.retained_difference_digest,
            postclosure_bindings.residue_phase_effect_digest,
            postclosure_bindings.typed_ablation_digest,
            postclosure_bindings.removal_dependence_digest,
        )
        if any(item in preterminal_digests for item in postclosure_digests):
            raise ValueError("p3og-formation-history-postclosure-preloaded")

    events: list[FormationHistoryEvent] = []

    def add(event_id, kind, parents, sources, payload):
        event = _event(
            plan,
            event_id,
            kind,
            parents,
            sources,
            len(events),
            payload,
            tuple(events),
        )
        events.append(event)
        return event.event_id

    source_id = add(
        "source",
        FormationHistoryEventKind.SOURCE_COMMIT,
        (),
        (),
        source.source_digest,
    )
    autonomous_id = add(
        "autonomous-law",
        FormationHistoryEventKind.AUTONOMOUS_LAW_COMMIT,
        (source_id,),
        (source_id,),
        autonomous_source.source_digest,
    )
    formation_contract_id = add(
        "formation-contract",
        FormationHistoryEventKind.FORMATION_CONTRACT_COMMIT,
        (autonomous_id,),
        (autonomous_id,),
        plan.formation_contract_digest,
    )
    precommitment_ids: list[str] = []
    preselection_parent = formation_contract_id
    for commitment in plan.preselection_commitments:
        commitment_id = add(
            commitment.commitment_id,
            FormationHistoryEventKind.PRESELECTION_COMMITMENT,
            (preselection_parent,),
            commitment.direct_source_event_ids,
            commitment.payload_digest,
        )
        precommitment_ids.append(commitment_id)
        preselection_parent = commitment_id
    pool_id = add(
        "selection-pool",
        FormationHistoryEventKind.SELECTION_POOL_COMMIT,
        (preselection_parent,),
        (source_id,),
        formation_source.selection_source.pool_digest,
    )
    blind_seed_id = add(
        "blind-seed",
        FormationHistoryEventKind.BLIND_SEED_COMMIT,
        (pool_id,),
        (),
        formation_source.selection_source.blind_seed_digest,
    )
    selector_law_id = add(
        "selector-law",
        FormationHistoryEventKind.SELECTOR_LAW_COMMIT,
        (blind_seed_id,),
        (),
        selector_law_digest(),
    )
    selection_closure_id = add(
        "selection-source-closure",
        FormationHistoryEventKind.SELECTION_SOURCE_CLOSURE_COMMIT,
        (selector_law_id,),
        (pool_id, blind_seed_id, selector_law_id),
        formation_source.selection_source.source_closure.closure_digest,
    )
    selection_source_id = add(
        "selection-source",
        FormationHistoryEventKind.SELECTION_SOURCE_COMMIT,
        (selection_closure_id,),
        (selection_closure_id,),
        formation_source.selection_source.source_digest,
    )
    available_id = add(
        "selection-capability-available",
        FormationHistoryEventKind.SELECTION_CAPABILITY_AVAILABLE,
        (selection_source_id,),
        (selection_source_id,),
        formation_source.selection_before.capability_digest,
    )
    plan_id = add(
        "history-plan",
        FormationHistoryEventKind.HISTORY_PLAN_COMMIT,
        (available_id,),
        (
            formation_contract_id,
            selection_source_id,
            available_id,
            *precommitment_ids,
        ),
        plan.plan_digest,
    )
    selection_id = add(
        "selection-consume",
        FormationHistoryEventKind.SELECTION_CONSUME,
        (plan_id,),
        (selection_source_id, available_id),
        formation_source.selection.receipt_digest,
    )
    consumed_id = add(
        "selection-capability-consumed",
        FormationHistoryEventKind.SELECTION_CAPABILITY_CONSUMED,
        (selection_id,),
        (selection_id,),
        formation_source.selection_after.capability_digest,
    )
    formation_source_id = add(
        "formation-source",
        FormationHistoryEventKind.FORMATION_SOURCE_BIND,
        (consumed_id,),
        (autonomous_id, selection_source_id, available_id, selection_id, consumed_id),
        formation_source.source_digest,
    )
    previous = formation_source_id
    for index, tick in enumerate(formation_evidence.ticks, start=1):
        tick_sources = (
            (formation_source_id,)
            if previous == formation_source_id
            else (formation_source_id, previous)
        )
        previous = add(
            f"formation-tick-{index}",
            FormationHistoryEventKind.FORMATION_TICK,
            (previous,),
            tick_sources,
            tick.receipt_digest,
        )
    terminal_id = add(
        "first-closure" if witnessed else "formation-refutation",
        (
            FormationHistoryEventKind.FIRST_CLOSURE
            if witnessed
            else FormationHistoryEventKind.FORMATION_REFUTATION
        ),
        (previous,),
        (
            (formation_source_id,)
            if previous == formation_source_id
            else (formation_source_id, previous)
        ),
        formation_evidence.evidence_digest,
    )
    postclosure_ids: list[str] = []
    future_parent = terminal_id
    if postclosure_bindings is not None:
        commitment_ids = {
            item.commitment_id for item in plan.preselection_commitments
        }
        required_commitments = {
            "semantic-formation-bridge-contract",
            "semantic-ablation-contract",
            "semantic-intervention-plan",
        }
        if not required_commitments.issubset(commitment_ids):
            raise ValueError(
                "p3og-formation-history-postclosure-missing-precommitments",
            )
        semantic_bridge_id = add(
            "semantic-first-closure",
            FormationHistoryEventKind.SEMANTIC_FIRST_CLOSURE,
            (future_parent,),
            (terminal_id, "semantic-formation-bridge-contract"),
            postclosure_bindings.semantic_first_closure_digest,
        )
        postclosure_ids.append(semantic_bridge_id)
        arithmetic_id = add(
            "arithmetic-input-source",
            FormationHistoryEventKind.ARITHMETIC_INPUT_SOURCE,
            (semantic_bridge_id,),
            (source_id,),
            postclosure_bindings.arithmetic_input_source_digest,
        )
        postclosure_ids.append(arithmetic_id)
        coupling_id = add(
            "arithmetic-coupling",
            FormationHistoryEventKind.ARITHMETIC_COUPLING,
            (arithmetic_id,),
            (semantic_bridge_id, arithmetic_id),
            postclosure_bindings.arithmetic_coupling_digest,
        )
        postclosure_ids.append(coupling_id)
        ablation_id = add(
            "typed-ablation",
            FormationHistoryEventKind.TYPED_ABLATION,
            (coupling_id,),
            (coupling_id, "semantic-ablation-contract"),
            postclosure_bindings.typed_ablation_digest,
        )
        postclosure_ids.append(ablation_id)
        retained_id = add(
            "retained-difference",
            FormationHistoryEventKind.RETAINED_DIFFERENCE,
            (coupling_id,),
            (coupling_id, "semantic-intervention-plan"),
            postclosure_bindings.retained_difference_digest,
        )
        postclosure_ids.append(retained_id)
        phase_id = add(
            "residue-phase-effect",
            FormationHistoryEventKind.RESIDUE_PHASE_EFFECT,
            (retained_id,),
            (retained_id,),
            postclosure_bindings.residue_phase_effect_digest,
        )
        postclosure_ids.append(phase_id)
        removal_id = add(
            "removal-dependence",
            FormationHistoryEventKind.REMOVAL_DEPENDENCE,
            (phase_id, ablation_id),
            (phase_id, ablation_id),
            postclosure_bindings.removal_dependence_digest,
        )
        postclosure_ids.append(removal_id)
        future_parent = removal_id

    criterion_id = None
    result_id = None
    if witnessed:
        criterion_id = add(
            "decisive-criterion",
            FormationHistoryEventKind.DECISIVE_CRITERION,
            (future_parent,),
            (),
            criterion_payload_digest,
        )
        result_id = add(
            "later-result",
            FormationHistoryEventKind.LATER_RESULT,
            (future_parent, criterion_id),
            (future_parent, criterion_id),
            later_result_payload_digest,
        )
    captured = tuple(events)
    if len(captured) > plan.max_events:
        raise ValueError("p3og-formation-history-event-limit")
    past, future = _causal_sets(captured, terminal_id)
    if witnessed and (criterion_id in past or result_id in past):
        raise ValueError("p3og-formation-history-future-leak")
    required_past = {
        source_id,
        autonomous_id,
        formation_contract_id,
        pool_id,
        blind_seed_id,
        selector_law_id,
        selection_closure_id,
        selection_source_id,
        available_id,
        plan_id,
        selection_id,
        consumed_id,
        formation_source_id,
    }
    required_past.update(precommitment_ids)
    required_past.update(
        f"formation-tick-{i}"
        for i in range(1, len(formation_evidence.ticks) + 1)
    )
    if not required_past.issubset(past):
        raise ValueError("p3og-formation-history-missing-formation-ancestry")
    if witnessed and (criterion_id not in future or result_id not in future):
        raise ValueError("p3og-formation-history-future-placement")
    if postclosure_ids and not set(postclosure_ids).issubset(future):
        raise ValueError("p3og-formation-history-postclosure-placement")
    table = {event.event_id: event for event in captured}
    future_seals = {item for item in (criterion_id, result_id) if item is not None}
    for event_id in (*past, terminal_id):
        if future_seals.intersection(
            table[event_id].source_closure.transitive_source_event_ids
        ):
            raise ValueError("p3og-formation-history-future-source-leak")
    if refuted and future:
        raise ValueError("p3og-formation-history-refuted-future")

    ancestry = formation_history_digest(
        "formation-history-ancestry",
        plan.plan_digest,
        formation_source.source_digest,
        formation_evidence.evidence_digest,
        captured,
        terminal_id,
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
        terminal_id,
        terminal_id if witnessed else None,
        criterion_id,
        result_id,
        past,
        future,
        (
            FormationHistoryStatus.WITNESSED
            if witnessed
            else FormationHistoryStatus.REFUTED
        ),
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
    criterion_payload_digest: str | None,
    later_result_payload_digest: str | None,
    evidence: P3OGFormationHistoryEvidence,
    postclosure_bindings: FormationHistoryPostClosureBindings | None = None,
) -> P3OGFormationHistoryEvidence:
    """Freshly rebuild the one-shot DAG and any post-closure future seals."""
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
            postclosure_bindings,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-formation-history-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-formation-history-evidence-drift")
    return replace(expected)
