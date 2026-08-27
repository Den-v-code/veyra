"""Focused/hostile tests for bounded P3-OG formation replay history."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_formation_history import (
    build_p3og_formation_history_evidence,
    p3og_formation_history_plan,
    validate_p3og_formation_history_evidence,
)
from src.core.prime_power_observer_genesis_p3og_formation_history_types import (
    FormationHistoryEvent,
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
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _fixture(*, low: TransitionKind = TransitionKind.MAINTAIN):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=f"formation-history-{low.value}",
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
            low,
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
    _, consumed, receipt = consume_p3og_selection_capability(
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
        receipt,
    )
    formation = run_p3og_native_formation(source, autonomous, formation_source)
    plan = p3og_formation_history_plan(
        source,
        autonomous,
        selection_source,
        available,
    )
    return source, autonomous, formation_source, formation, plan


def test_formation_contract_is_committed_before_selection() -> None:
    source, autonomous, formation_source, formation, plan = _fixture()
    evidence = build_p3og_formation_history_evidence(
        source,
        autonomous,
        plan,
        formation_source,
        formation,
        "a" * 64,
        "b" * 64,
    )
    ids = tuple(event.event_id for event in evidence.events)
    assert ids.index("formation-contract") < ids.index("selection-consume")
    assert ids.index("blind-seed") < ids.index("selection-source-closure")
    assert ids.index("selection-source-closure") < ids.index("selection-consume")
    assert ids.index("selection-pool") < ids.index("selection-consume")
    assert ids.index("selection-capability-available") < ids.index(
        "selection-consume"
    )
    assert ids.index("selection-consume") < ids.index(
        "selection-capability-consumed"
    )
    assert "formation-contract" in evidence.strict_past_event_ids
    assert "blind-seed" in evidence.strict_past_event_ids
    assert "selection-source-closure" in evidence.strict_past_event_ids
    assert "selection-pool" in evidence.strict_past_event_ids
    assert "selection-capability-available" in evidence.strict_past_event_ids
    assert "selection-consume" in evidence.strict_past_event_ids
    assert "selection-capability-consumed" in evidence.strict_past_event_ids
    assert "decisive-criterion" in evidence.future_event_ids
    assert "later-result" in evidence.future_event_ids
    assert len(evidence.events) == len(formation.ticks) + 15
    assert plan.max_events == 256
    assert plan.max_parents_per_event == 8
    plan_fields = {field.name for field in fields(plan)}
    assert "selected_seed_digest" not in plan_fields
    assert "selection_receipt_digest" not in plan_fields
    assert "criterion_payload_digest" not in plan_fields
    assert "later_result_payload_digest" not in plan_fields
    assert plan.selection_source_digest == formation_source.selection_source.source_digest
    assert plan.available_capability_digest == (
        formation_source.selection_before.capability_digest
    )
    assert evidence.promotions == 0
    assert "full-def-og-002-discharge" in evidence.nonclaims
    assert "process-global-unforgeable-linear-capability" in evidence.nonclaims
    assert "endogenous-observer-role" in evidence.nonclaims
    assert "birth-core-or-historical-token" in evidence.nonclaims
    assert "n0-or-hap-lift" in evidence.nonclaims
    assert "historical-actualization" in evidence.nonclaims


def test_future_seal_cannot_be_preloaded_in_preclosure_digest_inventory() -> None:
    source, autonomous, formation_source, formation, plan = _fixture()
    preloaded = (
        formation_source.selected_seed_digest,
        formation_source.selection.receipt_digest,
        formation_source.selection_source.blind_seed_digest,
        formation_source.selection_before.capability_digest,
        formation_source.selection_after.capability_digest,
        formation.evidence_digest,
        plan.lineage_id,
    )
    for digest in preloaded:
        with pytest.raises(ValueError, match="future-seal-preloaded"):
            build_p3og_formation_history_evidence(
                source,
                autonomous,
                plan,
                formation_source,
                formation,
                digest,
                "c" * 64,
            )


def test_history_plan_requires_the_exact_available_preselection_cut() -> None:
    source, autonomous, formation_source, _, _ = _fixture()
    with pytest.raises(ValueError, match="plan-capability-consumed"):
        p3og_formation_history_plan(
            source,
            autonomous,
            formation_source.selection_source,
            formation_source.selection_after,
        )


def test_history_plan_cannot_be_spliced_across_blind_selection_sources() -> None:
    source, autonomous, formation_source, formation, plan = _fixture()
    foreign_selection_source = p3og_one_shot_selection_source(source, "e" * 64)
    foreign_available = p3og_initial_selection_capability(
        source,
        foreign_selection_source,
    )
    _, foreign_consumed, foreign_receipt = consume_p3og_selection_capability(
        source,
        foreign_selection_source,
        foreign_available,
    )
    foreign_formation_source = p3og_native_formation_source(
        source,
        autonomous,
        foreign_selection_source,
        foreign_available,
        foreign_consumed,
        foreign_receipt,
    )
    foreign_formation = run_p3og_native_formation(
        source,
        autonomous,
        foreign_formation_source,
    )
    assert foreign_formation_source.source_digest != formation_source.source_digest
    with pytest.raises(ValueError):
        build_p3og_formation_history_evidence(
            source,
            autonomous,
            plan,
            foreign_formation_source,
            foreign_formation,
            "a" * 64,
            "b" * 64,
        )


def test_external_future_seals_are_fresh_validation_premises() -> None:
    source, autonomous, formation_source, formation, plan = _fixture()
    evidence = build_p3og_formation_history_evidence(
        source,
        autonomous,
        plan,
        formation_source,
        formation,
        "a" * 64,
        "b" * 64,
    )
    validate_p3og_formation_history_evidence(
        source,
        autonomous,
        plan,
        formation_source,
        formation,
        "a" * 64,
        "b" * 64,
        evidence,
    )
    with pytest.raises(ValueError):
        validate_p3og_formation_history_evidence(
            source,
            autonomous,
            plan,
            formation_source,
            formation,
            "d" * 64,
            "b" * 64,
            evidence,
        )


def test_refuted_selected_seed_is_preserved_without_retry_or_future_seals() -> None:
    source, autonomous, formation_source, formation, plan = _fixture(
        low=TransitionKind.IDLE,
    )
    evidence = build_p3og_formation_history_evidence(
        source,
        autonomous,
        plan,
        formation_source,
        formation,
        None,
        None,
    )
    assert evidence.status is FormationHistoryStatus.REFUTED
    assert evidence.formation_terminal_event_id == "formation-refutation"
    assert evidence.closure_event_id is None
    assert evidence.criterion_event_id is None
    assert evidence.later_result_event_id is None
    assert evidence.future_event_ids == ()
    assert "selection-consume" in evidence.strict_past_event_ids
    assert len(evidence.events) == len(formation.ticks) + 13
    rebuilt = validate_p3og_formation_history_evidence(
        source,
        autonomous,
        plan,
        formation_source,
        formation,
        None,
        None,
        evidence,
    )
    assert rebuilt == evidence
    with pytest.raises(ValueError, match="capability-consumed"):
        consume_p3og_selection_capability(
            source,
            formation_source.selection_source,
            formation_source.selection_after,
        )
    with pytest.raises(ValueError, match="refuted-future-seal"):
        build_p3og_formation_history_evidence(
            source,
            autonomous,
            plan,
            formation_source,
            formation,
            "a" * 64,
            "b" * 64,
        )


def test_spliced_parent_chain_fails_fresh_replay() -> None:
    source, autonomous, formation_source, formation, plan = _fixture()
    evidence = build_p3og_formation_history_evidence(
        source,
        autonomous,
        plan,
        formation_source,
        formation,
        "a" * 64,
        "b" * 64,
    )
    events = list(evidence.events)
    closure_index = next(
        index for index, event in enumerate(events)
        if event.event_id == evidence.closure_event_id
    )
    events[closure_index] = replace(
        events[closure_index],
        parent_ids=("source",),
    )
    forged = replace(evidence, events=tuple(events))
    with pytest.raises(ValueError):
        validate_p3og_formation_history_evidence(
            source,
            autonomous,
            plan,
            formation_source,
            formation,
            "a" * 64,
            "b" * 64,
            forged,
        )


def test_hostile_nested_event_is_rejected_before_codec_callback() -> None:
    source, autonomous, formation_source, formation, plan = _fixture()
    evidence = build_p3og_formation_history_evidence(
        source,
        autonomous,
        plan,
        formation_source,
        formation,
        "a" * 64,
        "b" * 64,
    )

    class HostileEvent(FormationHistoryEvent):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileEvent)
    forged = replace(evidence, events=(hostile,))
    with pytest.raises(ValueError):
        validate_p3og_formation_history_evidence(
            source,
            autonomous,
            plan,
            formation_source,
            formation,
            "a" * 64,
            "b" * 64,
            forged,
        )
