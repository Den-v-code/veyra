"""Focused/hostile tests for residue-aware P3-OG semantic tick pressure."""

from __future__ import annotations

from dataclasses import fields, replace
from inspect import signature

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
from src.core.prime_power_observer_genesis_p3og_residue_aware_tick import (
    P3OGResidueAwareFormationCompatibilityEvidence,
    P3OGResidueAwareTickSource,
    P3OG_RESIDUE_AWARE_TICK_NONCLAIMS,
    ResidueAwareFormationCompatibilityStatus,
    ResiduePresenceClass,
    build_p3og_residue_aware_formation_compatibility_evidence,
    p3og_residue_aware_tick_source,
    residue_aware_semantic_tick,
    residue_aware_tick_rule,
    validate_p3og_residue_aware_formation_compatibility_evidence,
    validate_residue_aware_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_residue_aware_tick_codec import (
    residue_aware_tick_digest,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    P3OGSemanticConfiguration,
    SemanticOperationMode,
    p3og_semantic_configuration_contract,
    semantic_couple,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
)


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


def _residue_rules(*, absent_active_high: TransitionKind = TransitionKind.IDLE):
    return (
        residue_aware_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.HIGH,
            ResiduePresenceClass.ABSENT,
            absent_active_high,
        ),
        residue_aware_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.HIGH,
            ResiduePresenceClass.PRESENT,
            TransitionKind.ADVANCE,
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
            TransitionKind.ADVANCE,
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


def _fixture():
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="residue-aware-tick-v2",
        seed_rows=(("alpha", (0, 0, 1, 0)),),
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
        _residue_rules(),
    )
    formation_contract = p3og_native_formation_contract(source, autonomous)
    bridge_contract = p3og_semantic_formation_bridge_contract(
        source,
        autonomous,
        semantic_contract,
        formation_contract,
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
        residue_source,
        formation_contract,
        bridge_contract,
        binding,
        formation_source,
        formation,
        bridge,
    )


def _compatibility(fixture):
    return build_p3og_residue_aware_formation_compatibility_evidence(*fixture)


def test_residue_aware_v2_is_exactly_v1_over_formation_genealogy() -> None:
    fixture = _fixture()
    bridge = fixture[9]
    evidence = _compatibility(fixture)

    assert evidence.status is ResidueAwareFormationCompatibilityStatus.WITNESSED
    assert evidence.all_steps_residue_absent is True
    assert evidence.q_seed == bridge.q_seed
    assert evidence.final_configuration == bridge.final_configuration
    assert evidence.first_closure_step == bridge.first_closure_step
    assert len(evidence.ticks) == len(bridge.steps)
    assert all(
        receipt.residue_class is ResiduePresenceClass.ABSENT
        for receipt in evidence.ticks
    )
    assert tuple(receipt.selected_kind for receipt in evidence.ticks) == tuple(
        step.semantic_tick.selected_kind for step in bridge.steps
    )
    assert evidence.promotions == 0


def test_equal_external_response_can_drive_different_phase_via_retained_residue() -> None:
    fixture = _fixture()
    source, autonomous, semantic_contract, residue_source = fixture[:4]
    bridge = fixture[9]
    seed = source.seeds[0]
    q0 = bridge.final_configuration

    left, left_coupling = semantic_couple(
        source,
        autonomous,
        semantic_contract,
        seed,
        q0,
        0,
    )
    right, right_coupling = semantic_couple(
        source,
        autonomous,
        semantic_contract,
        seed,
        q0,
        1,
    )
    assert left_coupling.response == right_coupling.response == 0
    assert left.retained_residue == 0
    assert right.retained_residue == 1
    assert left.phase == right.phase == 0

    left_after, left_tick = residue_aware_semantic_tick(
        source,
        autonomous,
        semantic_contract,
        residue_source,
        seed,
        left,
    )
    right_after, right_tick = residue_aware_semantic_tick(
        source,
        autonomous,
        semantic_contract,
        residue_source,
        seed,
        right,
    )

    assert left_tick.residue_class is ResiduePresenceClass.PRESENT
    assert right_tick.residue_class is ResiduePresenceClass.PRESENT
    assert left_tick.selected_kind is right_tick.selected_kind is TransitionKind.ADVANCE
    assert left_tick.mode is right_tick.mode is SemanticOperationMode.NATIVE_QUOTIENT
    assert left_after.phase == 1
    assert right_after.phase == 2
    assert left_after.phase != right_after.phase
    assert left_after.retained_residue == 0
    assert right_after.retained_residue == 1
    assert left_after.boundary is right_after.boundary is BoundaryState.ALIVE
    assert left_after.maintenance_credit == right_after.maintenance_credit == 2


