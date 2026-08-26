"""Focused/hostile tests for matched retained-residue causal-effect pressure."""

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
    p3og_native_formation_binding,
    p3og_native_formation_contract,
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_residue_aware_tick import (
    ResiduePresenceClass,
    build_p3og_residue_aware_formation_compatibility_evidence,
    p3og_residue_aware_tick_source,
    residue_aware_tick_rule,
)
from src.core.prime_power_observer_genesis_p3og_residue_causal_effect import (
    P3OGResidueCausalEffectEvidence,
    P3OGResidueCausalEffectPlan,
    P3OG_RESIDUE_CAUSAL_EFFECT_NONCLAIMS,
    ResidueCausalEffectStatus,
    build_p3og_residue_causal_effect_evidence,
    p3og_residue_causal_effect_plan,
    validate_p3og_residue_causal_effect_evidence,
)
from src.core.prime_power_observer_genesis_p3og_residue_causal_effect_codec import (
    residue_causal_effect_digest,
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
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _base_rules():
    return (
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


def _residue_rules(*, present_active: TransitionKind):
    return (
        residue_aware_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.HIGH,
            ResiduePresenceClass.ABSENT,
            TransitionKind.IDLE,
        ),
        residue_aware_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.HIGH,
            ResiduePresenceClass.PRESENT,
            present_active,
        ),
        residue_aware_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.LOW,
            ResiduePresenceClass.ABSENT,
            TransitionKind.MAINTAIN,
        ),
        residue_aware_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.LOW,
            ResiduePresenceClass.PRESENT,
            present_active,
        ),
        residue_aware_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.HIGH,
            ResiduePresenceClass.ABSENT,
            TransitionKind.IDLE,
        ),
        residue_aware_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.HIGH,
            ResiduePresenceClass.PRESENT,
            TransitionKind.IDLE,
        ),
        residue_aware_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.LOW,
            ResiduePresenceClass.ABSENT,
            TransitionKind.IDLE,
        ),
        residue_aware_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.LOW,
            ResiduePresenceClass.PRESENT,
            TransitionKind.IDLE,
        ),
    )


