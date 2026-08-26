"""Focused/hostile tests for matched post-closure semantic intervention pressure."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_matched_post_closure import (
    MatchedPostClosureStatus,
    P3OG_MATCHED_POST_CLOSURE_NONCLAIMS,
    build_p3og_matched_post_closure_evidence,
    p3og_matched_post_closure_plan,
    validate_p3og_matched_post_closure_evidence,
)
from src.core.prime_power_observer_genesis_p3og_matched_post_closure_types import (
    MatchedPostClosureEvent,
)
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    p3og_native_formation_binding,
    p3og_native_formation_contract,
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_semantic_ablation import (
    p3og_semantic_ablation_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_history import (
    p3og_semantic_formation_history_plan,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
)


def _fixture(*, disabled_low: TransitionKind = TransitionKind.IDLE):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="matched-post-closure-v1",
        seed_rows=(("alpha", (0, 1, 0)),),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=(TransitionKind.IDLE,),
    )
    rules = (
        autonomous_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.HIGH,
            TransitionKind.IDLE,
        ),
        autonomous_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.LOW,
            TransitionKind.MAINTAIN,
        ),
        autonomous_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.HIGH,
            TransitionKind.IDLE,
        ),
        autonomous_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.LOW,
            disabled_low,
        ),
    )
    autonomous = p3og_autonomous_tick_source(source, rules)
    semantic_contract = p3og_semantic_configuration_contract(source, autonomous)
    formation_contract = p3og_native_formation_contract(source, autonomous)
    bridge_contract = p3og_semantic_formation_bridge_contract(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
    )
    history_plan = p3og_semantic_formation_history_plan(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
        bridge_contract,
    )
    ablation_contract = p3og_semantic_ablation_contract(
        source,
        autonomous,
        semantic_contract,
    )
    match_plan = p3og_matched_post_closure_plan(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
        ablation_contract,
    )
    binding = p3og_native_formation_binding(source, autonomous, formation_contract)
    formation_source = p3og_native_formation_source(source, autonomous)
    formation = run_p3og_native_formation(source, autonomous, formation_source)
    bridge = build_p3og_semantic_formation_bridge_evidence(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
        bridge_contract,
        binding,
        formation_source,
        formation,
    )
    return (
        source,
        autonomous,
        semantic_contract,
        formation_contract,
        bridge_contract,
        history_plan,
        ablation_contract,
        match_plan,
        binding,
        formation_source,
        formation,
        bridge,
    )


def _build(fixture):
    return build_p3og_matched_post_closure_evidence(*fixture)


def test_ablation_after_exact_closure_causes_later_matched_efficacy_loss() -> None:
    fixture = _fixture()
    evidence = _build(fixture)

    assert evidence.status is MatchedPostClosureStatus.WITNESSED
    assert evidence.reason == "ablation-causes-later-transition-liveness-and-response-loss"
    assert evidence.first_transition_divergence_step == 2
    assert evidence.liveness_diverged is True
    assert evidence.response_diverged is True
    assert tuple(tick.selected_kind for tick in evidence.control_ticks) == (
        TransitionKind.IDLE,
        TransitionKind.MAINTAIN,
    )
    assert tuple(tick.selected_kind for tick in evidence.ablated_ticks) == (
        TransitionKind.IDLE,
        TransitionKind.IDLE,
    )
    assert evidence.control_final.boundary is BoundaryState.ALIVE
    assert evidence.ablated_final.boundary is BoundaryState.REMOVED
    assert evidence.control_observation.response == 0
    assert evidence.ablated_observation.response is None
    assert evidence.promotions == 0


def test_ablation_is_strictly_after_closure_and_before_ablated_observation() -> None:
    evidence = _build(_fixture())
    table = {event.event_id: event for event in evidence.events}

    closure = table[evidence.closure_event_id]
    ablation = table[evidence.ablation_event_id]
    ablated_observation = table[evidence.ablated_observation_event_id]
    assert ablation.parent_ids == (closure.event_id,)
    assert closure.logical_time < ablation.logical_time < ablated_observation.logical_time
    assert table["match-plan"].logical_time < table["selection"].logical_time
    assert table["ablation-contract"].logical_time < table["selection"].logical_time


def test_same_witnessed_formation_can_refute_later_ablation_efficacy() -> None:
    evidence = _build(_fixture(disabled_low=TransitionKind.MAINTAIN))

    assert evidence.status is MatchedPostClosureStatus.REFUTED
    assert evidence.reason == "matched-continuation-does-not-witness-maintenance-efficacy-loss"
    assert evidence.first_transition_divergence_step is None
    assert evidence.liveness_diverged is False
    assert evidence.response_diverged is False
    assert evidence.control_final.boundary is BoundaryState.ALIVE
    assert evidence.ablated_final.boundary is BoundaryState.ALIVE
    assert tuple(tick.selected_kind for tick in evidence.control_ticks) == (
        TransitionKind.IDLE,
        TransitionKind.MAINTAIN,
    )
    assert tuple(tick.selected_kind for tick in evidence.ablated_ticks) == (
        TransitionKind.IDLE,
        TransitionKind.MAINTAIN,
    )
    assert evidence.control_observation.response == evidence.ablated_observation.response == 0


def test_match_plan_is_selection_free_and_horizon_is_precommitted_from_source() -> None:
    fixture = _fixture()
    source = fixture[0]
    history_plan = fixture[5]
    ablation_contract = fixture[6]
    plan = fixture[7]

    names = {field.name for field in fields(plan)}
    assert {"selection", "selected_seed_digest", "status", "expected_status"}.isdisjoint(names)
    assert plan.semantic_formation_history_plan_digest == history_plan.plan_digest
    assert plan.semantic_ablation_contract_digest == ablation_contract.contract_digest
    assert plan.lineage_id == history_plan.lineage_id
    assert plan.scope_digest == history_plan.scope_digest
    assert plan.continuation_steps == source.maintenance_credit == 2
    assert plan.observation_input == 0


def test_fresh_validation_rejects_spliced_ablation_and_graph_drift() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    replay = validate_p3og_matched_post_closure_evidence(*fixture, evidence)
    assert replay == evidence
    assert replay is not evidence

    forged_receipt = replace(
        evidence.ablation_receipt,
        after_configuration_digest="f" * 64,
    )
    with pytest.raises(ValueError):
        validate_p3og_matched_post_closure_evidence(
            *fixture,
            replace(evidence, ablation_receipt=forged_receipt),
        )

    events = list(evidence.events)
    index = next(i for i, event in enumerate(events) if event.event_id == "ablation")
    events[index] = replace(events[index], parent_ids=("formation-binding",))
    with pytest.raises(ValueError):
        validate_p3og_matched_post_closure_evidence(
            *fixture,
            replace(evidence, events=tuple(events)),
        )


def test_hostile_nested_event_fails_before_codec_callback() -> None:
    fixture = _fixture()
    evidence = _build(fixture)

    class HostileEvent(MatchedPostClosureEvent):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileEvent)
    with pytest.raises(ValueError):
        validate_p3og_matched_post_closure_evidence(
            *fixture,
            replace(evidence, events=(hostile,)),
        )


def test_claim_boundary_stays_below_token_role_hap_and_full_def_og() -> None:
    evidence = _build(_fixture())
    assert evidence.nonclaims == P3OG_MATCHED_POST_CLOSURE_NONCLAIMS
    assert {
        "full-def-og-006-discharge",
        "full-def-og-007-discharge",
        "full-def-og-008-discharge",
        "full-def-og-009-discharge",
        "same-historical-token",
        "endogenous-observer-role",
        "n0-or-hap-lift",
        "promotion",
    }.issubset(evidence.nonclaims)
