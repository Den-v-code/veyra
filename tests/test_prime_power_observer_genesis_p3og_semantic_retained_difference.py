"""Focused/hostile tests for current P3-OG retained-difference evidence."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_arithmetic_input import (
    p3og_arithmetic_input_source,
)
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_one_shot_selection import (
    consume_p3og_selection_capability,
    p3og_initial_selection_capability,
    p3og_one_shot_selection_source,
)
from src.core.prime_power_observer_genesis_p3og_semantic_ablation import (
    p3og_semantic_ablation_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    P3OGSemanticConfiguration,
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_intervention_plan import (
    p3og_semantic_intervention_plan,
)
from src.core.prime_power_observer_genesis_p3og_semantic_retained_difference import (
    P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS,
    SemanticRetainedDifferenceStatus,
    build_p3og_semantic_retained_difference_evidence,
    validate_p3og_semantic_retained_difference_evidence,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
)


def _fixture(
    *,
    cycle=(0, 1, 0),
    label="semantic-retained-difference-current",
):
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
    semantic = p3og_semantic_configuration_contract(source, autonomous)
    bridge_contract = p3og_semantic_formation_bridge_contract(
        source,
        autonomous,
        semantic,
    )
    ablation = p3og_semantic_ablation_contract(
        source,
        autonomous,
        semantic,
    )
    intervention = p3og_semantic_intervention_plan(
        source,
        autonomous,
        semantic,
        bridge_contract,
        ablation,
    )
    arithmetic = p3og_arithmetic_input_source(source)
    selection_source = p3og_one_shot_selection_source(source, "f" * 64)
    available = p3og_initial_selection_capability(source, selection_source)
    _, consumed, selection = consume_p3og_selection_capability(
        source,
        selection_source,
        available,
    )
    formation_source = p3og_native_formation_source(
        source,
        autonomous,
        selection_source,
        available,
        consumed,
        selection,
    )
    formation = run_p3og_native_formation(
        source,
        autonomous,
        formation_source,
    )
    bridge = build_p3og_semantic_formation_bridge_evidence(
        source,
        autonomous,
        semantic,
        bridge_contract,
        formation_source,
        formation,
    )
    return (
        source,
        autonomous,
        semantic,
        bridge_contract,
        ablation,
        intervention,
        arithmetic,
        formation_source,
        formation,
        bridge,
    )


def _build(fixture):
    return build_p3og_semantic_retained_difference_evidence(*fixture)


def test_p3n2_f0_f1_remain_distinct_over_declared_continuation() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    intervention = fixture[5]
    arithmetic = fixture[6]
    continuation = intervention.continuation_catalog[0]

    assert evidence.status is SemanticRetainedDifferenceStatus.WITNESSED
    assert evidence.arithmetic_input_source_digest == arithmetic.source_digest
    assert evidence.intervention_plan_digest == intervention.plan_digest
    assert evidence.continuation_entry_id == continuation.entry_id
    assert evidence.continuation_spec_digest == continuation.spec_digest
    assert evidence.continuation_steps == continuation.steps == 2
    assert evidence.q0 == fixture[9].final_configuration
    assert evidence.left_coupled.retained_residue == arithmetic.left_residue == 0
    assert evidence.right_coupled.retained_residue == arithmetic.right_residue == 1
    assert evidence.initial_residues_distinct is True
    assert evidence.every_step_residues_distinct is True
    assert evidence.every_step_boundary_alive is True
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


def test_retained_difference_is_internal_even_when_responses_match() -> None:
    fixture = _fixture(
        cycle=(0, 0, 1, 0),
        label="semantic-retained-difference-equal-response-current",
    )
    evidence = _build(fixture)

    assert evidence.left_coupling.response == evidence.right_coupling.response == 0
    assert evidence.left_coupled.retained_residue == 0
    assert evidence.right_coupled.retained_residue == 1
    assert evidence.status is SemanticRetainedDifferenceStatus.WITNESSED
    assert evidence.every_step_residues_distinct is True


def test_fresh_validation_rebuilds_complete_witness() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    replay = validate_p3og_semantic_retained_difference_evidence(
        *fixture,
        evidence,
    )
    assert replay == evidence
    assert replay is not evidence

    forged = replace(evidence, initial_residues_distinct=False)
    with pytest.raises(ValueError):
        validate_p3og_semantic_retained_difference_evidence(
            *fixture,
            forged,
        )


def test_foreign_arithmetic_source_cannot_splice_into_witness() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    foreign = _fixture(label="semantic-retained-difference-foreign")

    with pytest.raises(ValueError):
        validate_p3og_semantic_retained_difference_evidence(
            fixture[0],
            fixture[1],
            fixture[2],
            fixture[3],
            fixture[4],
            fixture[5],
            foreign[6],
            fixture[7],
            fixture[8],
            fixture[9],
            evidence,
        )


def test_hostile_nested_q0_is_rejected_before_codec_callback() -> None:
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
        validate_p3og_semantic_retained_difference_evidence(
            *fixture,
            forged,
        )


def test_claim_boundary_stays_narrow() -> None:
    assert {
        "standalone-witness-does-not-prove-intervention-plan-strict-past",
        "arithmetic-source-preselection-history-binding",
        "retained-residue-causes-later-transition-or-response",
        "universal-def-og-004-theorem",
        "full-def-og-004-discharge",
        "full-def-og-009-discharge",
        "same-historical-token",
        "endogenous-observer-role",
        "promotion",
    }.issubset(P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS)
