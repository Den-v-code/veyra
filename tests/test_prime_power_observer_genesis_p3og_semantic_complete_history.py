"""Focused/hostile tests for the coherent semantic candidate in history v6."""

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
from src.core.prime_power_observer_genesis_p3og_formation_history import (
    build_p3og_formation_history_evidence,
    p3og_formation_history_plan,
)
from src.core.prime_power_observer_genesis_p3og_formation_history_types import (
    FormationHistoryPostClosureBindings,
    FormationHistoryStatus,
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
from src.core.prime_power_observer_genesis_p3og_semantic_complete_history import (
    build_p3og_semantic_complete_history_evidence,
    validate_p3og_semantic_complete_history_evidence,
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
    build_p3og_semantic_matched_ablation_removal_evidence,
)
from src.core.prime_power_observer_genesis_p3og_semantic_preselection_history import (
    p3og_semantic_preselection_history_plan,
)
from src.core.prime_power_observer_genesis_p3og_semantic_residue_phase_effect import (
    build_p3og_semantic_residue_phase_effect_evidence,
)
from src.core.prime_power_observer_genesis_p3og_semantic_retained_difference import (
    build_p3og_semantic_retained_difference_evidence,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
)


def _fixture(label: str = "semantic-complete-history-current"):
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
    plan = p3og_semantic_preselection_history_plan(
        source,
        autonomous,
        semantic,
        bridge_contract,
        ablation,
        intervention,
        selection_source,
        available,
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
    removal = build_p3og_semantic_matched_ablation_removal_evidence(
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
    return (
        source,
        autonomous,
        semantic,
        bridge_contract,
        ablation,
        intervention,
        arithmetic,
        plan,
        formation_source,
        formation,
        bridge,
        retained,
        phase,
        removal,
    )


def _build(fixture):
    return build_p3og_semantic_complete_history_evidence(*fixture)


def test_coherent_candidate_is_one_forward_noncircular_history_v6() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    ids = tuple(event.event_id for event in evidence.events)
    table = {event.event_id: event for event in evidence.events}

    chain = (
        "first-closure",
        "semantic-first-closure",
        "arithmetic-input-source",
        "arithmetic-coupling",
        "typed-ablation",
        "retained-difference",
        "residue-phase-effect",
        "removal-dependence",
        "decisive-criterion",
        "later-result",
    )
    assert all(ids.index(left) < ids.index(right) for left, right in zip(chain, chain[1:]))
    assert evidence.status is FormationHistoryStatus.WITNESSED
    assert {
        "semantic-configuration-contract",
        "semantic-formation-bridge-contract",
        "semantic-ablation-contract",
        "semantic-intervention-plan",
        "selection-consume",
    }.issubset(evidence.strict_past_event_ids)
    assert set(chain[1:]).issubset(evidence.future_event_ids)
    assert set(chain[1:]).isdisjoint(evidence.strict_past_event_ids)

    selection_sources = set(
        table["selection-consume"].source_closure.transitive_source_event_ids
    )
    assert "semantic-intervention-plan" not in selection_sources
    assert set(chain[1:]).isdisjoint(selection_sources)

    assert table["semantic-first-closure"].source_closure.direct_source_event_ids == (
        "first-closure",
        "semantic-formation-bridge-contract",
    )
    assert table["arithmetic-input-source"].source_closure.direct_source_event_ids == (
        "source",
    )
    assert table["arithmetic-coupling"].source_closure.direct_source_event_ids == (
        "semantic-first-closure",
        "arithmetic-input-source",
    )
    assert table["typed-ablation"].source_closure.direct_source_event_ids == (
        "arithmetic-coupling",
        "semantic-ablation-contract",
    )
    assert table["retained-difference"].source_closure.direct_source_event_ids == (
        "arithmetic-coupling",
        "semantic-intervention-plan",
    )
    assert table["residue-phase-effect"].source_closure.direct_source_event_ids == (
        "retained-difference",
    )
    assert table["removal-dependence"].source_closure.direct_source_event_ids == (
        "residue-phase-effect",
        "typed-ablation",
    )
    assert table["typed-ablation"].logical_time < table["residue-phase-effect"].logical_time
    assert table["removal-dependence"].parent_ids == (
        "residue-phase-effect",
        "typed-ablation",
    )
    assert table["decisive-criterion"].parent_ids == ("removal-dependence",)
    assert table["later-result"].parent_ids == (
        "removal-dependence",
        "decisive-criterion",
    )
    assert evidence.promotions == 0
    assert "full-def-og-009-discharge" in evidence.nonclaims
    assert "typed-post-formation-ablation" in evidence.nonclaims
    assert "same-token-causal-efficacy" in evidence.nonclaims


def test_specialized_complete_history_fresh_validation_rebuilds_exact_dag() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    replay = validate_p3og_semantic_complete_history_evidence(
        *fixture,
        evidence,
    )
    assert replay == evidence
    assert replay is not evidence

    events = list(evidence.events)
    index = next(
        i for i, event in enumerate(events) if event.event_id == "removal-dependence"
    )
    events[index] = replace(events[index], payload_digest="e" * 64)
    forged = replace(evidence, events=tuple(events))
    with pytest.raises(ValueError):
        validate_p3og_semantic_complete_history_evidence(
            *fixture,
            forged,
        )


def test_foreign_removal_witness_cannot_splice_into_complete_history() -> None:
    fixture = _fixture()
    foreign = _fixture("semantic-complete-history-foreign")

    with pytest.raises(ValueError):
        build_p3og_semantic_complete_history_evidence(
            *fixture[:-1],
            foreign[-1],
        )


def test_plain_history_cannot_admit_semantic_postclosure_without_commitments() -> None:
    fixture = _fixture()
    source = fixture[0]
    autonomous = fixture[1]
    formation_source = fixture[8]
    formation = fixture[9]
    selection_source = formation_source.selection_source
    plain_plan = p3og_formation_history_plan(
        source,
        autonomous,
        selection_source,
        formation_source.selection_before,
    )
    bindings = FormationHistoryPostClosureBindings(
        *("d" * 64 for _ in range(7)),
    )
    with pytest.raises(ValueError, match="postclosure-missing-precommitments"):
        build_p3og_formation_history_evidence(
            source,
            autonomous,
            plain_plan,
            formation_source,
            formation,
            "a" * 64,
            "b" * 64,
            bindings,
        )


def test_refuted_formation_cannot_receive_postclosure_bindings() -> None:
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="semantic-complete-history-refuted",
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
            TransitionKind.IDLE,
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
    formation = run_p3og_native_formation(source, autonomous, formation_source)
    plan = p3og_formation_history_plan(
        source,
        autonomous,
        selection_source,
        available,
    )
    bindings = FormationHistoryPostClosureBindings(
        *("d" * 64 for _ in range(7)),
    )
    with pytest.raises(ValueError, match="refuted-postclosure"):
        build_p3og_formation_history_evidence(
            source,
            autonomous,
            plan,
            formation_source,
            formation,
            None,
            None,
            bindings,
        )
