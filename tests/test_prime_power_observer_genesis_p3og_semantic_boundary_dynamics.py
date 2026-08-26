"""Focused/hostile tests for P3-OG semantic boundary dynamics."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

import src.core as root_core
from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_codec import digest as pressure_digest
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    p3og_native_formation_binding,
    p3og_native_formation_contract,
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_semantic_ablation import (
    p3og_semantic_ablation_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_boundary_dynamics import (
    BoundaryMaintenanceStatus,
    InternalRemovalStatus,
    P3OGSemanticBoundaryDynamicsPlan,
    P3OG_SEMANTIC_BOUNDARY_DYNAMICS_NONCLAIMS,
    build_p3og_semantic_boundary_dynamics_evidence,
    p3og_semantic_boundary_dynamics_plan,
    validate_p3og_semantic_boundary_dynamics_evidence,
    validate_semantic_boundary_dynamics_plan,
)
from src.core.prime_power_observer_genesis_p3og_semantic_boundary_dynamics_codec import (
    semantic_boundary_dynamics_digest,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    P3OGSemanticConfiguration,
    SemanticOperationMode,
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
)


def _fixture(*, disabled_low: TransitionKind = TransitionKind.IDLE):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=f"semantic-boundary-dynamics-{disabled_low.value}",
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
    ablation_contract = p3og_semantic_ablation_contract(
        source,
        autonomous,
        semantic_contract,
    )
    plan = p3og_semantic_boundary_dynamics_plan(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
        bridge_contract,
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
        ablation_contract,
        plan,
        binding,
        formation_source,
        formation,
        bridge,
    )


def _build(fixture):
    return build_p3og_semantic_boundary_dynamics_evidence(*fixture)


def test_active_component_maintains_declared_catalog_and_disabled_component_removes() -> None:
    fixture = _fixture()
    evidence = _build(fixture)

    assert evidence.maintenance_status is BoundaryMaintenanceStatus.WITNESSED
    assert evidence.every_catalog_boundary_alive is True
    assert evidence.maintenance_component_exercised is True
    assert tuple(tick.selected_kind for tick in evidence.maintenance_ticks) == (
        TransitionKind.IDLE,
        TransitionKind.MAINTAIN,
    )
    assert all(
        state.boundary is BoundaryState.ALIVE
        for state in evidence.maintenance_configurations
    )

    assert evidence.ablated_q0.maintenance_control is MaintenanceControlState.DISABLED
    assert evidence.removal_status is InternalRemovalStatus.WITNESSED
    assert evidence.internal_removal_witnessed is True
    assert evidence.removal_step == 2
    assert evidence.removal_before is not None
    assert evidence.removal_after is not None
    assert evidence.removal_tick is not None
    assert evidence.removal_before.boundary is BoundaryState.ALIVE
    assert evidence.removal_before.maintenance_control is MaintenanceControlState.DISABLED
    assert evidence.removal_before.maintenance_credit == 1
    assert evidence.removal_after.boundary is BoundaryState.REMOVED
    assert evidence.removal_tick.mode is SemanticOperationMode.NATIVE_QUOTIENT
    assert evidence.removal_transition_kind is TransitionKind.IDLE
    assert evidence.removal_signal_control is MaintenanceControlState.DISABLED
    assert evidence.removal_signal_credit == 1
    assert evidence.promotions == 0


def test_negative_disabled_low_rule_refutes_removal_without_breaking_maintenance() -> None:
    fixture = _fixture(disabled_low=TransitionKind.MAINTAIN)
    evidence = _build(fixture)

    assert evidence.maintenance_status is BoundaryMaintenanceStatus.WITNESSED
    assert evidence.every_catalog_boundary_alive is True
    assert evidence.maintenance_component_exercised is True
    assert evidence.removal_status is InternalRemovalStatus.REFUTED
    assert evidence.internal_removal_witnessed is False
    assert evidence.removal_step is None
    assert evidence.removal_before is None
    assert evidence.removal_after is None
    assert evidence.removal_tick is None
    assert evidence.removal_transition_kind is None
    assert all(
        state.boundary is BoundaryState.ALIVE
        for state in evidence.removal_configurations
    )


def test_plan_is_pre_selection_and_commits_catalog_and_component() -> None:
    fixture = _fixture()
    source = fixture[0]
    ablation_contract = fixture[5]
    plan = fixture[6]
    names = {field.name for field in fields(P3OGSemanticBoundaryDynamicsPlan)}

    assert {
        "selection",
        "selected_seed_digest",
        "status",
        "expected_status",
        "later_result",
        "historical_token_id",
    }.isdisjoint(names)
    assert plan.component_id == ablation_contract.component_id
    assert plan.continuation_lengths == (1, 2)
    assert plan.max_steps == source.maintenance_credit


def test_fresh_validation_rebuilds_and_rejects_tampering() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    replay = validate_p3og_semantic_boundary_dynamics_evidence(*fixture, evidence)
    assert replay == evidence
    assert replay is not evidence

    forged = replace(evidence, internal_removal_witnessed=False)
    with pytest.raises(ValueError):
        validate_p3og_semantic_boundary_dynamics_evidence(*fixture, forged)


def test_hostile_q0_is_rejected_before_codec_callback() -> None:
    fixture = _fixture()
    evidence = _build(fixture)

    class HostileConfiguration(P3OGSemanticConfiguration):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    forged = replace(evidence, q0=object.__new__(HostileConfiguration))
    with pytest.raises(ValueError, match="evidence-shape"):
        validate_p3og_semantic_boundary_dynamics_evidence(*fixture, forged)


def test_hostile_plan_container_is_rejected_before_iteration() -> None:
    fixture = _fixture()
    plan = fixture[6]

    class HostileTuple(tuple):
        def __iter__(self):
            raise AssertionError("hostile iterator reached")

    forged = replace(plan, continuation_lengths=HostileTuple((1, 2)))
    with pytest.raises(ValueError, match="plan-shape"):
        validate_semantic_boundary_dynamics_plan(*fixture[:6], forged)


def test_digest_domain_and_nonclaims_stay_narrow() -> None:
    values = ("same", 1, 2)
    assert semantic_boundary_dynamics_digest(
        "semantic-boundary-dynamics-plan",
        *values,
    ) != pressure_digest("semantic-boundary-dynamics-plan", *values)
    assert {
        "universal-def-og-005-theorem",
        "all-possible-continuation-catalogs",
        "removal-without-prior-typed-ablation",
        "full-def-og-006-discharge",
        "same-historical-token",
        "endogenous-observer-role",
        "promotion",
    }.issubset(P3OG_SEMANTIC_BOUNDARY_DYNAMICS_NONCLAIMS)
    assert not hasattr(root_core, "p3og_semantic_boundary_dynamics_plan")
