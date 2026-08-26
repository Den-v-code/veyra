"""Focused/hostile tests for P3-OG semantic retained-difference pressure."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

import src.core as root_core
from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_arithmetic_input import (
    p3og_arithmetic_input_source,
)
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_codec import digest as pressure_digest
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    NativeFormationStatus,
    p3og_native_formation_binding,
    p3og_native_formation_contract,
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    P3OGSemanticConfiguration,
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    SemanticFormationBridgeStatus,
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_retained_difference import (
    P3OGSemanticRetainedDifferencePlan,
    P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS,
    SemanticRetainedDifferenceStatus,
    build_p3og_semantic_retained_difference_evidence,
    p3og_semantic_retained_difference_plan,
    validate_p3og_semantic_retained_difference_evidence,
    validate_semantic_retained_difference_plan,
)
from src.core.prime_power_observer_genesis_p3og_semantic_retained_difference_codec import (
    semantic_retained_difference_digest,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _fixture(*, cycle=(0, 1, 0), label="semantic-retained-difference"):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label,
        seed_rows=(("alpha", cycle),),
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
    arithmetic = p3og_arithmetic_input_source(source)
    plan = p3og_semantic_retained_difference_plan(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
        bridge_contract,
        arithmetic,
    )
    binding = p3og_native_formation_binding(
        source,
        autonomous,
        formation_contract,
    )
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
        arithmetic,
        plan,
        binding,
        formation_source,
        formation,
        bridge,
    )


def _build(fixture):
    return build_p3og_semantic_retained_difference_evidence(*fixture)


def test_f0_f1_residues_remain_distinct_over_every_declared_prefix() -> None:
    fixture = _fixture()
    source = fixture[0]
    plan = fixture[6]
    formation = fixture[9]
    bridge = fixture[10]
    evidence = _build(fixture)

    assert formation.status is NativeFormationStatus.WITNESSED
    assert bridge.status is SemanticFormationBridgeStatus.WITNESSED
    assert plan.continuation_lengths == tuple(range(1, source.maintenance_credit + 1))
    assert plan.max_steps == source.maintenance_credit == 2
    assert evidence.status is SemanticRetainedDifferenceStatus.WITNESSED
    assert evidence.q0 == bridge.q_seed == bridge.final_configuration
    assert evidence.left_coupled == evidence.left_configurations[0]
    assert evidence.right_coupled == evidence.right_configurations[0]
    assert evidence.left_coupled.retained_residue == 0
    assert evidence.right_coupled.retained_residue == 1
    assert evidence.initial_residues_distinct is True
    assert evidence.every_prefix_residues_distinct is True
    assert evidence.every_prefix_boundary_alive is True
    assert len(evidence.left_ticks) == len(evidence.right_ticks) == 2
    assert all(
        left.retained_residue != right.retained_residue
        for left, right in zip(
            evidence.left_configurations,
            evidence.right_configurations,
            strict=True,
        )
    )
    assert evidence.promotions == 0


def test_retained_difference_does_not_require_different_responses() -> None:
    fixture = _fixture(
        cycle=(0, 0, 1, 0),
        label="semantic-retained-difference-equal-response",
    )
    evidence = _build(fixture)

    assert evidence.left_coupling.response == evidence.right_coupling.response == 0
    assert evidence.left_coupled.retained_residue == 0
    assert evidence.right_coupled.retained_residue == 1
    assert evidence.status is SemanticRetainedDifferenceStatus.WITNESSED
    assert evidence.every_prefix_residues_distinct is True
    assert "different-response-required-for-retained-difference" in evidence.nonclaims


def test_plan_is_pre_selection_and_commits_complete_prefix_catalog() -> None:
    fixture = _fixture()
    source = fixture[0]
    plan = fixture[6]
    names = {field.name for field in fields(P3OGSemanticRetainedDifferencePlan)}

    assert {
        "selection",
        "selected_seed_digest",
        "candidate_id",
        "status",
        "expected_status",
        "criterion",
        "later_result",
        "historical_token_id",
    }.isdisjoint(names)
    assert plan.continuation_lengths == (1, 2)
    assert plan.max_steps == source.maintenance_credit


def test_fresh_validation_rebuilds_and_rejects_tampered_evidence() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    replay = validate_p3og_semantic_retained_difference_evidence(*fixture, evidence)

    assert replay == evidence
    assert replay is not evidence

    forged = replace(evidence, initial_residues_distinct=False)
    with pytest.raises(ValueError):
        validate_p3og_semantic_retained_difference_evidence(*fixture, forged)


def test_hostile_q0_is_rejected_before_codec_callback() -> None:
    fixture = _fixture()
    evidence = _build(fixture)

    class HostileConfiguration(P3OGSemanticConfiguration):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileConfiguration)
    forged = replace(evidence, q0=hostile)

    with pytest.raises(ValueError, match="evidence-shape"):
        validate_p3og_semantic_retained_difference_evidence(*fixture, forged)


def test_hostile_plan_container_is_rejected_before_iteration_callback() -> None:
    fixture = _fixture()
    plan = fixture[6]

    class HostileTuple(tuple):
        def __iter__(self):
            raise AssertionError("hostile iterator reached")

    forged = replace(plan, continuation_lengths=HostileTuple((1, 2)))
    with pytest.raises(ValueError, match="plan-shape"):
        validate_semantic_retained_difference_plan(*fixture[:6], forged)


def test_digest_domain_and_claim_boundary_remain_isolated() -> None:
    values = ("same", 0, 1)
    assert semantic_retained_difference_digest(
        "semantic-retained-difference-plan",
        *values,
    ) != pressure_digest("semantic-retained-difference-plan", *values)
    assert {
        "different-response-required-for-retained-difference",
        "retained-residue-causes-later-transition-or-response",
        "universal-def-og-004-theorem",
        "full-def-og-005-discharge",
        "same-historical-token",
        "endogenous-observer-role",
        "promotion",
    }.issubset(P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS)
    assert not hasattr(root_core, "p3og_semantic_retained_difference_plan")
