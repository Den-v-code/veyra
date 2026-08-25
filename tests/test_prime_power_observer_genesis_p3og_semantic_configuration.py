"""Focused and exhaustive-small tests for the P3-OG semantic configuration quotient."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_machine_internal import _state
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    P3OGSemanticConfiguration,
    SemanticOperationMode,
    p3og_semantic_configuration_contract,
    semantic_alive,
    semantic_boundary,
    semantic_configuration_from_native,
    semantic_couple,
    semantic_q_seed,
    semantic_read,
    semantic_residue,
    semantic_state_space_size,
    semantic_tick,
    validate_semantic_configuration,
    validate_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
)


def _fixture():
    source = p3og_source(
        prime=2,
        depth=0,
        source_instance_label="semantic-configuration",
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
            TransitionKind.MAINTAIN,
        ),
        autonomous_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.HIGH,
            TransitionKind.ADVANCE,
        ),
        autonomous_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.LOW,
            TransitionKind.IDLE,
        ),
    )
    autonomous = p3og_autonomous_tick_source(source, rules)
    contract = p3og_semantic_configuration_contract(source, autonomous)
    seed = source.seeds[0]
    return source, autonomous, contract, seed


def _all_configurations(source, seed):
    initial = semantic_q_seed(source, seed)
    for control in tuple(MaintenanceControlState):
        for phase in range(2):
            for credit in (1, 2):
                for retained in (None, 0, 1):
                    native = _state(
                        initial.run_id,
                        seed.seed_digest,
                        BoundaryState.ALIVE,
                        control,
                        phase,
                        retained,
                        credit,
                        17,
                    )
                    yield semantic_configuration_from_native(source, seed, native), native
        removed = _state(
            initial.run_id,
            seed.seed_digest,
            BoundaryState.REMOVED,
            control,
            0,
            None,
            0,
            17,
        )
        yield semantic_configuration_from_native(source, seed, removed), removed


def test_contract_is_selection_free_and_commits_exact_finite_operations() -> None:
    source, autonomous, contract, _ = _fixture()
    names = {field.name for field in fields(contract)}
    assert "selection" not in names
    assert "selected_seed_digest" not in names
    assert contract.pressure_source_digest == source.source_digest
    assert contract.autonomous_source_digest == autonomous.source_digest
    assert contract.max_input_bits == 4096
    assert contract.max_transition_count == 4096
    validate_semantic_configuration_contract(source, autonomous, contract)


def test_q_seed_and_total_read_residue_boundary_alive_are_native_projections() -> None:
    source, _, _, seed = _fixture()
    q0 = semantic_q_seed(source, seed)
    assert semantic_read(source, seed, q0) is None
    assert semantic_residue(source, seed, q0) is None
    assert semantic_boundary(source, seed, q0) is BoundaryState.ALIVE
    assert semantic_alive(source, seed, q0) is True


def test_live_coupling_matches_exact_native_response_formula() -> None:
    source, autonomous, contract, seed = _fixture()
    q0 = semantic_q_seed(source, seed)
    for input_value in range(-3, 5):
        after, receipt = semantic_couple(
            source, autonomous, contract, seed, q0, input_value,
        )
        assert receipt.mode is SemanticOperationMode.NATIVE_QUOTIENT
        assert receipt.native_receipt_digest is not None
        assert receipt.response == semantic_read(source, seed, after)
        assert semantic_residue(source, seed, after) == input_value % 2
        assert receipt.response == seed.cycle[(input_value % 2) % 2]


def test_live_tick_is_exact_operational_projection_for_every_small_configuration() -> None:
    source, autonomous, contract, seed = _fixture()
    for configuration, native in _all_configurations(source, seed):
        if configuration.boundary is BoundaryState.REMOVED:
            continue
        semantic_after, receipt = semantic_tick(
            source, autonomous, contract, seed, configuration,
        )
        native_after, native_receipt = autonomous_tick(
            source, autonomous, seed, native,
        )
        projected = semantic_configuration_from_native(source, seed, native_after)
        assert semantic_after == projected
        assert receipt.mode is SemanticOperationMode.NATIVE_QUOTIENT
        assert receipt.selected_kind is native_receipt.selected_kind


def test_removed_tick_is_absorbing_native_projection_and_coupling_is_explicit_totalization() -> None:
    source, autonomous, contract, seed = _fixture()
    removed = next(
        configuration
        for configuration, _ in _all_configurations(source, seed)
        if configuration.boundary is BoundaryState.REMOVED
    )
    ticked, tick_receipt = semantic_tick(
        source, autonomous, contract, seed, removed,
    )
    assert ticked == removed
    assert tick_receipt.mode is SemanticOperationMode.REMOVED_TOTALIZATION
    assert tick_receipt.native_receipt_digest

    coupled, coupling_receipt = semantic_couple(
        source, autonomous, contract, seed, removed, 1,
    )
    assert coupled == removed
    assert coupling_receipt.mode is SemanticOperationMode.REMOVED_TOTALIZATION
    assert coupling_receipt.native_receipt_digest is None
    assert coupling_receipt.response is None
    assert semantic_alive(source, seed, coupled) is False


def test_small_semantic_carrier_is_total_under_tick_couple_and_observers() -> None:
    source, autonomous, contract, seed = _fixture()
    configurations = tuple(_all_configurations(source, seed))
    assert len(configurations) == 26
    assert semantic_state_space_size(source, seed) == 26
    for configuration, _ in configurations:
        validate_semantic_configuration(source, seed, configuration)
        after_tick, _ = semantic_tick(
            source, autonomous, contract, seed, configuration,
        )
        validate_semantic_configuration(source, seed, after_tick)
        for input_value in (-1, 0, 1):
            after_couple, _ = semantic_couple(
                source, autonomous, contract, seed, configuration, input_value,
            )
            validate_semantic_configuration(source, seed, after_couple)
        semantic_read(source, seed, configuration)
        semantic_residue(source, seed, configuration)
        semantic_boundary(source, seed, configuration)
        semantic_alive(source, seed, configuration)


def test_contract_and_configuration_drift_fail_closed() -> None:
    source, autonomous, contract, seed = _fixture()
    with pytest.raises(ValueError):
        validate_semantic_configuration_contract(
            source, autonomous, replace(contract, max_input_bits=4095),
        )
    q0 = semantic_q_seed(source, seed)
    forged = replace(q0, maintenance_credit=1)
    with pytest.raises(ValueError):
        validate_semantic_configuration(source, seed, forged)


def test_semantic_configuration_outer_subclass_is_rejected() -> None:
    source, _, _, seed = _fixture()
    q0 = semantic_q_seed(source, seed)

    class HostileConfiguration(P3OGSemanticConfiguration):
        pass

    hostile = HostileConfiguration(*tuple(getattr(q0, field.name) for field in fields(q0)))
    with pytest.raises(ValueError, match="configuration-type"):
        validate_semantic_configuration(source, seed, hostile)
