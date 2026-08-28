"""Focused/hostile tests for current matched ablation/removal dependence."""

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
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_intervention_plan import (
    p3og_semantic_intervention_plan,
)
from src.core.prime_power_observer_genesis_p3og_semantic_matched_ablation_removal import (
    P3OG_SEMANTIC_MATCHED_ABLATION_REMOVAL_NONCLAIMS,
    SemanticMatchedAblationRemovalStatus,
    build_p3og_semantic_matched_ablation_removal_evidence,
    validate_p3og_semantic_matched_ablation_removal_evidence,
)
from src.core.prime_power_observer_genesis_p3og_semantic_residue_phase_effect import (
    SemanticResiduePhaseEffectStatus,
    build_p3og_semantic_residue_phase_effect_evidence,
)
from src.core.prime_power_observer_genesis_p3og_semantic_retained_difference import (
    SemanticRetainedDifferenceStatus,
    build_p3og_semantic_retained_difference_evidence,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
)


def _fixture(
    *,
    disabled_low: TransitionKind = TransitionKind.IDLE,
    label: str = "semantic-matched-ablation-removal-current",
):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label,
        seed_rows=(("alpha", (0, 0, 1, 0)),),
        calibration_inputs=(0, 1),
        maintenance_credit=1,
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
            TransitionKind.ADVANCE,
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
    retained = build_p3og_semantic_retained_difference_evidence(
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
    phase = build_p3og_semantic_residue_phase_effect_evidence(
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
        retained,
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
        retained,
        phase,
    )


def _build(fixture):
    return build_p3og_semantic_matched_ablation_removal_evidence(*fixture)


def test_same_candidate_ablation_removes_boundary_and_retained_ability() -> None:
    fixture = _fixture()
    retained = fixture[10]
    phase = fixture[11]
    evidence = _build(fixture)

    assert retained.status is SemanticRetainedDifferenceStatus.WITNESSED
    assert phase.status is SemanticResiduePhaseEffectStatus.WITNESSED
    assert evidence.status is SemanticMatchedAblationRemovalStatus.WITNESSED
    assert evidence.component_id == "maintenance-control-v1"
    assert evidence.continuation_steps == 1
    assert (evidence.left_input, evidence.right_input) == (0, 1)
    assert evidence.matched_initials_except_component is True
    assert evidence.arithmetic_inputs_bound is True
    assert evidence.direct_reads_preserved is True
    assert evidence.unablated_boundaries_alive is True
    assert evidence.ablated_boundaries_removed is True
    assert evidence.ablated_residues_cleared is True
    assert evidence.claimed_ability_destroyed is True
    assert evidence.left_ablated_initial.maintenance_control is (
        MaintenanceControlState.DISABLED
    )
    assert evidence.right_ablated_initial.maintenance_control is (
        MaintenanceControlState.DISABLED
    )
    assert tuple(tick.selected_kind for tick in evidence.left_ablated_ticks) == (
        TransitionKind.IDLE,
    )
    assert tuple(tick.selected_kind for tick in evidence.right_ablated_ticks) == (
        TransitionKind.IDLE,
    )
    left_final = evidence.left_ablated_configurations[-1]
    right_final = evidence.right_ablated_configurations[-1]
    assert left_final.boundary is right_final.boundary is BoundaryState.REMOVED
    assert left_final.retained_residue is right_final.retained_residue is None
    assert left_final.phase == right_final.phase == 0
    assert evidence.promotions == 0


def test_valid_ablation_without_removal_dependence_is_refuted() -> None:
    fixture = _fixture(
        disabled_low=TransitionKind.MAINTAIN,
        label="semantic-matched-ablation-removal-refuted",
    )
    phase = fixture[11]
    evidence = _build(fixture)

    assert phase.status is SemanticResiduePhaseEffectStatus.WITNESSED
    assert evidence.matched_initials_except_component is True
    assert evidence.direct_reads_preserved is True
    assert evidence.ablated_boundaries_removed is False
    assert evidence.ablated_residues_cleared is False
    assert evidence.claimed_ability_destroyed is False
    assert evidence.status is SemanticMatchedAblationRemovalStatus.REFUTED


def test_fresh_validation_rebuilds_and_rejects_tampering() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    replay = validate_p3og_semantic_matched_ablation_removal_evidence(
        *fixture,
        evidence,
    )
    assert replay == evidence
    assert replay is not evidence

    forged = replace(evidence, ablated_boundaries_removed=False)
    with pytest.raises(ValueError):
        validate_p3og_semantic_matched_ablation_removal_evidence(
            *fixture,
            forged,
        )


def test_foreign_phase_effect_cannot_splice_into_removal_witness() -> None:
    fixture = _fixture()
    foreign = _fixture(label="semantic-matched-ablation-removal-foreign")
    evidence = _build(fixture)

    with pytest.raises(ValueError):
        validate_p3og_semantic_matched_ablation_removal_evidence(
            *fixture[:-1],
            foreign[-1],
            evidence,
        )


def test_claim_boundary_stays_bounded_below_history_and_role() -> None:
    assert {
        "standalone-witness-is-not-complete-event-history",
        "ablation-cut-not-yet-bound-into-noncircular-history-dag",
        "full-def-og-006-discharge",
        "full-def-og-007-discharge",
        "same-historical-token-causal-efficacy",
        "full-def-og-008-discharge",
        "full-def-og-009-discharge",
        "universal-ablation-separator-theorem",
        "endogenous-observer-role",
        "promotion",
    }.issubset(P3OG_SEMANTIC_MATCHED_ABLATION_REMOVAL_NONCLAIMS)
