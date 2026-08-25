"""Exhaustive finite-state pressure for P3-OG autonomous tick programs."""

from __future__ import annotations

from itertools import product

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    AutonomousTickStatus,
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
    run_p3og_autonomous_first_closure,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState

_KEYS = (
    (MaintenanceControlState.ACTIVE, MaintenanceCreditClass.LOW),
    (MaintenanceControlState.ACTIVE, MaintenanceCreditClass.HIGH),
    (MaintenanceControlState.DISABLED, MaintenanceCreditClass.LOW),
    (MaintenanceControlState.DISABLED, MaintenanceCreditClass.HIGH),
)
_REASONS = {
    "least-autonomous-native-state-return-witnessed",
    "autonomous-boundary-removed-before-closure",
    "autonomous-native-state-never-departs",
    "autonomous-native-state-entered-disjoint-cycle",
}


def _source(period: int, credit: int):
    cycle = tuple(range(period + 1))
    return p3og_source(
        prime=3,
        depth=1,
        source_instance_label=f"autonomous-exhaustive-p{period}-c{credit}",
        seed_rows=(("alpha", cycle),),
        calibration_inputs=(0, 1),
        maintenance_credit=credit,
        suffix=(TransitionKind.IDLE,),
    )


def test_all_81_feedback_tables_terminate_exactly_on_small_state_spaces() -> None:
    """Every total four-row law must close or refute inside the finite Q bound."""
    kinds = tuple(TransitionKind)
    tables_checked = 0
    runs_checked = 0

    for transitions in product(kinds, repeat=len(_KEYS)):
        tables_checked += 1
        rules = tuple(
            autonomous_tick_rule(control, credit_class, kind)
            for (control, credit_class), kind in zip(
                _KEYS,
                transitions,
                strict=True,
            )
        )
        for period in (1, 2, 3):
            for credit in (1, 2, 3):
                source = _source(period, credit)
                autonomous_source = p3og_autonomous_tick_source(source, rules)
                evidence = run_p3og_autonomous_first_closure(
                    source,
                    autonomous_source,
                )
                runs_checked += 1

                assert evidence.status in (
                    AutonomousTickStatus.WITNESSED,
                    AutonomousTickStatus.REFUTED,
                )
                assert evidence.reason in _REASONS
                assert 1 <= len(evidence.ticks) <= evidence.state_space_bound
                assert evidence.state_space_bound == period * credit + 1
                if evidence.status is AutonomousTickStatus.WITNESSED:
                    assert evidence.first_closure_step == len(evidence.ticks)
                    assert evidence.reason == (
                        "least-autonomous-native-state-return-witnessed"
                    )
                else:
                    assert evidence.first_closure_step is None

    assert tables_checked == 81
    assert runs_checked == 729
