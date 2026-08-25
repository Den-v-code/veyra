"""Focused laws for bounded P3-OG state-extensional autonomous ticks."""

from __future__ import annotations

from dataclasses import fields, replace
from inspect import signature

import pytest

import src.core.prime_power_observer_genesis_p3og_autonomous_tick as autonomous_facade
from src.core.prime_power_observer_genesis_p3og import (
    TransitionKind,
    deterministic_select,
    p3og_source,
)
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    AutonomousTickStatus,
    MaintenanceCreditClass,
    P3OGAutonomousFirstClosureEvidence,
    P3OGAutonomousTickSource,
    P3OG_AUTONOMOUS_TICK_NONCLAIMS,
    autonomous_tick,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
    run_p3og_autonomous_first_closure,
    validate_autonomous_tick_source,
    validate_p3og_autonomous_first_closure_evidence,
)
from src.core.prime_power_observer_genesis_p3og_autonomous_tick_codec import (
    autonomous_tick_digest,
)
from src.core.prime_power_observer_genesis_p3og_codec import digest as pressure_digest
from src.core.prime_power_observer_genesis_p3og_machine import (
    apply_pre_coupling_maintenance_control,
    initial_state,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState

SUFFIX = (
    TransitionKind.IDLE,
    TransitionKind.MAINTAIN,
    TransitionKind.IDLE,
    TransitionKind.ADVANCE,
)


def _source(
    word: tuple[int, ...] = (0, 1, 0),
    *,
    maintenance_credit: int = 2,
    source_instance: str = "autonomous-tick-source",
):
    return p3og_source(
        prime=3,
        depth=1,
        source_instance_label=source_instance,
        seed_rows=(("alpha", word),),
        calibration_inputs=(0, 1),
        maintenance_credit=maintenance_credit,
        suffix=SUFFIX,
    )


def _rules(
    *,
    active_low: TransitionKind = TransitionKind.MAINTAIN,
):
    return (
        autonomous_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.HIGH,
            TransitionKind.IDLE,
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


def _run(
    word: tuple[int, ...] = (0, 1, 0),
    *,
    active_low: TransitionKind = TransitionKind.MAINTAIN,
    maintenance_credit: int = 2,
):
    source = _source(word, maintenance_credit=maintenance_credit)
    autonomous_source = p3og_autonomous_tick_source(
        source,
        _rules(active_low=active_low),
    )
    evidence = run_p3og_autonomous_first_closure(source, autonomous_source)
    return source, autonomous_source, evidence


def test_state_feedback_tick_witnesses_exact_configuration_return() -> None:
    source, _autonomous_source, evidence = _run()
    assert evidence.status is AutonomousTickStatus.WITNESSED
    assert evidence.reason == "least-autonomous-native-state-return-witnessed"
    assert evidence.first_closure_step == 2
    assert tuple(tick.selected_kind for tick in evidence.ticks) == (
        TransitionKind.IDLE,
        TransitionKind.MAINTAIN,
    )
    assert evidence.initial_state.maintenance_credit == source.maintenance_credit == 2
    assert evidence.final_state.maintenance_credit == 2
    assert evidence.initial_state.phase == evidence.final_state.phase == 0
    assert evidence.initial_state.retained_residue is evidence.final_state.retained_residue is None
    assert evidence.initial_state.boundary is evidence.final_state.boundary
    assert evidence.initial_state.maintenance_control is evidence.final_state.maintenance_control
    assert evidence.initial_state.transition_count == 0
    assert evidence.final_state.transition_count == 2
    assert evidence.promotions == 0


def test_positive_and_negative_programs_differ_in_exactly_one_committed_row() -> None:
    source = _source()
    positive = p3og_autonomous_tick_source(source, _rules())
    negative = p3og_autonomous_tick_source(
        source,
        _rules(active_low=TransitionKind.IDLE),
    )
    assert positive.pressure_source_digest == negative.pressure_source_digest
    differences = tuple(
        (left, right)
        for left, right in zip(positive.rules, negative.rules, strict=True)
        if left != right
    )
    assert len(differences) == 1
    left, right = differences[0]
    assert left.maintenance_control is right.maintenance_control is MaintenanceControlState.ACTIVE
    assert left.credit_class is right.credit_class is MaintenanceCreditClass.LOW
    assert left.transition_kind is TransitionKind.MAINTAIN
    assert right.transition_kind is TransitionKind.IDLE


def test_one_row_negative_separator_removes_boundary_before_closure() -> None:
    _source_value, _autonomous_source, evidence = _run(
        active_low=TransitionKind.IDLE,
    )
    assert evidence.status is AutonomousTickStatus.REFUTED
    assert evidence.reason == "autonomous-boundary-removed-before-closure"
    assert evidence.first_closure_step is None
    assert tuple(tick.selected_kind for tick in evidence.ticks) == (
        TransitionKind.IDLE,
        TransitionKind.IDLE,
    )
    assert evidence.final_state.boundary.value == "removed"


def test_public_tick_has_no_transition_kind_or_step_input() -> None:
    parameters = tuple(signature(autonomous_tick).parameters)
    assert parameters == ("source", "autonomous_source", "seed", "state")


def test_same_exact_q_selects_same_transition_and_next_q() -> None:
    source = _source()
    autonomous_source = p3og_autonomous_tick_source(source, _rules())
    selection = deterministic_select(source)
    seed = source.seeds[selection.selected_index]
    state = initial_state(source, seed)
    left_state, left_receipt = autonomous_tick(source, autonomous_source, seed, state)
    right_state, right_receipt = autonomous_tick(source, autonomous_source, seed, state)
    assert left_state == right_state
    assert left_receipt == right_receipt
    assert left_receipt.selected_kind is TransitionKind.IDLE


def test_disabled_maintenance_drives_internal_removal_under_same_program() -> None:
    source = _source()
    autonomous_source = p3og_autonomous_tick_source(source, _rules())
    seed = source.seeds[deterministic_select(source).selected_index]
    state = initial_state(source, seed)
    state, _control = apply_pre_coupling_maintenance_control(source, seed, state)
    state, first = autonomous_tick(source, autonomous_source, seed, state)
    state, second = autonomous_tick(source, autonomous_source, seed, state)
    assert first.selected_kind is second.selected_kind is TransitionKind.IDLE
    assert state.boundary.value == "removed"


def test_low_credit_advance_enters_a_disjoint_native_cycle() -> None:
    _source_value, _autonomous_source, evidence = _run(
        active_low=TransitionKind.ADVANCE,
    )
    assert evidence.status is AutonomousTickStatus.REFUTED
    assert evidence.reason == "autonomous-native-state-entered-disjoint-cycle"
    assert evidence.first_closure_step is None
    assert tuple(tick.selected_kind for tick in evidence.ticks) == (
        TransitionKind.IDLE,
        TransitionKind.ADVANCE,
        TransitionKind.ADVANCE,
    )


def test_credit_one_maintain_self_loop_never_genuinely_departs() -> None:
    _source_value, _autonomous_source, evidence = _run(maintenance_credit=1)
    assert evidence.status is AutonomousTickStatus.REFUTED
    assert evidence.reason == "autonomous-native-state-never-departs"
    assert evidence.first_closure_step is None
    assert len(evidence.ticks) == 1
    assert evidence.ticks[0].selected_kind is TransitionKind.MAINTAIN


def test_terminal_raw_coordinate_does_not_control_autonomous_verdict() -> None:
    source_a, _autonomous_a, evidence_a = _run((0, 1, 0))
    source_b, _autonomous_b, evidence_b = _run((0, 1, 2))
    assert source_a.source_digest != source_b.source_digest
    assert evidence_a.status is evidence_b.status is AutonomousTickStatus.WITNESSED
    assert evidence_a.first_closure_step == evidence_b.first_closure_step == 2


def test_autonomous_source_commits_code_without_selection_or_outcome_fields() -> None:
    source = _source()
    autonomous_source = p3og_autonomous_tick_source(source, _rules())
    names = {field.name for field in fields(P3OGAutonomousTickSource)}
    assert autonomous_source.pressure_source_digest == source.source_digest
    assert {
        "selection",
        "selected_seed_digest",
        "status",
        "expected_status",
        "expected_closure_step",
        "target",
    }.isdisjoint(names)
    rebuilt_source, rebuilt = validate_autonomous_tick_source(source, autonomous_source)
    assert rebuilt_source == source
    assert rebuilt == autonomous_source
    assert rebuilt is not autonomous_source


def test_rule_table_is_total_unique_and_rejects_hidden_schedule_shapes() -> None:
    source = _source()
    with pytest.raises(ValueError, match="p3og-autonomous-tick-rules"):
        p3og_autonomous_tick_source(source, _rules()[:-1])
    duplicate = (_rules()[0], _rules()[0], *_rules()[2:])
    with pytest.raises(ValueError, match="p3og-autonomous-tick-rule-coverage"):
        p3og_autonomous_tick_source(source, duplicate)


def test_validation_freshly_replays_complete_evidence() -> None:
    source, autonomous_source, evidence = _run()
    replay = validate_p3og_autonomous_first_closure_evidence(
        source,
        autonomous_source,
        evidence,
    )
    assert replay == evidence
    assert replay is not evidence
    assert replay.initial_state is not evidence.initial_state
    assert replay.ticks is not evidence.ticks


def test_foreign_source_and_tampered_evidence_fail_closed() -> None:
    source, autonomous_source, evidence = _run()
    foreign = _source(source_instance="autonomous-tick-foreign")
    with pytest.raises(ValueError):
        validate_autonomous_tick_source(foreign, autonomous_source)
    forged_tick = replace(evidence.ticks[0], selected_kind=TransitionKind.ADVANCE)
    with pytest.raises(ValueError):
        validate_p3og_autonomous_first_closure_evidence(
            source,
            autonomous_source,
            replace(evidence, ticks=(forged_tick, *evidence.ticks[1:])),
        )
    with pytest.raises(ValueError):
        validate_p3og_autonomous_first_closure_evidence(
            source,
            autonomous_source,
            replace(evidence, first_closure_step=1),
        )


def test_uninitialized_exact_dtos_fail_typed() -> None:
    source = _source()
    with pytest.raises(ValueError, match="p3og-autonomous-tick-source-malformed"):
        validate_autonomous_tick_source(
            source,
            object.__new__(P3OGAutonomousTickSource),
        )
    autonomous_source = p3og_autonomous_tick_source(source, _rules())
    with pytest.raises(
        ValueError,
        match="p3og-autonomous-first-closure-evidence-malformed",
    ):
        validate_p3og_autonomous_first_closure_evidence(
            source,
            autonomous_source,
            object.__new__(P3OGAutonomousFirstClosureEvidence),
        )


def test_autonomous_tick_digest_domain_is_isolated() -> None:
    values = ("same", (0, 1, 0))
    autonomous = autonomous_tick_digest("autonomous-tick-source", *values)
    assert autonomous != pressure_digest("autonomous-tick-source", *values)


def test_autonomous_tick_is_non_root_and_grants_no_role_or_history_authority() -> None:
    _source_value, _autonomous_source, evidence = _run()
    assert evidence.nonclaims == P3OG_AUTONOMOUS_TICK_NONCLAIMS
    evidence_names = {field.name for field in fields(P3OGAutonomousFirstClosureEvidence)}
    assert {
        "observer_role",
        "historical_token_id",
        "birth_core_digest",
        "doctrine_admission",
        "hap_witness",
        "ablation_receipt",
    }.isdisjoint(evidence_names)
    assert {
        "historical-code-commitment-or-chronology",
        "full-def-og-001-discharge",
        "full-def-og-003-discharge",
        "historical-formation-or-history-dag",
        "endogenous-observer-role",
        "typed-post-formation-ablation",
        "same-token-causal-efficacy",
        "promotion",
    }.issubset(evidence.nonclaims)
    assert autonomous_facade.__all__ == (
        "AutonomousTickReceipt",
        "AutonomousTickRule",
        "AutonomousTickStatus",
        "MaintenanceCreditClass",
        "P3OGAutonomousFirstClosureEvidence",
        "P3OGAutonomousTickSource",
        "P3OG_AUTONOMOUS_TICK_NONCLAIMS",
        "autonomous_tick",
        "autonomous_tick_rule",
        "p3og_autonomous_tick_source",
        "run_p3og_autonomous_first_closure",
        "validate_autonomous_tick_source",
        "validate_p3og_autonomous_first_closure_evidence",
    )
    import src.core as root_core

    assert not hasattr(root_core, "autonomous_tick")
    assert not hasattr(root_core, "P3OGAutonomousFirstClosureEvidence")
