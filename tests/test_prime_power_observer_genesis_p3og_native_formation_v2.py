"""Focused/hostile candidate tests for authority-free native P3-OG formation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.prime_power_observer_genesis_p3og import (
    TransitionKind,
    deterministic_select,
    p3og_source,
)
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    NativeFormationBoundary,
    NativeFormationStatus,
    p3og_native_formation_source,
    run_p3og_native_formation,
    validate_p3og_native_formation_evidence,
)
from src.core.prime_power_observer_genesis_p3og_native_formation_runtime import (
    _validate_native_formation_state,
)
from src.core.prime_power_observer_genesis_p3og_native_formation_types import (
    NativeFormationTickReceipt,
)
from src.core.prime_power_observer_genesis_p3og_one_shot_selection import (
    consume_p3og_selection_capability,
    p3og_initial_selection_capability,
    p3og_one_shot_selection_source,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _source(period: int = 2, credit: int = 2, label: str = "formation-v2"):
    cycle = tuple(range(period)) + (0,)
    return p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label,
        seed_rows=(("alpha", cycle),),
        calibration_inputs=(0, 1),
        maintenance_credit=credit,
        suffix=(TransitionKind.IDLE,),
    )


def _autonomous(source, high: TransitionKind, low: TransitionKind):
    rules = (
        autonomous_tick_rule(
            MaintenanceControlState.ACTIVE,
            MaintenanceCreditClass.HIGH,
            high,
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
    return p3og_autonomous_tick_source(source, rules)


def _formation_source(source, autonomous, blind: str = "a" * 64):
    selection_source = p3og_one_shot_selection_source(source, blind)
    available = p3og_initial_selection_capability(source, selection_source)
    _, consumed, receipt = consume_p3og_selection_capability(
        source,
        selection_source,
        available,
    )
    return p3og_native_formation_source(
        source,
        autonomous,
        selection_source,
        available,
        consumed,
        receipt,
    )


def test_native_formation_is_derived_only_after_genuine_return() -> None:
    source = _source()
    autonomous = _autonomous(source, TransitionKind.IDLE, TransitionKind.MAINTAIN)
    formation_source = _formation_source(source, autonomous)
    evidence = run_p3og_native_formation(source, autonomous, formation_source)

    assert evidence.status is NativeFormationStatus.WITNESSED
    assert evidence.initial_state.boundary is NativeFormationBoundary.UNFORMED
    assert evidence.final_state.boundary is NativeFormationBoundary.ALIVE
    assert evidence.first_closure_step == 2
    assert evidence.ticks[0].became_departed is True
    assert evidence.ticks[-1].became_alive is True
    assert evidence.state_space_bound == 3
    assert formation_source.max_formation_ticks == 126
    assert evidence.promotions == 0


def test_native_formation_uses_one_shot_receipt_not_legacy_selector() -> None:
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="one-shot-native-formation-selection",
        seed_rows=(
            ("alpha", (0, 1, 0)),
            ("beta", (0, 1, 2, 0)),
            ("gamma", (0, 2, 1, 0)),
        ),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=(TransitionKind.IDLE,),
    )
    autonomous = _autonomous(source, TransitionKind.IDLE, TransitionKind.MAINTAIN)
    legacy = deterministic_select(source)
    selected = None
    for nonce in range(256):
        selection_source = p3og_one_shot_selection_source(
            source,
            f"{nonce:064x}",
        )
        available = p3og_initial_selection_capability(source, selection_source)
        _, consumed, receipt = consume_p3og_selection_capability(
            source,
            selection_source,
            available,
        )
        if receipt.selected_index != legacy.selected_index:
            selected = (selection_source, available, consumed, receipt)
            break
    assert selected is not None
    selection_source, available, consumed, receipt = selected
    formation_source = p3og_native_formation_source(
        source,
        autonomous,
        selection_source,
        available,
        consumed,
        receipt,
    )
    evidence = run_p3og_native_formation(source, autonomous, formation_source)
    assert formation_source.selection == receipt
    assert formation_source.selected_seed_digest == source.seeds[
        receipt.selected_index
    ].seed_digest
    assert evidence.initial_state.selected_seed_digest == receipt.selected_seed_digest


def test_removal_self_loop_and_disjoint_cycle_do_not_form() -> None:
    cases = (
        (TransitionKind.IDLE, TransitionKind.IDLE, "native-boundary-removed-before-formation"),
        (TransitionKind.MAINTAIN, TransitionKind.IDLE, "native-formation-never-departs"),
        (TransitionKind.IDLE, TransitionKind.ADVANCE, "native-formation-entered-disjoint-cycle"),
    )
    for index, (high, low, reason) in enumerate(cases):
        source = _source(label=f"formation-refutation-{index}")
        autonomous = _autonomous(source, high, low)
        formation_source = _formation_source(source, autonomous)
        evidence = run_p3og_native_formation(source, autonomous, formation_source)
        assert evidence.status is NativeFormationStatus.REFUTED
        assert evidence.final_state.boundary is NativeFormationBoundary.UNFORMED
        assert evidence.reason == reason
        assert evidence.first_closure_step is None


def test_forged_formation_tick_count_fails_closed() -> None:
    source = _source()
    autonomous = _autonomous(source, TransitionKind.IDLE, TransitionKind.MAINTAIN)
    formation_source = _formation_source(source, autonomous)
    evidence = run_p3og_native_formation(source, autonomous, formation_source)
    forged = replace(evidence.initial_state, tick_count=1)
    with pytest.raises(ValueError):
        _validate_native_formation_state(source, formation_source, forged)


def test_hostile_nested_tick_is_rejected_before_codec_callback() -> None:
    source = _source()
    autonomous = _autonomous(source, TransitionKind.IDLE, TransitionKind.MAINTAIN)
    formation_source = _formation_source(source, autonomous)
    evidence = run_p3og_native_formation(source, autonomous, formation_source)

    class HostileTick(NativeFormationTickReceipt):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileTick)
    forged = replace(evidence, ticks=(hostile,))
    with pytest.raises(ValueError):
        validate_p3og_native_formation_evidence(
            source, autonomous, formation_source, forged,
        )
