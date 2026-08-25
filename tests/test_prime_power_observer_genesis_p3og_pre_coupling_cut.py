"""Focused regression laws for the exact P3-OG pre-coupling control cut."""

from __future__ import annotations

import logging

import pytest

from src.core.prime_power_observer_genesis_p3og import (
    TransitionKind,
    p3og_source,
    run_p3og_pressure,
)
from src.core.prime_power_observer_genesis_p3og_formation_pressure import (
    build_p3og_formation_pressure_binding,
)
from src.core.prime_power_observer_genesis_p3og_lifecycle import (
    p3og_formation_source,
    run_p3og_first_closure,
)
from src.core.prime_power_observer_genesis_p3og_machine import (
    apply_pre_coupling_maintenance_control,
    couple,
    initial_state,
    transition,
)

logger = logging.getLogger(__name__)
GOOD_SEEDS = (("alpha", (0, 1, 0)), ("beta", (1, 0, 1)))
GOOD_SUFFIX = (
    TransitionKind.IDLE,
    TransitionKind.MAINTAIN,
    TransitionKind.IDLE,
    TransitionKind.ADVANCE,
)


def _source(*, source_instance: str = "source-1"):
    return p3og_source(
        prime=3,
        depth=1,
        source_instance_label=source_instance,
        seed_rows=GOOD_SEEDS,
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=GOOD_SUFFIX,
    )


def test_exact_initial_state_remains_the_only_accepted_pre_coupling_cut() -> None:
    source = _source()
    seed = source.seeds[0]
    state = initial_state(source, seed)
    controlled, receipt = apply_pre_coupling_maintenance_control(source, seed, state)
    assert receipt.enabled_state_digest == state.state_digest
    assert receipt.disabled_state_digest == controlled.state_digest


def test_post_coupling_state_cannot_mint_pre_coupling_receipt() -> None:
    source = _source()
    seed = source.seeds[0]
    state = initial_state(source, seed)
    coupled, _ = couple(source, seed, state, 0)
    with pytest.raises(
        ValueError,
        match="^p3og-maintenance-control-not-pre-coupling$",
    ):
        apply_pre_coupling_maintenance_control(source, seed, coupled)


def test_post_transition_state_cannot_mint_pre_coupling_receipt() -> None:
    source = _source()
    seed = source.seeds[0]
    state = initial_state(source, seed)
    transitioned, _ = transition(source, seed, state, TransitionKind.MAINTAIN)
    assert transitioned.boundary is state.boundary
    assert transitioned.maintenance_control is state.maintenance_control
    assert transitioned.phase == state.phase
    assert transitioned.retained_residue == state.retained_residue
    assert transitioned.maintenance_credit == state.maintenance_credit
    assert transitioned.transition_count == state.transition_count + 1
    with pytest.raises(
        ValueError,
        match="^p3og-maintenance-control-not-pre-coupling$",
    ):
        apply_pre_coupling_maintenance_control(source, seed, transitioned)


def test_existing_pressure_digest_remains_exact() -> None:
    report = run_p3og_pressure(_source())
    assert report.report_digest == (
        "6cb296c650deaf458649b0211546815490a46aa0ab8d7606362daea3fc38faf7"
    )


def test_existing_formation_pressure_binding_digest_remains_exact() -> None:
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="formation-pressure-source",
        seed_rows=(("alpha", (0, 1, 0)),),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=GOOD_SUFFIX,
    )
    formation = p3og_formation_source(source)
    evidence = run_p3og_first_closure(source, formation)
    report = run_p3og_pressure(source)
    binding = build_p3og_formation_pressure_binding(
        source,
        formation,
        evidence,
        report,
    )
    assert binding.binding_digest == (
        "6802d057df56caccd303a6bd3fe9fbd5ddf48f28e22f3a99831df560df92a2f6"
    )
