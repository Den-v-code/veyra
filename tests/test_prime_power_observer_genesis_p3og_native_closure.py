"""Focused laws for bounded P3-OG native-state first-closure pressure."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

import src.core.prime_power_observer_genesis_p3og_native_closure as closure_facade
from src.core.prime_power_observer_genesis_p3og import (
    PressureStatus,
    TransitionKind,
    deterministic_select,
    p3og_source,
    run_p3og_pressure,
)
from src.core.prime_power_observer_genesis_p3og_codec import digest as pressure_digest
from src.core.prime_power_observer_genesis_p3og_lifecycle import (
    FirstClosureStatus,
    p3og_formation_source,
    run_p3og_first_closure,
)
from src.core.prime_power_observer_genesis_p3og_lifecycle_codec import (
    lifecycle_digest,
)
from src.core.prime_power_observer_genesis_p3og_native_closure import (
    NativeClosureStatus,
    P3OGNativeClosureSource,
    P3OGNativeFirstClosureEvidence,
    P3OG_NATIVE_CLOSURE_NONCLAIMS,
    p3og_native_closure_source,
    run_p3og_native_first_closure,
    validate_native_closure_source,
    validate_p3og_native_first_closure_evidence,
)
from src.core.prime_power_observer_genesis_p3og_native_closure_codec import (
    native_closure_digest,
)

SUFFIX = (
    TransitionKind.IDLE,
    TransitionKind.MAINTAIN,
    TransitionKind.IDLE,
    TransitionKind.ADVANCE,
)


def _source(
    word: tuple[int, ...],
    label: str = "alpha",
    source_instance: str = "native-closure-source",
):
    return p3og_source(
        prime=3,
        depth=1,
        source_instance_label=source_instance,
        seed_rows=((label, word),),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=SUFFIX,
    )


def _run(word: tuple[int, ...]):
    source = _source(word)
    closure_source = p3og_native_closure_source(source)
    evidence = run_p3og_native_first_closure(source, closure_source)
    return source, closure_source, evidence


def test_native_transition_replay_witnesses_first_projected_return() -> None:
    _source_value, closure_source, evidence = _run((0, 1, 0))
    assert closure_source.step_bound == 2
    assert closure_source.transition_kind is TransitionKind.ADVANCE
    assert evidence.status is NativeClosureStatus.WITNESSED
    assert evidence.reason == "least-native-state-return-witnessed"
    assert evidence.first_closure_step == 2
    assert evidence.initial_state.phase == 0
    assert evidence.final_state.phase == 0
    assert evidence.initial_state.transition_count == 0
    assert evidence.final_state.transition_count == 2
    assert evidence.steps[0].became_departed is True
    assert evidence.steps[0].became_closed is False
    assert evidence.steps[-1].became_closed is True
    assert evidence.promotions == 0


def test_native_receipts_bind_continuous_exact_transition_chain() -> None:
    _source_value, _closure_source, evidence = _run((0, 1, 2, 0))
    assert evidence.steps[0].before_state_digest == evidence.initial_state.state_digest
    assert all(
        left.after_state_digest == right.before_state_digest
        for left, right in zip(evidence.steps, evidence.steps[1:], strict=True)
    )
    assert evidence.steps[-1].after_state_digest == evidence.final_state.state_digest
    assert all(
        step.transition.before_digest == step.before_state_digest
        and step.transition.after_digest == step.after_state_digest
        for step in evidence.steps
    )


def test_terminal_raw_coordinate_does_not_control_native_closure_verdict() -> None:
    source_a, closure_a, evidence_a = _run((0, 1, 0))
    source_b, closure_b, evidence_b = _run((0, 1, 2))
    assert source_a.source_digest != source_b.source_digest
    assert closure_a.source_digest != closure_b.source_digest
    assert evidence_a.status is evidence_b.status is NativeClosureStatus.WITNESSED
    assert evidence_a.first_closure_step == evidence_b.first_closure_step == 2

    raw_a = run_p3og_first_closure(source_a, p3og_formation_source(source_a))
    raw_b = run_p3og_first_closure(source_b, p3og_formation_source(source_b))
    assert raw_a.status is FirstClosureStatus.WITNESSED
    assert raw_b.status is FirstClosureStatus.REFUTED


def test_blind_seed_may_close_natively_while_discrimination_remains_refuted() -> None:
    source, _closure_source, evidence = _run((0, 0, 0))
    report = run_p3og_pressure(source)
    assert evidence.status is NativeClosureStatus.WITNESSED
    assert evidence.first_closure_step == 2
    assert report.status is PressureStatus.REFUTED
    assert report.reason == "blind-seed"


@pytest.mark.parametrize("word", [(0, 0), (0, 1)])
def test_period_one_never_genuinely_departs(word: tuple[int, ...]) -> None:
    _source_value, closure_source, evidence = _run(word)
    assert closure_source.step_bound == 1
    assert evidence.status is NativeClosureStatus.REFUTED
    assert evidence.reason == "native-state-never-departs"
    assert evidence.first_closure_step is None
    assert len(evidence.steps) == 1
    assert evidence.steps[0].became_departed is False
    assert evidence.steps[0].became_closed is False


def test_source_exposes_exact_probe_scope_and_is_freshly_reconstructed() -> None:
    source, closure_source, _evidence = _run((0, 1, 0))
    assert closure_source.version == "p3og-native-closure-source-v1"
    assert closure_source.pressure_source_digest == source.source_digest
    assert closure_source.step_bound == 2
    assert closure_source.transition_kind is TransitionKind.ADVANCE
    assert closure_source.transition_rule_id == "fixed-source-bound-advance-probe-v1"
    assert closure_source.projection_rule_id == (
        "machine-configuration-minus-counter-and-digest-v1"
    )
    assert closure_source.projection_excluded_fields == (
        "transition_count",
        "state_digest",
    )
    assert closure_source.closure_rule_id == "least-return-after-genuine-departure-v1"
    rebuilt_source, rebuilt = validate_native_closure_source(source, closure_source)
    assert rebuilt_source == source
    assert rebuilt == closure_source
    assert rebuilt is not closure_source


def test_multiseed_source_reuses_existing_deterministic_selection_only() -> None:
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="native-closure-multiseed",
        seed_rows=(
            ("alpha", (10, 11, 10)),
            ("beta", (20, 21, 20)),
            ("gamma", (30, 31, 30)),
        ),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=SUFFIX,
    )
    existing = deterministic_select(source)
    closure_source = p3og_native_closure_source(source)
    assert closure_source.selection == existing
    assert closure_source.selected_seed_digest == (
        source.seeds[existing.selected_index].seed_digest
    )


def test_validation_freshly_replays_complete_nested_evidence() -> None:
    source, closure_source, evidence = _run((0, 1, 0))
    replay = validate_p3og_native_first_closure_evidence(
        source,
        closure_source,
        evidence,
    )
    assert replay == evidence
    assert replay is not evidence
    assert replay.initial_state is not evidence.initial_state
    assert replay.steps is not evidence.steps


def test_foreign_and_tampered_sources_or_evidence_fail_closed() -> None:
    source, closure_source, evidence = _run((0, 1, 0))
    foreign = _source((7, 8, 7), label="foreign", source_instance="foreign")
    with pytest.raises(ValueError):
        validate_native_closure_source(foreign, closure_source)
    with pytest.raises(ValueError):
        validate_native_closure_source(
            source,
            replace(closure_source, transition_kind=TransitionKind.IDLE),
        )
    with pytest.raises(ValueError):
        validate_p3og_native_first_closure_evidence(
            source,
            closure_source,
            replace(evidence, first_closure_step=1),
        )
    forged_step = replace(evidence.steps[0], became_closed=True)
    with pytest.raises(ValueError):
        validate_p3og_native_first_closure_evidence(
            source,
            closure_source,
            replace(evidence, steps=(forged_step, *evidence.steps[1:])),
        )


def test_uninitialized_exact_dtos_fail_typed() -> None:
    source = _source((0, 1, 0))
    with pytest.raises(ValueError, match="p3og-native-closure-source-malformed"):
        validate_native_closure_source(
            source,
            object.__new__(P3OGNativeClosureSource),
        )
    closure_source = p3og_native_closure_source(source)
    with pytest.raises(
        ValueError,
        match="p3og-native-first-closure-evidence-malformed",
    ):
        validate_p3og_native_first_closure_evidence(
            source,
            closure_source,
            object.__new__(P3OGNativeFirstClosureEvidence),
        )


def test_native_closure_digest_domain_is_isolated() -> None:
    values = ("same", (0, 1, 0))
    native = native_closure_digest("native-closure-source", *values)
    assert native != pressure_digest("native-closure-source", *values)
    assert native != lifecycle_digest("native-closure-source", *values)


def test_native_closure_is_non_root_and_grants_no_role_or_history_authority() -> None:
    _source_value, _closure_source, evidence = _run((0, 1, 0))
    assert evidence.nonclaims == P3OG_NATIVE_CLOSURE_NONCLAIMS
    names = {field.name for field in fields(P3OGNativeFirstClosureEvidence)}
    assert {
        "observer_role",
        "historical_token_id",
        "birth_core_digest",
        "doctrine_admission",
        "hap_witness",
        "ablation_receipt",
    }.isdisjoint(names)
    assert {
        "advance-probe-is-not-def-og-001-tick",
        "autonomous-native-tick-not-established",
        "operational-alive-is-not-formation-boundary",
        "full-def-og-003-discharge",
        "historical-formation-or-chronology",
        "endogenous-observer-role",
        "post-formation-ablation",
        "same-token-causal-efficacy",
        "promotion",
    }.issubset(evidence.nonclaims)
    assert closure_facade.__all__ == (
        "NativeClosureStatus",
        "NativeClosureStepReceipt",
        "P3OGNativeClosureSource",
        "P3OGNativeFirstClosureEvidence",
        "P3OG_NATIVE_CLOSURE_NONCLAIMS",
        "p3og_native_closure_source",
        "run_p3og_native_first_closure",
        "validate_native_closure_source",
        "validate_p3og_native_first_closure_evidence",
    )
    import src.core as root_core

    assert not hasattr(root_core, "run_p3og_native_first_closure")
    assert not hasattr(root_core, "P3OGNativeFirstClosureEvidence")


def test_source_and_evidence_do_not_expose_authority_fields() -> None:
    source_names = {field.name for field in fields(P3OGNativeClosureSource)}
    evidence_names = {field.name for field in fields(P3OGNativeFirstClosureEvidence)}
    forbidden = {
        "status_target",
        "expected_closure_step",
        "observer_role",
        "historical_token_id",
        "birth_core_digest",
        "doctrine_admission",
    }
    assert forbidden.isdisjoint(source_names)
    assert forbidden.isdisjoint(evidence_names)
