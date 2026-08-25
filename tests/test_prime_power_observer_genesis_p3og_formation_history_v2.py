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
)
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    p3og_native_formation_source,
    run_p3og_native_formation,
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
    formation_source = p3og_native_formation_source(source, autonomous)
    formation = run_p3og_native_formation(source, autonomous, formation_source)
    plan = p3og_formation_history_plan(source, autonomous)
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
    assert ids.index("formation-contract") < ids.index("selection")
    assert "formation-contract" in evidence.strict_past_event_ids
    assert "decisive-criterion" in evidence.future_event_ids
    assert "later-result" in evidence.future_event_ids
    assert len(evidence.events) == len(formation.ticks) + 9
    assert plan.max_events == 256
    assert plan.max_parents_per_event == 8
    assert "selection" not in {field.name for field in fields(plan)}
    assert evidence.promotions == 0


def test_future_seal_cannot_be_preloaded_in_preclosure_digest_inventory() -> None:
    source, autonomous, formation_source, formation, plan = _fixture()
    preloaded = (
        formation_source.selected_seed_digest,
        formation_source.selection.receipt_digest,
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


def test_refuted_native_formation_cannot_mint_history_witness() -> None:
    source, autonomous, formation_source, formation, plan = _fixture(
        low=TransitionKind.IDLE,
    )
    with pytest.raises(ValueError, match="requires-witnessed-formation"):
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
