"""Typed semantic P3-OG formation-history replay graph v3."""

from __future__ import annotations

from collections import deque
from dataclasses import fields, is_dataclass, replace
from enum import Enum
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes
from .prime_power_observer_genesis_p3og_native_formation_source import (
    validate_legacy_source_against_contract_binding,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationBinding,
    P3OGNativeFormationContract,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_native_formation_validation import (
    validate_p3og_native_formation_evidence,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfigurationContract,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_runtime import (
    validate_p3og_semantic_formation_bridge_evidence,
    validate_semantic_formation_bridge_contract,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationBridgeEvidence,
    SemanticFormationBridgeStatus,
)
from .prime_power_observer_genesis_p3og_semantic_formation_history_codec import (
    semantic_formation_history_digest,
)
from .prime_power_observer_genesis_p3og_semantic_formation_history_types import (
    P3OGSemanticFormationHistoryEvidence,
    P3OGSemanticFormationHistoryPlan,
    P3OG_SEMANTIC_FORMATION_HISTORY_NONCLAIMS,
    SemanticFormationHistoryEvent,
    SemanticFormationHistoryEventKind,
    SemanticFormationHistoryStatus,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

PLAN_VERSION = "p3og-semantic-formation-history-plan-v3"
EVIDENCE_VERSION = "p3og-semantic-formation-history-evidence-v3"
GRAPH_RULE_ID = "preselection-semantic-contracts-binding-q-sem-ticks-first-return-v3"
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


def p3og_semantic_formation_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
) -> P3OGSemanticFormationHistoryPlan:
    """Commit the whole semantic-history graph grammar before selection."""
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
    ) = validate_semantic_formation_bridge_contract(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
    )
    lineage_id = semantic_formation_history_digest(
        "semantic-formation-history-lineage",
        source.source_digest,
        autonomous_source.source_digest,
        semantic_contract.contract_digest,
        formation_contract.contract_digest,
        bridge_contract.contract_digest,
        GRAPH_RULE_ID,
    )
    scope_digest = semantic_formation_history_digest(
        "semantic-formation-history-scope",
        source.source_digest,
        autonomous_source.source_digest,
        semantic_contract.contract_digest,
        formation_contract.contract_digest,
        bridge_contract.contract_digest,
        GRAPH_RULE_ID,
    )
    plan_fields = (
        PLAN_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        semantic_contract.contract_digest,
        formation_contract.contract_digest,
        bridge_contract.contract_digest,
        lineage_id,
        scope_digest,
        GRAPH_RULE_ID,
        MAX_EVENTS,
        MAX_PARENTS_PER_EVENT,
    )
    return P3OGSemanticFormationHistoryPlan(
        *plan_fields,
        semantic_formation_history_digest(
            "semantic-formation-history-plan",
            *plan_fields,
        ),
    )


def validate_semantic_formation_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    plan: P3OGSemanticFormationHistoryPlan,
) -> tuple[
    P3OGSource,
    P3OGAutonomousTickSource,
    P3OGSemanticConfigurationContract,
    P3OGNativeFormationContract,
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationHistoryPlan,
]:
    if type(plan) is not P3OGSemanticFormationHistoryPlan:
        raise ValueError("p3og-semantic-formation-history-plan-type")
    try:
        expected = p3og_semantic_formation_history_plan(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
        )
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-formation-history-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-formation-history-plan-drift")
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
    ) = validate_semantic_formation_bridge_contract(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
    )
    return (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        replace(expected),
    )


def _event(
    plan: P3OGSemanticFormationHistoryPlan,
    event_id: str,
    kind: SemanticFormationHistoryEventKind,
    parents: tuple[str, ...],
    logical_time: int,
    payload_digest: str,
) -> SemanticFormationHistoryEvent:
    if type(event_id) is not str or not event_id or len(event_id) > 128:
        raise ValueError("p3og-semantic-formation-history-event-id")
    if type(kind) is not SemanticFormationHistoryEventKind:
        raise ValueError("p3og-semantic-formation-history-event-kind")
    if (
        type(parents) is not tuple
        or len(parents) > plan.max_parents_per_event
        or len(parents) != len(set(parents))
    ):
        raise ValueError("p3og-semantic-formation-history-event-parents")
    if event_id in parents or type(logical_time) is not int or logical_time < 0:
        raise ValueError("p3og-semantic-formation-history-event-shape")
    payload_digest = _hex_digest(
        payload_digest,
        "p3og-semantic-formation-history-event-payload",
    )
    event_fields = (
        event_id,
        kind,
        parents,
        logical_time,
        plan.lineage_id,
        plan.scope_digest,
        payload_digest,
    )
    return SemanticFormationHistoryEvent(
        *event_fields,
        semantic_formation_history_digest(
            "semantic-formation-history-event",
            *event_fields,
        ),
    )


