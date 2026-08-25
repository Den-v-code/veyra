"""Focused/hostile tests for the exact P3-OG semantic-formation bridge."""

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
    NativeFormationStatus,
    p3og_native_formation_binding,
    p3og_native_formation_contract,
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    SemanticFormationBridgeStatus,
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
    validate_p3og_semantic_formation_bridge_evidence,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    SemanticFormationBridgeStep,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _fixture(*, low: TransitionKind = TransitionKind.MAINTAIN):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=f"semantic-formation-bridge-{low.value}",
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
            low,
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
    binding = p3og_native_formation_binding(
        source,
        autonomous,
        formation_contract,
    )
    formation_source = p3og_native_formation_source(source, autonomous)
    formation = run_p3og_native_formation(
        source,
        autonomous,
        formation_source,
    )
    return (
        source,
        autonomous,
        semantic_contract,
        formation_contract,
        bridge_contract,
        binding,
        formation_source,
        formation,
    )


def _build(fixture):
    return build_p3og_semantic_formation_bridge_evidence(*fixture)


def test_witnessed_formation_is_exact_first_return_in_q_sem() -> None:
    fixture = _fixture()
    formation = fixture[-1]
    evidence = _build(fixture)

    assert formation.status is NativeFormationStatus.WITNESSED
    assert evidence.status is SemanticFormationBridgeStatus.WITNESSED
    assert evidence.departure_step == 1
    assert evidence.first_closure_step == formation.first_closure_step == 2
    assert evidence.final_configuration == evidence.q_seed
    assert tuple(step.semantic_tick.selected_kind for step in evidence.steps) == (
        TransitionKind.IDLE,
        TransitionKind.MAINTAIN,
    )
    assert tuple(step.closed_after for step in evidence.steps) == (False, True)
    assert tuple(step.departed_after for step in evidence.steps) == (True, True)
    assert evidence.promotions == 0
    assert "typed-history-dag-or-full-def-og-003" in evidence.nonclaims


def test_bridge_contract_is_pre_selection_only() -> None:
    fixture = _fixture()
    bridge_contract = fixture[4]

    names = {field.name for field in fields(bridge_contract)}
    assert "selection" not in names
    assert "selected_seed_digest" not in names
    assert bridge_contract.semantic_configuration_contract_digest == fixture[2].contract_digest
    assert bridge_contract.native_formation_contract_digest == fixture[3].contract_digest


def test_refuted_native_formation_cannot_mint_positive_bridge() -> None:
    fixture = _fixture(low=TransitionKind.IDLE)
    assert fixture[-1].status is NativeFormationStatus.REFUTED
    with pytest.raises(ValueError, match="requires-witnessed-formation"):
        _build(fixture)


def test_tampered_bridge_step_fails_fresh_replay() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    first = replace(
        evidence.steps[0],
        after_configuration_digest="0" * 64,
    )
    forged = replace(evidence, steps=(first, *evidence.steps[1:]))

    with pytest.raises(ValueError):
        validate_p3og_semantic_formation_bridge_evidence(
            *fixture,
            forged,
        )


def test_hostile_nested_step_is_rejected_before_codec_callback() -> None:
    fixture = _fixture()
    evidence = _build(fixture)

    class HostileStep(SemanticFormationBridgeStep):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileStep)
    forged = replace(evidence, steps=(hostile,))

    with pytest.raises(ValueError):
        validate_p3og_semantic_formation_bridge_evidence(
            *fixture,
            forged,
        )