def test_absent_rows_must_match_exact_v1_kernel() -> None:
    fixture = _fixture()
    source, autonomous, semantic_contract = fixture[:3]

    with pytest.raises(ValueError, match="absent-kernel-drift"):
        p3og_residue_aware_tick_source(
            source,
            autonomous,
            semantic_contract,
            _residue_rules(absent_active_high=TransitionKind.ADVANCE),
        )


def test_source_is_pre_selection_and_tick_has_no_caller_transition_kind() -> None:
    fixture = _fixture()
    residue_source = fixture[3]
    names = {field.name for field in fields(P3OGResidueAwareTickSource)}

    assert {
        "selection",
        "selected_seed_digest",
        "status",
        "expected_status",
        "result",
        "later_result",
        "historical_token_id",
    }.isdisjoint(names)
    assert len(residue_source.rules) == 8
    assert "transition_kind" not in signature(residue_aware_semantic_tick).parameters


def test_fresh_validation_rebuilds_source_and_compatibility_evidence() -> None:
    fixture = _fixture()
    source, autonomous, semantic_contract, residue_source = fixture[:4]
    validated = validate_residue_aware_tick_source(
        source,
        autonomous,
        semantic_contract,
        residue_source,
    )[3]
    assert validated == residue_source
    assert validated is not residue_source

    evidence = _compatibility(fixture)
    replay = validate_p3og_residue_aware_formation_compatibility_evidence(
        *fixture,
        evidence,
    )
    assert replay == evidence
    assert replay is not evidence

    forged = replace(evidence, all_steps_residue_absent=False)
    with pytest.raises(ValueError):
        validate_p3og_residue_aware_formation_compatibility_evidence(
            *fixture,
            forged,
        )


def test_hostile_q_seed_is_rejected_before_codec_callback() -> None:
    fixture = _fixture()
    evidence = _compatibility(fixture)

    class HostileConfiguration(P3OGSemanticConfiguration):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileConfiguration)
    forged = replace(evidence, q_seed=hostile)

    with pytest.raises(ValueError, match="compatibility-shape"):
        validate_p3og_residue_aware_formation_compatibility_evidence(
            *fixture,
            forged,
        )


def test_digest_domain_and_nonclaims_stay_isolated() -> None:
    values = ("same", 0, 1)
    assert residue_aware_tick_digest(
        "residue-aware-tick-source",
        *values,
    ) != pressure_digest("residue-aware-tick-source", *values)
    assert {
        "v1-feedback-grammar-general-impossibility-theorem",
        "residue-aware-tick-is-upstream-native-api",
        "universal-def-og-004-theorem",
        "full-def-og-005-discharge",
        "full-def-og-006-through-def-og-009-discharge",
        "same-historical-token",
        "promotion",
    }.issubset(P3OG_RESIDUE_AWARE_TICK_NONCLAIMS)
    assert not hasattr(root_core, "p3og_residue_aware_tick_source")


def test_evidence_type_does_not_embed_outcome_authority() -> None:
    names = {
        field.name
        for field in fields(P3OGResidueAwareFormationCompatibilityEvidence)
    }
    assert {
        "expected_status",
        "criterion",
        "role",
        "observer",
        "historical_token",
        "actualization",
    }.isdisjoint(names)
