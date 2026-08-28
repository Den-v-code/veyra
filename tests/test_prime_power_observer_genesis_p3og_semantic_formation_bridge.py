"""Focused/hostile tests for the current one-shot P3-OG semantic-formation bridge."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
)
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    NativeFormationStatus,
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_one_shot_selection import (
    consume_p3og_selection_capability,
    p3og_initial_selection_capability,
    p3og_one_shot_selection_source,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    P3OG_SEMANTIC_FORMATION_BRIDGE_NONCLAIMS,
    SemanticFormationBridgeStatus,
    build_p3og_semantic_formation_bridge_evidence,
    p3og_semantic_formation_bridge_contract,
    validate_p3og_semantic_formation_bridge_evidence,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    SemanticFormationBridgeStep,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _fixture(
    *,
    low: TransitionKind = TransitionKind.MAINTAIN,
    label: str | None = None,
):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label or f"semantic-formation-bridge-{low.value}",
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
    semantic_contract = p3og_semantic_configuration_contract(source, autonomous)
    bridge_contract = p3og_semantic_formation_bridge_contract(
        source,
        autonomous,
        semantic_contract,
    )
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
    return (
        source,
        autonomous,
        semantic_contract,
        bridge_contract,
        formation_source,
        formation,
    )


def _build(fixture):
    return build_p3og_semantic_formation_bridge_evidence(*fixture)


def test_witnessed_one_shot_formation_is_exact_first_return_in_q_sem() -> None:
    fixture = _fixture()
    formation_source = fixture[-2]
    formation = fixture[-1]
    evidence = _build(fixture)

    assert formation.status is NativeFormationStatus.WITNESSED
    assert evidence.status is SemanticFormationBridgeStatus.WITNESSED
    assert evidence.departure_step == 1
    assert evidence.first_closure_step == formation.first_closure_step == 2
    assert evidence.final_configuration == evidence.q_seed
    assert tuple(step.semantic_tick.selected_kind for step in evidence.steps) == (
        TransitionKind.IDLE,
        TransitionKind.MAINTAIN,
    )
    assert tuple(step.closed_after for step in evidence.steps) == (False, True)
    assert tuple(step.departed_after for step in evidence.steps) == (True, True)
    assert evidence.selection_source_digest == (
        formation_source.selection_source.source_digest
    )
    assert evidence.selection_receipt_digest == formation_source.selection.receipt_digest
    assert evidence.selected_seed_digest == formation_source.selected_seed_digest
    assert evidence.promotions == 0
    assert "standalone-bridge-is-not-history-evidence" in evidence.nonclaims
    assert "full-def-og-009-discharge" in evidence.nonclaims


def test_bridge_contract_is_selection_free_and_binds_current_formation_rules() -> None:
    fixture = _fixture()
    semantic_contract = fixture[2]
    bridge_contract = fixture[3]

    names = {field.name for field in fields(bridge_contract)}
    assert "selection" not in names
    assert "selection_source_digest" not in names
    assert "selection_receipt_digest" not in names
    assert "selected_seed_digest" not in names
    assert "formation_source_digest" not in names
    assert bridge_contract.semantic_configuration_contract_digest == (
        semantic_contract.contract_digest
    )
    assert bridge_contract.native_formation_source_version == (
        "p3og-native-formation-source-v3"
    )
    assert bridge_contract.max_formation_ticks == 126
    assert "strict-past-selection-commitment-not-reestablished-by-bridge" in (
        P3OG_SEMANTIC_FORMATION_BRIDGE_NONCLAIMS
    )


def test_refuted_native_formation_cannot_mint_positive_bridge() -> None:
    fixture = _fixture(low=TransitionKind.IDLE)
    assert fixture[-1].status is NativeFormationStatus.REFUTED
    with pytest.raises(ValueError, match="requires-witnessed-formation"):
        _build(fixture)


def test_tampered_bridge_step_fails_fresh_replay() -> None:
    fixture = _fixture()
    evidence = _build(fixture)
    first = replace(
        evidence.steps[0],
        after_configuration_digest="0" * 64,
    )
    forged = replace(evidence, steps=(first, *evidence.steps[1:]))

    with pytest.raises(ValueError):
        validate_p3og_semantic_formation_bridge_evidence(
            *fixture,
            forged,
        )


def test_foreign_one_shot_formation_source_cannot_splice_into_bridge() -> None:
    fixture = _fixture(label="semantic-bridge-primary")
    evidence = _build(fixture)
    foreign = _fixture(label="semantic-bridge-foreign")

    with pytest.raises(ValueError):
        validate_p3og_semantic_formation_bridge_evidence(
            fixture[0],
            fixture[1],
            fixture[2],
            fixture[3],
            foreign[4],
            foreign[5],
            evidence,
        )


def test_hostile_nested_step_is_rejected_before_codec_callback() -> None:
    fixture = _fixture()
    evidence = _build(fixture)

    class HostileStep(SemanticFormationBridgeStep):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileStep)
    forged = replace(evidence, steps=(hostile,))

    with pytest.raises(ValueError):
        validate_p3og_semantic_formation_bridge_evidence(
            *fixture,
            forged,
        )