def _causal_sets(
    events: tuple[SemanticFormationHistoryEvent, ...],
    closure_event_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    table = {event.event_id: event for event in events}
    if len(table) != len(events) or closure_event_id not in table:
        raise ValueError("p3og-semantic-formation-history-event-table")
    children = {name: [] for name in table}
    for event in events:
        for parent in event.parent_ids:
            if parent not in table:
                raise ValueError("p3og-semantic-formation-history-unknown-parent")
            if table[parent].logical_time >= event.logical_time:
                raise ValueError("p3og-semantic-formation-history-nonmonotone-parent")
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


def semantic_formation_history_closure_payload_digest(
    bridge_contract: P3OGSemanticFormationBridgeContract,
    binding: P3OGNativeFormationBinding,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
) -> str:
    """Commit the exact first-return cut, not the whole post-hoc bridge certificate."""
    if (
        type(bridge_contract) is not P3OGSemanticFormationBridgeContract
        or type(binding) is not P3OGNativeFormationBinding
        or type(bridge_evidence) is not P3OGSemanticFormationBridgeEvidence
        or not bridge_evidence.steps
    ):
        raise ValueError("p3og-semantic-formation-history-closure-payload-shape")
    return semantic_formation_history_digest(
        "first-closure-payload",
        bridge_contract.contract_digest,
        binding.binding_digest,
        bridge_evidence.q_seed.configuration_digest,
        bridge_evidence.first_closure_step,
        bridge_evidence.steps[-1].receipt_digest,
    )


def build_p3og_semantic_formation_history_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    plan: P3OGSemanticFormationHistoryPlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    criterion_payload_digest: str,
    later_result_payload_digest: str,
) -> P3OGSemanticFormationHistoryEvidence:
    """Build one typed DAG around an exact semantic first-return bridge."""
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        plan,
    ) = validate_semantic_formation_history_plan(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        plan,
    )
    formation_contract, binding, formation_source = (
        validate_legacy_source_against_contract_binding(
            source,
            autonomous_source,
            formation_contract,
            binding,
            formation_source,
        )
    )
    formation_evidence = validate_p3og_native_formation_evidence(
        source,
        autonomous_source,
        formation_source,
        formation_evidence,
    )
    bridge_evidence = validate_p3og_semantic_formation_bridge_evidence(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        binding,
        formation_source,
        formation_evidence,
        bridge_evidence,
    )
    if bridge_evidence.status is not SemanticFormationBridgeStatus.WITNESSED:
        raise ValueError("p3og-semantic-formation-history-requires-witnessed-bridge")
    if not bridge_evidence.steps:
        raise ValueError("p3og-semantic-formation-history-empty-genealogy")

    criterion_payload_digest = _hex_digest(
        criterion_payload_digest,
        "p3og-semantic-formation-history-criterion-digest",
    )
    later_result_payload_digest = _hex_digest(
        later_result_payload_digest,
        "p3og-semantic-formation-history-result-digest",
    )
    required_events = len(bridge_evidence.steps) + 11
    if required_events > plan.max_events:
        raise ValueError("p3og-semantic-formation-history-event-limit")

    preclosure_digests = _digest_inventory(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        plan,
        binding,
        formation_source,
        formation_evidence,
        bridge_evidence,
    )
    if (
        criterion_payload_digest in preclosure_digests
        or later_result_payload_digest in preclosure_digests
    ):
        raise ValueError("p3og-semantic-formation-history-future-seal-preloaded")

    closure_payload = semantic_formation_history_closure_payload_digest(
        bridge_contract,
        binding,
        bridge_evidence,
    )
    events: list[SemanticFormationHistoryEvent] = []

    def add(event_id, kind, parents, payload):
        event = _event(plan, event_id, kind, parents, len(events), payload)
        events.append(event)
        return event.event_id

    source_id = add(
        "source",
        SemanticFormationHistoryEventKind.SOURCE_COMMIT,
        (),
        source.source_digest,
    )
    autonomous_id = add(
        "autonomous-law",
        SemanticFormationHistoryEventKind.AUTONOMOUS_LAW_COMMIT,
        (source_id,),
        autonomous_source.source_digest,
    )
    semantic_contract_id = add(
        "semantic-configuration-contract",
        SemanticFormationHistoryEventKind.SEMANTIC_CONFIGURATION_CONTRACT_COMMIT,
        (autonomous_id,),
        semantic_contract.contract_digest,
    )
    formation_contract_id = add(
        "formation-contract",
        SemanticFormationHistoryEventKind.FORMATION_CONTRACT_COMMIT,
        (autonomous_id,),
        formation_contract.contract_digest,
    )
    bridge_contract_id = add(
        "semantic-formation-bridge-contract",
        SemanticFormationHistoryEventKind.SEMANTIC_FORMATION_BRIDGE_CONTRACT_COMMIT,
        (semantic_contract_id, formation_contract_id),
        bridge_contract.contract_digest,
    )
    plan_id = add(
        "history-plan",
        SemanticFormationHistoryEventKind.HISTORY_PLAN_COMMIT,
        (bridge_contract_id,),
        plan.plan_digest,
    )
    selection_id = add(
        "selection",
        SemanticFormationHistoryEventKind.SELECTION,
        (plan_id,),
        binding.selection.receipt_digest,
    )
    binding_id = add(
        "formation-binding",
        SemanticFormationHistoryEventKind.FORMATION_BINDING,
        (selection_id,),
        binding.binding_digest,
    )
    previous = binding_id
    for index, step in enumerate(bridge_evidence.steps, start=1):
        previous = add(
            f"semantic-formation-tick-{index}",
            SemanticFormationHistoryEventKind.SEMANTIC_FORMATION_TICK,
            (previous,),
            step.receipt_digest,
        )
    closure_id = add(
        "first-closure",
        SemanticFormationHistoryEventKind.FIRST_CLOSURE,
        (previous,),
        closure_payload,
    )
    criterion_id = add(
        "decisive-criterion",
        SemanticFormationHistoryEventKind.DECISIVE_CRITERION,
        (closure_id,),
        criterion_payload_digest,
    )
    result_id = add(
        "later-result",
        SemanticFormationHistoryEventKind.LATER_RESULT,
        (closure_id, criterion_id),
        later_result_payload_digest,
    )
    captured = tuple(events)
    if len(captured) > plan.max_events:
        raise ValueError("p3og-semantic-formation-history-event-limit")

    past, future = _causal_sets(captured, closure_id)
    if criterion_id in past or result_id in past:
        raise ValueError("p3og-semantic-formation-history-future-leak")
    required_past = {
        source_id,
        autonomous_id,
        semantic_contract_id,
        formation_contract_id,
        bridge_contract_id,
        plan_id,
        selection_id,
        binding_id,
    }
    required_past.update(
        f"semantic-formation-tick-{index}"
        for index in range(1, len(bridge_evidence.steps) + 1)
    )
    if not required_past.issubset(past):
        raise ValueError("p3og-semantic-formation-history-missing-formation-ancestry")
    if criterion_id not in future or result_id not in future:
        raise ValueError("p3og-semantic-formation-history-future-placement")

    ancestry = semantic_formation_history_digest(
        "semantic-formation-history-ancestry",
        plan.plan_digest,
        binding.binding_digest,
        bridge_evidence.evidence_digest,
        closure_payload,
        captured,
        closure_id,
        past,
        future,
    )
    evidence_fields = (
        EVIDENCE_VERSION,
        plan.plan_digest,
        binding.binding_digest,
        bridge_evidence.evidence_digest,
        closure_payload,
        criterion_payload_digest,
        later_result_payload_digest,
        captured,
        closure_id,
        criterion_id,
        result_id,
        past,
        future,
        SemanticFormationHistoryStatus.WITNESSED,
        ancestry,
        0,
        P3OG_SEMANTIC_FORMATION_HISTORY_NONCLAIMS,
    )
    return P3OGSemanticFormationHistoryEvidence(
        *evidence_fields,
        semantic_formation_history_digest(
            "semantic-formation-history-evidence",
            *evidence_fields,
        ),
    )


