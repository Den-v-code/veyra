"""Matched post-closure semantic intervention replay for bounded P3-OG."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationBinding,
    P3OGNativeFormationContract,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_runtime import (
    semantic_ablate_maintenance,
    validate_semantic_ablation_contract,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    P3OGSemanticAblationContract,
    SemanticAblationReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    semantic_alive,
    semantic_couple,
    semantic_tick,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
    SemanticCouplingReceipt,
    SemanticTickReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_runtime import (
    validate_p3og_semantic_formation_bridge_evidence,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationBridgeEvidence,
)
from .prime_power_observer_genesis_p3og_semantic_formation_history_runtime import (
    semantic_formation_history_closure_payload_digest,
    validate_semantic_formation_history_plan,
)
from .prime_power_observer_genesis_p3og_semantic_formation_history_types import (
    P3OGSemanticFormationHistoryPlan,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import P3OGSource
from .prime_power_observer_genesis_p3og_matched_post_closure_codec import (
    matched_post_closure_digest,
)
from .prime_power_observer_genesis_p3og_matched_post_closure_types import (
    MatchedPostClosureEvent,
    MatchedPostClosureEventKind,
    MatchedPostClosureStatus,
    P3OGMatchedPostClosureEvidence,
    P3OGMatchedPostClosurePlan,
    P3OG_MATCHED_POST_CLOSURE_NONCLAIMS,
)

PLAN_VERSION = "p3og-matched-post-closure-plan-v1"
EVIDENCE_VERSION = "p3og-matched-post-closure-evidence-v1"
CONTINUATION_RULE_ID = "same-semantic-tick-operator-for-maintenance-credit-horizon-v1"
OBSERVATION_RULE_ID = "same-semantic-coupling-input-zero-after-continuation-v1"
GRAPH_RULE_ID = "precommitted-ablation-fork-after-exact-semantic-first-closure-v1"
OBSERVATION_INPUT = 0
MAX_EVENTS = 160
MAX_PARENTS_PER_EVENT = 4


def p3og_matched_post_closure_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    history_plan: P3OGSemanticFormationHistoryPlan,
    ablation_contract: P3OGSemanticAblationContract,
) -> P3OGMatchedPostClosurePlan:
    """Commit the matched branch grammar and horizon before selection."""
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
    ) = validate_semantic_formation_history_plan(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
    )
    source, autonomous_source, semantic_contract, ablation_contract = (
        validate_semantic_ablation_contract(
            source,
            autonomous_source,
            semantic_contract,
            ablation_contract,
        )
    )
    steps = source.maintenance_credit
    fields = (
        PLAN_VERSION,
        history_plan.plan_digest,
        ablation_contract.contract_digest,
        history_plan.lineage_id,
        history_plan.scope_digest,
        CONTINUATION_RULE_ID,
        steps,
        OBSERVATION_RULE_ID,
        OBSERVATION_INPUT,
        GRAPH_RULE_ID,
        MAX_EVENTS,
        MAX_PARENTS_PER_EVENT,
    )
    return P3OGMatchedPostClosurePlan(
        *fields,
        matched_post_closure_digest("matched-post-closure-plan", *fields),
    )


def validate_matched_post_closure_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    history_plan: P3OGSemanticFormationHistoryPlan,
    ablation_contract: P3OGSemanticAblationContract,
    plan: P3OGMatchedPostClosurePlan,
) -> tuple[
    P3OGSource,
    P3OGAutonomousTickSource,
    P3OGSemanticConfigurationContract,
    P3OGNativeFormationContract,
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationHistoryPlan,
    P3OGSemanticAblationContract,
    P3OGMatchedPostClosurePlan,
]:
    if type(plan) is not P3OGMatchedPostClosurePlan:
        raise ValueError("p3og-matched-post-closure-plan-type")
    try:
        expected = p3og_matched_post_closure_plan(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
            history_plan,
            ablation_contract,
        )
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-matched-post-closure-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-matched-post-closure-plan-drift")
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
    ) = validate_semantic_formation_history_plan(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
    )
    source, autonomous_source, semantic_contract, ablation_contract = (
        validate_semantic_ablation_contract(
            source,
            autonomous_source,
            semantic_contract,
            ablation_contract,
        )
    )
    return (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
        ablation_contract,
        replace(expected),
    )


def _event(
    plan: P3OGMatchedPostClosurePlan,
    event_id: str,
    kind: MatchedPostClosureEventKind,
    parents: tuple[str, ...],
    logical_time: int,
    payload_digest: str,
) -> MatchedPostClosureEvent:
    if type(event_id) is not str or not event_id or len(event_id) > 128:
        raise ValueError("p3og-matched-post-closure-event-id")
    if type(kind) is not MatchedPostClosureEventKind:
        raise ValueError("p3og-matched-post-closure-event-kind")
    if (
        type(parents) is not tuple
        or len(parents) > plan.max_parents_per_event
        or len(parents) != len(set(parents))
        or event_id in parents
    ):
        raise ValueError("p3og-matched-post-closure-event-parents")
    if type(logical_time) is not int or logical_time < 0:
        raise ValueError("p3og-matched-post-closure-event-time")
    if type(payload_digest) is not str or len(payload_digest) != 64:
        raise ValueError("p3og-matched-post-closure-event-payload")
    try:
        int(payload_digest, 16)
    except ValueError as exc:
        raise ValueError("p3og-matched-post-closure-event-payload") from exc
    fields = (
        event_id,
        kind,
        parents,
        logical_time,
        plan.lineage_id,
        plan.scope_digest,
        payload_digest,
    )
    return MatchedPostClosureEvent(
        *fields,
        matched_post_closure_digest("matched-post-closure-event", *fields),
    )


def build_p3og_matched_post_closure_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    history_plan: P3OGSemanticFormationHistoryPlan,
    ablation_contract: P3OGSemanticAblationContract,
    match_plan: P3OGMatchedPostClosurePlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
) -> P3OGMatchedPostClosureEvidence:
    """Fork one exact semantic first-closure state into matched control/ablation histories."""
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
        ablation_contract,
        match_plan,
    ) = validate_matched_post_closure_plan(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
        ablation_contract,
        match_plan,
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
    try:
        seed = source.seeds[binding.selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-matched-post-closure-selection") from exc
    source, seed = validate_seed(source, seed)
    if seed.seed_digest != binding.selected_seed_digest:
        raise ValueError("p3og-matched-post-closure-selected-seed")

    control_initial = bridge_evidence.final_configuration
    if not compare_digest(
        canonical_bytes(control_initial),
        canonical_bytes(bridge_evidence.q_seed),
    ):
        raise ValueError("p3og-matched-post-closure-not-at-first-closure")
    ablated_initial, ablation_receipt = semantic_ablate_maintenance(
        source,
        autonomous_source,
        semantic_contract,
        ablation_contract,
        seed,
        control_initial,
    )

    control = control_initial
    ablated = ablated_initial
    control_ticks: list[SemanticTickReceipt] = []
    ablated_ticks: list[SemanticTickReceipt] = []
    first_transition_divergence_step: int | None = None
    for step in range(1, match_plan.continuation_steps + 1):
        control, control_tick = semantic_tick(
            source,
            autonomous_source,
            semantic_contract,
            seed,
            control,
        )
        ablated, ablated_tick = semantic_tick(
            source,
            autonomous_source,
            semantic_contract,
            seed,
            ablated,
        )
        control_ticks.append(control_tick)
        ablated_ticks.append(ablated_tick)
        if (
            first_transition_divergence_step is None
            and control_tick.selected_kind is not ablated_tick.selected_kind
        ):
            first_transition_divergence_step = step

    control_final = control
    ablated_final = ablated
    control_alive = semantic_alive(source, seed, control_final)
    ablated_alive = semantic_alive(source, seed, ablated_final)
    liveness_diverged = control_alive and not ablated_alive

    control_observation_after, control_observation = semantic_couple(
        source,
        autonomous_source,
        semantic_contract,
        seed,
        control_final,
        match_plan.observation_input,
    )
    ablated_observation_after, ablated_observation = semantic_couple(
        source,
        autonomous_source,
        semantic_contract,
        seed,
        ablated_final,
        match_plan.observation_input,
    )
    response_diverged = (
        control_observation.response is not None
        and ablated_observation.response is None
    )
    witnessed = (
        first_transition_divergence_step is not None
        and liveness_diverged
        and response_diverged
    )
    status = (
        MatchedPostClosureStatus.WITNESSED
        if witnessed
        else MatchedPostClosureStatus.REFUTED
    )
    reason = (
        "ablation-causes-later-transition-liveness-and-response-loss"
        if witnessed
        else "matched-continuation-does-not-witness-maintenance-efficacy-loss"
    )
    closure_payload = semantic_formation_history_closure_payload_digest(
        bridge_contract,
        binding,
        bridge_evidence,
    )

    events: list[MatchedPostClosureEvent] = []

    def add(event_id, kind, parents, payload):
        event = _event(match_plan, event_id, kind, parents, len(events), payload)
        events.append(event)
        return event.event_id

    history_plan_id = add(
        "formation-history-plan",
        MatchedPostClosureEventKind.FORMATION_HISTORY_PLAN_COMMIT,
        (),
        history_plan.plan_digest,
    )
    ablation_contract_id = add(
        "ablation-contract",
        MatchedPostClosureEventKind.ABLATION_CONTRACT_COMMIT,
        (history_plan_id,),
        ablation_contract.contract_digest,
    )
    match_plan_id = add(
        "match-plan",
        MatchedPostClosureEventKind.MATCH_PLAN_COMMIT,
        (ablation_contract_id,),
        match_plan.plan_digest,
    )
    selection_id = add(
        "selection",
        MatchedPostClosureEventKind.SELECTION,
        (match_plan_id,),
        binding.selection.receipt_digest,
    )
    binding_id = add(
        "formation-binding",
        MatchedPostClosureEventKind.FORMATION_BINDING,
        (selection_id,),
        binding.binding_digest,
    )
    bridge_id = add(
        "semantic-formation-bridge",
        MatchedPostClosureEventKind.SEMANTIC_FORMATION_BRIDGE,
        (binding_id,),
        bridge_evidence.evidence_digest,
    )
    closure_id = add(
        "first-closure",
        MatchedPostClosureEventKind.FIRST_CLOSURE,
        (bridge_id,),
        closure_payload,
    )
    control_parent = add(
        "unablated-branch",
        MatchedPostClosureEventKind.UNABLATED_BRANCH,
        (closure_id,),
        control_initial.configuration_digest,
    )
    ablation_id = add(
        "ablation",
        MatchedPostClosureEventKind.ABLATION,
        (closure_id,),
        ablation_receipt.receipt_digest,
    )
    ablated_parent = ablation_id
    for step, (control_tick, ablated_tick) in enumerate(
        zip(control_ticks, ablated_ticks, strict=True),
        start=1,
    ):
        control_parent = add(
            f"control-tick-{step}",
            MatchedPostClosureEventKind.CONTROL_TICK,
            (control_parent,),
            control_tick.receipt_digest,
        )
        ablated_parent = add(
            f"ablated-tick-{step}",
            MatchedPostClosureEventKind.ABLATED_TICK,
            (ablated_parent,),
            ablated_tick.receipt_digest,
        )
    control_observation_id = add(
        "control-observation",
        MatchedPostClosureEventKind.CONTROL_OBSERVATION,
        (control_parent,),
        control_observation.receipt_digest,
    )
    ablated_observation_id = add(
        "ablated-observation",
        MatchedPostClosureEventKind.ABLATED_OBSERVATION,
        (ablated_parent,),
        ablated_observation.receipt_digest,
    )
    result_payload = matched_post_closure_digest(
        "matched-result",
        first_transition_divergence_step,
        liveness_diverged,
        response_diverged,
        status,
        reason,
        control_observation.receipt_digest,
        ablated_observation.receipt_digest,
    )
    result_id = add(
        "matched-result",
        MatchedPostClosureEventKind.MATCHED_RESULT,
        (control_observation_id, ablated_observation_id),
        result_payload,
    )
    captured = tuple(events)
    if len(captured) > match_plan.max_events:
        raise ValueError("p3og-matched-post-closure-event-limit")
    table = {event.event_id: event for event in captured}
    if len(table) != len(captured):
        raise ValueError("p3og-matched-post-closure-event-table")
    for event in captured:
        for parent in event.parent_ids:
            if parent not in table or table[parent].logical_time >= event.logical_time:
                raise ValueError("p3og-matched-post-closure-parent-order")
    if table[ablation_id].parent_ids != (closure_id,):
        raise ValueError("p3og-matched-post-closure-ablation-cut")
    if table[control_observation_id].logical_time <= table[closure_id].logical_time:
        raise ValueError("p3og-matched-post-closure-control-observation-cut")
    if table[ablated_observation_id].logical_time <= table[ablation_id].logical_time:
        raise ValueError("p3og-matched-post-closure-ablated-observation-cut")

    ancestry = matched_post_closure_digest(
        "matched-post-closure-ancestry",
        match_plan.plan_digest,
        bridge_evidence.evidence_digest,
        closure_payload,
        control_initial,
        ablated_initial,
        ablation_receipt,
        tuple(control_ticks),
        tuple(ablated_ticks),
        control_final,
        ablated_final,
        control_observation_after,
        ablated_observation_after,
        control_observation,
        ablated_observation,
        captured,
    )
    fields = (
        EVIDENCE_VERSION,
        match_plan.plan_digest,
        bridge_evidence.evidence_digest,
        closure_payload,
        control_initial,
        ablated_initial,
        ablation_receipt,
        tuple(control_ticks),
        tuple(ablated_ticks),
        control_final,
        ablated_final,
        control_observation_after,
        ablated_observation_after,
        control_observation,
        ablated_observation,
        first_transition_divergence_step,
        liveness_diverged,
        response_diverged,
        status,
        reason,
        captured,
        closure_id,
        ablation_id,
        control_observation_id,
        ablated_observation_id,
        result_id,
        ancestry,
        0,
        P3OG_MATCHED_POST_CLOSURE_NONCLAIMS,
    )
    return P3OGMatchedPostClosureEvidence(
        *fields,
        matched_post_closure_digest("matched-post-closure-evidence", *fields),
    )


def _preflight_evidence(evidence: P3OGMatchedPostClosureEvidence) -> None:
    try:
        events = evidence.events
        control_ticks = evidence.control_ticks
        ablated_ticks = evidence.ablated_ticks
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-matched-post-closure-evidence-fields") from exc
    if (
        type(events) is not tuple
        or len(events) > MAX_EVENTS
        or type(control_ticks) is not tuple
        or type(ablated_ticks) is not tuple
        or len(control_ticks) > 64
        or len(ablated_ticks) > 64
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-matched-post-closure-evidence-shape")
    for event in events:
        if type(event) is not MatchedPostClosureEvent:
            raise ValueError("p3og-matched-post-closure-event-type")
        if type(event.parent_ids) is not tuple or len(event.parent_ids) > MAX_PARENTS_PER_EVENT:
            raise ValueError("p3og-matched-post-closure-event-shape")
    for tick in control_ticks + ablated_ticks:
        if type(tick) is not SemanticTickReceipt:
            raise ValueError("p3og-matched-post-closure-tick-type")
    if type(evidence.ablation_receipt) is not SemanticAblationReceipt:
        raise ValueError("p3og-matched-post-closure-ablation-receipt-type")
    if (
        type(evidence.control_observation) is not SemanticCouplingReceipt
        or type(evidence.ablated_observation) is not SemanticCouplingReceipt
    ):
        raise ValueError("p3og-matched-post-closure-observation-type")
    for configuration in (
        evidence.control_initial,
        evidence.ablated_initial,
        evidence.control_final,
        evidence.ablated_final,
        evidence.control_observation_after,
        evidence.ablated_observation_after,
    ):
        if type(configuration) is not P3OGSemanticConfiguration:
            raise ValueError("p3og-matched-post-closure-configuration-type")


def validate_p3og_matched_post_closure_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    history_plan: P3OGSemanticFormationHistoryPlan,
    ablation_contract: P3OGSemanticAblationContract,
    match_plan: P3OGMatchedPostClosurePlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    evidence: P3OGMatchedPostClosureEvidence,
) -> P3OGMatchedPostClosureEvidence:
    """Freshly rebuild the complete matched history and reject any drift."""
    if type(evidence) is not P3OGMatchedPostClosureEvidence:
        raise ValueError("p3og-matched-post-closure-evidence-type")
    _preflight_evidence(evidence)
    try:
        expected = build_p3og_matched_post_closure_evidence(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
            history_plan,
            ablation_contract,
            match_plan,
            binding,
            formation_source,
            formation_evidence,
            bridge_evidence,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-matched-post-closure-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-matched-post-closure-evidence-drift")
    return replace(expected)
