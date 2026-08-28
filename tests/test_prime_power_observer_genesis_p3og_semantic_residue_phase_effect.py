"""Focused/hostile tests for current retained-residue ADVANCE phase effect."""

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
from src.core.prime_power_observer_genesis_p3og_semantic_residue_phase_effect import (
    P3OG_SEMANTIC_RESIDUE_PHASE_EFFECT_NONCLAIMS,
    SemanticResiduePhaseEffectStatus,
    build_p3og_semantic_residue_phase_effect_evidence,
    validate_p3og_semantic_residue_phase_effect_evidence,
)
from src.core.prime_power_observer_genesis_p3og_semantic_retained_difference import (
    SemanticRetainedDifferenceStatus,
    build_p3og_semantic_retained_difference_evidence,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
)


def _fixture(
    *,
    credit: int = 1,
    active_high: TransitionKind = TransitionKind.IDLE,
    active_low: TransitionKind = TransitionKind.ADVANCE,
    label: str = "semantic-residue-phase-effect-current",
):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label,
        seed_rows=(("alpha", (0, 0, 1, 0)),),
        calibration_inputs=(0, 1),
        maintenance_credit=credit,
        suffix=(TransitionKind.IDLE,),
    )
    rules = (
        autonomous_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.HIGH,
            active_high,
        ),
        autonomous_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.LOW,
            active_low,
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
    )


def _build(fixture):
    return build_p3og_semantic_residue_phase_effect_evidence(*fixture)


def test_equal_response_f0_f1_change_first_later_advance_phase() -> None:
    fixture = _fixture()
    bridge = fixture[9]
    retained = fixture[10]
    evidence = _build(fixture)

    assert bridge.first_closure_step == 3
    assert retained.status is SemanticRetainedDifferenceStatus.WITNESSED
    assert retained.continuation_steps == 1
    assert retained.left_coupling.response == retained.right_coupling.response == 0
    assert evidence.status is SemanticResiduePhaseEffectStatus.WITNESSED
    assert evidence.equal_coupling_response is True
    assert evidence.residues_distinct is True
    assert (evidence.left_residue, evidence.right_residue) == (0, 1)
    assert evidence.before_matched_except_residue is True
    assert evidence.left_before_phase == evidence.right_before_phase == 0
    assert evidence.same_advance_kind is True
    assert evidence.left_selected_kind is TransitionKind.ADVANCE
    assert evidence.right_selected_kind is TransitionKind.ADVANCE
    assert (evidence.left_after_phase, evidence.right_after_phase) == (1, 2)
    assert evidence.phase_diverged is True
    assert evidence.transition_law_bound is True
    assert evidence.promotions == 0


def test_same_retained_difference_without_advance_refutes_phase_effect() -> None:
    fixture = _fixture(
        credit=2,
        active_high=TransitionKind.IDLE,
        active_low=TransitionKind.MAINTAIN,
        label="semantic-residue-phase-effect-idle",
    )
    retained = fixture[10]
    evidence = _build(fixture)

    assert retained.status is SemanticRetainedDifferenceStatus.WITNESSED
    assert evidence.same_advance_kind is False
    assert evidence.phase_diverged is False
    assert evidence.status is SemanticResiduePhaseEffectStatus.REFUTED


def test_fresh_validation_rebuilds_and_rejects_tampered_effect() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    replay = validate_p3og_semantic_residue_phase_effect_evidence(
        *fixture,
        evidence,
    )
    assert replay == evidence
    assert replay is not evidence

    forged = replace(evidence, phase_diverged=False)
    with pytest.raises(ValueError):
        validate_p3og_semantic_residue_phase_effect_evidence(
            *fixture,
            forged,
        )


def test_foreign_retained_witness_cannot_splice_into_effect() -> None:
    fixture = _fixture()
    foreign = _fixture(label="semantic-residue-phase-effect-foreign")
    evidence = _build(fixture)

    with pytest.raises(ValueError):
        validate_p3og_semantic_residue_phase_effect_evidence(
            *fixture[:-1],
            foreign[-1],
            evidence,
        )


def test_claim_boundary_stays_functional_not_causal() -> None:
    assert {
        "different-later-transition-kind",
        "different-later-readiness-state",
        "different-later-typed-response",
        "same-historical-token-causal-efficacy",
        "full-def-og-008-discharge",
        "full-def-og-004-discharge",
        "full-def-og-009-discharge",
        "endogenous-observer-role",
        "promotion",
    }.issubset(P3OG_SEMANTIC_RESIDUE_PHASE_EFFECT_NONCLAIMS)
