"""Focused/hostile tests for semantic commitments in the blind history cut."""

from __future__ import annotations

from dataclasses import replace

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
    p3og_formation_history_precommitment,
    validate_formation_history_plan,
)
from src.core.prime_power_observer_genesis_p3og_formation_history_types import (
    FormationHistoryPrecommitment,
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
from src.core.prime_power_observer_genesis_p3og_semantic_ablation import (
    p3og_semantic_ablation_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    p3og_semantic_configuration_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_formation_bridge import (
    p3og_semantic_formation_bridge_contract,
)
from src.core.prime_power_observer_genesis_p3og_semantic_intervention_plan import (
    p3og_semantic_intervention_plan,
)
from src.core.prime_power_observer_genesis_p3og_semantic_preselection_history import (
    P3OG_SEMANTIC_PRESELECTION_HISTORY_NONCLAIMS,
    p3og_semantic_preselection_history_plan,
    semantic_preselection_commitments,
    validate_p3og_semantic_preselection_commitments,
    validate_p3og_semantic_preselection_history_plan,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
)


def _fixture():
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="semantic-preselection-history",
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
            TransitionKind.IDLE,
        ),
        autonomous_tick_rule(
            MaintenanceControlState.DISABLED,
            MaintenanceCreditClass.LOW,
            TransitionKind.IDLE,
        ),
    )
    autonomous = p3og_autonomous_tick_source(source, rules)
    semantic = p3og_semantic_configuration_contract(source, autonomous)
    bridge = p3og_semantic_formation_bridge_contract(
        source,
        autonomous,
        semantic,
    )
    ablation = p3og_semantic_ablation_contract(
        source,
        autonomous,
        semantic,
    )
    intervention = p3og_semantic_intervention_plan(
        source,
        autonomous,
        semantic,
        bridge,
        ablation,
    )
    selection_source = p3og_one_shot_selection_source(source, "f" * 64)
    available = p3og_initial_selection_capability(source, selection_source)
    plan = p3og_semantic_preselection_history_plan(
        source,
        autonomous,
        semantic,
        bridge,
        ablation,
        intervention,
        selection_source,
        available,
    )
    return (
        source,
        autonomous,
        semantic,
        bridge,
        ablation,
        intervention,
        selection_source,
        available,
        plan,
    )


def test_exact_four_semantic_commitments_are_canonical() -> None:
    fixture = _fixture()
    commitments = semantic_preselection_commitments(*fixture[:6])
    assert tuple(item.commitment_id for item in commitments) == (
        "semantic-configuration-contract",
        "semantic-formation-bridge-contract",
        "semantic-ablation-contract",
        "semantic-intervention-plan",
    )
    assert tuple(item.payload_digest for item in commitments) == (
        fixture[2].contract_digest,
        fixture[3].contract_digest,
        fixture[4].contract_digest,
        fixture[5].plan_digest,
    )
    assert "full-def-og-009-discharge" in (
        P3OG_SEMANTIC_PRESELECTION_HISTORY_NONCLAIMS
    )


def test_semantic_commitments_are_strict_past_not_selection_sources() -> None:
    fixture = _fixture()
    (
        source,
        autonomous,
        _,
        _,
        _,
        _,
        selection_source,
        available,
        plan,
    ) = fixture
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
    formation = run_p3og_native_formation(
        source,
        autonomous,
        formation_source,
    )
    evidence = build_p3og_formation_history_evidence(
        source,
        autonomous,
        plan,
        formation_source,
        formation,
        "a" * 64,
        "b" * 64,
    )
    semantic_ids = {
        "semantic-configuration-contract",
        "semantic-formation-bridge-contract",
        "semantic-ablation-contract",
        "semantic-intervention-plan",
    }
    assert semantic_ids.issubset(evidence.strict_past_event_ids)
    table = {event.event_id: event for event in evidence.events}
    selection_sources = set(
        table["selection-consume"].source_closure.transitive_source_event_ids
    )
    assert semantic_ids.isdisjoint(selection_sources)
    history_plan_sources = set(
        table["history-plan"].source_closure.transitive_source_event_ids
    )
    assert semantic_ids.issubset(history_plan_sources)


def test_generic_valid_wrong_policy_fails_specialized_validator() -> None:
    fixture = _fixture()
    (
        source,
        autonomous,
        semantic,
        bridge,
        ablation,
        intervention,
        selection_source,
        available,
        _,
    ) = fixture
    wrong = p3og_formation_history_precommitment(
        "foreign-preselection-policy",
        "e" * 64,
        ("source", "autonomous-law"),
    )
    generic = p3og_formation_history_plan(
        source,
        autonomous,
        selection_source,
        available,
        (wrong,),
    )
    validate_formation_history_plan(
        source,
        autonomous,
        selection_source,
        available,
        generic,
    )
    with pytest.raises(ValueError, match="commitments-drift"):
        validate_p3og_semantic_preselection_history_plan(
            source,
            autonomous,
            semantic,
            bridge,
            ablation,
            intervention,
            selection_source,
            available,
            generic,
        )


def test_spliced_semantic_payload_fails_specialized_validator() -> None:
    fixture = _fixture()
    commitments = list(fixture[-1].preselection_commitments)
    commitments[-1] = p3og_formation_history_precommitment(
        "semantic-intervention-plan",
        "e" * 64,
        commitments[-1].direct_source_event_ids,
    )
    generic = p3og_formation_history_plan(
        fixture[0],
        fixture[1],
        fixture[6],
        fixture[7],
        tuple(commitments),
    )
    validate_formation_history_plan(
        fixture[0],
        fixture[1],
        fixture[6],
        fixture[7],
        generic,
    )
    with pytest.raises(ValueError, match="commitments-drift"):
        validate_p3og_semantic_preselection_history_plan(
            *fixture[:-1],
            generic,
        )


def test_hostile_nested_commitment_rejected_before_codec_callback() -> None:
    fixture = _fixture()

    class HostileCommitment(FormationHistoryPrecommitment):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileCommitment)
    with pytest.raises(ValueError, match="commitments-shape"):
        validate_p3og_semantic_preselection_commitments(
            *fixture[:6],
            (hostile,),
        )
