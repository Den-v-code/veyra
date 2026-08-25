"""Focused/hostile tests for semantic P3-OG formation-history v3."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    p3og_native_formation_binding,
    p3og_native_formation_contract,
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_history import (
    build_p3og_semantic_formation_history_evidence,
    p3og_semantic_formation_history_plan,
    semantic_formation_history_closure_payload_digest,
    validate_p3og_semantic_formation_history_evidence,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_history_types import (
    SemanticFormationHistoryEvent,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _fixture():
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="semantic-formation-history-v3",
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
            TransitionKind.IDLE,
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
    plan = p3og_semantic_formation_history_plan(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
        bridge_contract,
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
        plan,
        binding,
        formation_source,
        formation,
        bridge,
    )


def _build(fixture, criterion="a" * 64, result="b" * 64):
    return build_p3og_semantic_formation_history_evidence(
        *fixture,
        criterion,
        result,
    )


def test_semantic_contracts_and_genealogy_are_strict_past_of_closure() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    ids = tuple(event.event_id for event in evidence.events)

    selection_index = ids.index("selection")
    for event_id in (
        "semantic-configuration-contract",
        "formation-contract",
        "semantic-formation-bridge-contract",
        "history-plan",
    ):
        assert ids.index(event_id) < selection_index
        assert event_id in evidence.strict_past_event_ids
    assert "formation-binding" in evidence.strict_past_event_ids
    assert "semantic-formation-tick-1" in evidence.strict_past_event_ids
    assert "semantic-formation-tick-2" in evidence.strict_past_event_ids
    assert "decisive-criterion" in evidence.future_event_ids
    assert "later-result" in evidence.future_event_ids
    assert len(evidence.events) == len(fixture[-1].steps) + 11
    assert evidence.promotions == 0
    assert "full-def-og-003-discharge" in evidence.nonclaims
    assert "full-def-og-009-discharge" in evidence.nonclaims


def test_first_closure_payload_binds_exact_cut_not_whole_bridge_certificate() -> None:
    fixture = _fixture()
    bridge_contract = fixture[4]
    binding = fixture[6]
    bridge = fixture[-1]
    evidence = _build(fixture)
    table = {event.event_id: event for event in evidence.events}
    closure = table[evidence.closure_event_id]

    expected = semantic_formation_history_closure_payload_digest(
        bridge_contract,
        binding,
        bridge,
    )
    assert evidence.closure_payload_digest == expected
    assert closure.payload_digest == expected
    assert closure.payload_digest != bridge.evidence_digest
    assert closure.parent_ids == (f"semantic-formation-tick-{len(bridge.steps)}",)


def test_history_plan_is_selection_free_and_binds_all_preselection_contracts() -> None:
    fixture = _fixture()
    semantic_contract = fixture[2]
    formation_contract = fixture[3]
    bridge_contract = fixture[4]
    plan = fixture[5]

    names = {field.name for field in fields(plan)}
    assert "selection" not in names
    assert "selected_seed_digest" not in names
    assert plan.semantic_configuration_contract_digest == semantic_contract.contract_digest
    assert plan.formation_contract_digest == formation_contract.contract_digest
    assert plan.semantic_formation_bridge_contract_digest == bridge_contract.contract_digest


def test_future_seals_cannot_reuse_preclosure_digest_inventory() -> None:
    fixture = _fixture()
    binding = fixture[6]
    bridge = fixture[-1]

    with pytest.raises(ValueError, match="future-seal-preloaded"):
        _build(fixture, criterion=binding.binding_digest)
    with pytest.raises(ValueError, match="future-seal-preloaded"):
        _build(fixture, result=bridge.evidence_digest)


def test_spliced_closure_parent_fails_fresh_rebuild() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    events = list(evidence.events)
    closure_index = next(
        index
        for index, event in enumerate(events)
        if event.event_id == evidence.closure_event_id
    )
    events[closure_index] = replace(
        events[closure_index],
        parent_ids=("source",),
    )
    forged = replace(evidence, events=tuple(events))

    with pytest.raises(ValueError):
        validate_p3og_semantic_formation_history_evidence(
            *fixture,
            "a" * 64,
            "b" * 64,
            forged,
        )


def test_hostile_nested_event_is_rejected_before_codec_callback() -> None:
    fixture = _fixture()
    evidence = _build(fixture)

    class HostileEvent(SemanticFormationHistoryEvent):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileEvent)
    forged = replace(evidence, events=(hostile,))

    with pytest.raises(ValueError):
        validate_p3og_semantic_formation_history_evidence(
            *fixture,
            "a" * 64,
            "b" * 64,
            forged,
        )