def _fixture(
    *,
    cycle=(0, 0, 1, 0),
    present_active: TransitionKind = TransitionKind.ADVANCE,
):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=f"residue-causal-{present_active.value}-{cycle}",
        seed_rows=(("alpha", cycle),),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=(TransitionKind.IDLE,),
    )
    autonomous = p3og_autonomous_tick_source(source, _base_rules())
    semantic_contract = p3og_semantic_configuration_contract(source, autonomous)
    residue_source = p3og_residue_aware_tick_source(
        source,
        autonomous,
        semantic_contract,
        _residue_rules(present_active=present_active),
    )
    formation_contract = p3og_native_formation_contract(source, autonomous)
    bridge_contract = p3og_semantic_formation_bridge_contract(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
    )
    arithmetic = p3og_arithmetic_input_source(source)
    plan = p3og_residue_causal_effect_plan(
        source,
        autonomous,
        semantic_contract,
        residue_source,
        formation_contract,
        bridge_contract,
        arithmetic,
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
    compatibility = build_p3og_residue_aware_formation_compatibility_evidence(
        source,
        autonomous,
        semantic_contract,
        residue_source,
        formation_contract,
        bridge_contract,
        binding,
        formation_source,
        formation,
        bridge,
    )
    return (
        source,
        autonomous,
        semantic_contract,
        residue_source,
        formation_contract,
        bridge_contract,
        arithmetic,
        plan,
        binding,
        formation_source,
        formation,
        bridge,
        compatibility,
    )


def _build(fixture):
    return build_p3og_residue_causal_effect_evidence(*fixture)


def test_equal_response_matched_pair_exposes_residue_to_phase_sensitivity() -> None:
    evidence = _build(_fixture())

    assert evidence.status is ResidueCausalEffectStatus.WITNESSED
    assert evidence.before_matched_except_residue is True
    assert evidence.equal_coupling_response is True
    assert evidence.left_coupling.response == evidence.right_coupling.response == 0
    assert evidence.residues_distinct is True
    assert evidence.left_coupled.retained_residue == 0
    assert evidence.right_coupled.retained_residue == 1
    assert evidence.left_coupled.phase == evidence.right_coupled.phase == 0
    assert evidence.same_selected_kind is True
    assert evidence.same_tick_mode is True
    assert evidence.selected_advance is True
    assert evidence.left_tick.selected_kind is evidence.right_tick.selected_kind is TransitionKind.ADVANCE
    assert evidence.left_tick.mode is evidence.right_tick.mode is SemanticOperationMode.NATIVE_QUOTIENT
    assert evidence.phase_diverged is True
    assert evidence.left_after.phase == 1
    assert evidence.right_after.phase == 2
    assert evidence.after_matched_except_phase_and_residue is True
    assert evidence.left_after.boundary == evidence.right_after.boundary
    assert evidence.left_after.maintenance_control == evidence.right_after.maintenance_control
    assert evidence.left_after.maintenance_credit == evidence.right_after.maintenance_credit
    assert evidence.promotions == 0


def test_present_maintain_refutes_downstream_effect_without_breaking_match() -> None:
    evidence = _build(_fixture(present_active=TransitionKind.MAINTAIN))

    assert evidence.before_matched_except_residue is True
    assert evidence.equal_coupling_response is True
    assert evidence.residues_distinct is True
    assert evidence.same_selected_kind is True
    assert evidence.left_tick.selected_kind is evidence.right_tick.selected_kind is TransitionKind.MAINTAIN
    assert evidence.selected_advance is False
    assert evidence.phase_diverged is False
    assert evidence.left_after.phase == evidence.right_after.phase == 0
    assert evidence.status is ResidueCausalEffectStatus.REFUTED


def test_different_external_responses_refute_equal_response_criterion() -> None:
    evidence = _build(_fixture(cycle=(0, 1, 2, 0)))

    assert evidence.before_matched_except_residue is True
    assert evidence.residues_distinct is True
    assert evidence.left_coupling.response == 0
    assert evidence.right_coupling.response == 1
    assert evidence.equal_coupling_response is False
    assert evidence.selected_advance is True
    assert evidence.phase_diverged is True
    assert evidence.status is ResidueCausalEffectStatus.REFUTED


def test_plan_is_pre_selection_and_commits_effect_coordinate() -> None:
    fixture = _fixture()
    plan = fixture[7]
    names = {field.name for field in fields(P3OGResidueCausalEffectPlan)}

    assert {
        "selection",
        "selected_seed_digest",
        "status",
        "expected_status",
        "result",
        "historical_token_id",
        "left_response",
        "right_response",
    }.isdisjoint(names)
    assert plan.effect_coordinate == "phase"
    assert plan.residue_aware_source_digest == fixture[3].source_digest


def test_fresh_validation_rebuilds_and_rejects_tampering() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    replay = validate_p3og_residue_causal_effect_evidence(*fixture, evidence)

    assert replay == evidence
    assert replay is not evidence

    forged = replace(evidence, phase_diverged=False)
    with pytest.raises(ValueError):
        validate_p3og_residue_causal_effect_evidence(*fixture, forged)


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
        validate_p3og_residue_causal_effect_evidence(*fixture, forged)


def test_digest_domain_and_claim_boundary_remain_narrow() -> None:
    values = ("same", 0, 1)
    assert residue_causal_effect_digest(
        "residue-causal-effect-plan",
        *values,
    ) != pressure_digest("residue-causal-effect-plan", *values)
    assert {
        "universal-retained-residue-causal-theorem",
        "f0-f1-input-history-is-a-typed-ablation",
        "do-retained-residue-intervention",
        "same-historical-token-causal-efficacy",
        "full-def-og-008-discharge",
        "endogenous-observer-role",
        "promotion",
    }.issubset(P3OG_RESIDUE_CAUSAL_EFFECT_NONCLAIMS)
    assert not hasattr(root_core, "p3og_residue_causal_effect_plan")


def test_evidence_type_does_not_embed_role_or_historical_authority() -> None:
    names = {field.name for field in fields(P3OGResidueCausalEffectEvidence)}
    assert {
        "expected_status",
        "role",
        "observer",
        "historical_token",
        "actualization",
        "do_intervention",
    }.isdisjoint(names)
