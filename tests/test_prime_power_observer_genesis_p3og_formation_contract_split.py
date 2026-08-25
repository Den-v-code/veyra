"""Pre-selection contract / post-selection binding split for native P3-OG formation."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass, autonomous_tick_rule, p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_formation_history import (
    p3og_formation_history_plan,
)
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    P3OGNativeFormationContract,
    p3og_native_formation_binding,
    p3og_native_formation_contract,
    p3og_native_formation_source,
    validate_legacy_source_against_contract_binding,
    validate_native_formation_binding,
    validate_native_formation_contract,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _fixture():
    source = p3og_source(
        prime=3, depth=1, source_instance_label="formation-contract-split",
        seed_rows=(("alpha", (0, 1, 0)),), calibration_inputs=(0, 1),
        maintenance_credit=2, suffix=(TransitionKind.IDLE,),
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
            TransitionKind.IDLE,
        ),
        autonomous_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.LOW,
            TransitionKind.IDLE,
        ),
    )
    autonomous = p3og_autonomous_tick_source(source, rules)
    contract = p3og_native_formation_contract(source, autonomous)
    binding = p3og_native_formation_binding(source, autonomous, contract)
    legacy = p3og_native_formation_source(source, autonomous)
    return source, autonomous, contract, binding, legacy


def test_contract_is_selection_free_and_exactly_matches_preselection_history_commit() -> None:
    source, autonomous, contract, binding, legacy = _fixture()
    assert type(contract) is P3OGNativeFormationContract
    names = {field.name for field in fields(contract)}
    assert "selection" not in names
    assert "selected_seed_digest" not in names
    assert "pressure_source_digest" not in names
    plan = p3og_formation_history_plan(source, autonomous)
    assert plan.formation_contract_digest == contract.contract_digest
    assert binding.contract_digest == contract.contract_digest
    assert binding.pressure_source_digest == source.source_digest
    assert binding.autonomous_source_digest == autonomous.source_digest
    assert binding.selection == legacy.selection
    assert binding.selected_seed_digest == legacy.selected_seed_digest
    validate_legacy_source_against_contract_binding(
        source, autonomous, contract, binding, legacy,
    )


def test_contract_and_binding_fail_closed_under_drift() -> None:
    source, autonomous, contract, binding, legacy = _fixture()
    with pytest.raises(ValueError):
        validate_native_formation_contract(
            source, autonomous, replace(contract, max_formation_ticks=125),
        )
    with pytest.raises(ValueError):
        validate_native_formation_binding(
            source, autonomous, contract, replace(
                binding, selected_seed_digest="0" * 64,
            ),
        )
    with pytest.raises(ValueError):
        validate_legacy_source_against_contract_binding(
            source,
            autonomous,
            replace(contract, contract_digest="1" * 64),
            binding,
            legacy,
        )


def test_hostile_binding_selection_is_rejected_before_codec_callback() -> None:
    source, autonomous, contract, binding, _ = _fixture()

    class HostileSelection(type(binding.selection)):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileSelection)
    forged = replace(binding, selection=hostile)
    with pytest.raises(ValueError):
        validate_native_formation_binding(source, autonomous, contract, forged)