def _preflight_history_evidence(
    evidence: P3OGSemanticFormationHistoryEvidence,
) -> None:
    try:
        events = evidence.events
        past = evidence.strict_past_event_ids
        future = evidence.future_event_ids
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-semantic-formation-history-evidence-fields") from exc
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
        raise ValueError("p3og-semantic-formation-history-evidence-shape")
    for event in events:
        if type(event) is not SemanticFormationHistoryEvent:
            raise ValueError("p3og-semantic-formation-history-event-type")
        if (
            type(event.parent_ids) is not tuple
            or len(event.parent_ids) > MAX_PARENTS_PER_EVENT
            or any(type(item) is not str for item in event.parent_ids)
            or type(event.event_id) is not str
            or type(event.kind) is not SemanticFormationHistoryEventKind
            or type(event.logical_time) is not int
            or type(event.lineage_id) is not str
            or type(event.scope_digest) is not str
            or type(event.payload_digest) is not str
            or type(event.event_digest) is not str
        ):
            raise ValueError("p3og-semantic-formation-history-event-shape")
    if any(type(item) is not str for item in past + future):
        raise ValueError("p3og-semantic-formation-history-id-shape")


def validate_p3og_semantic_formation_history_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    plan: P3OGSemanticFormationHistoryPlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    criterion_payload_digest: str,
    later_result_payload_digest: str,
    evidence: P3OGSemanticFormationHistoryEvidence,
) -> P3OGSemanticFormationHistoryEvidence:
    """Freshly rebuild the complete semantic formation DAG."""
    if type(evidence) is not P3OGSemanticFormationHistoryEvidence:
        raise ValueError("p3og-semantic-formation-history-evidence-type")
    _preflight_history_evidence(evidence)
    try:
        expected = build_p3og_semantic_formation_history_evidence(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
            plan,
            binding,
            formation_source,
            formation_evidence,
            bridge_evidence,
            criterion_payload_digest,
            later_result_payload_digest,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-formation-history-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-formation-history-evidence-drift")
    return replace(expected)
