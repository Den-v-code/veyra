"""Focused/hostile tests for the selection-free semantic intervention plan."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_autonomous_tick import (
    MaintenanceCreditClass,
    autonomous_tick_rule,
    p3og_autonomous_tick_source,
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
    P3OG_SEMANTIC_INTERVENTION_PLAN_NONCLAIMS,
    p3og_semantic_intervention_plan,
    validate_p3og_semantic_intervention_plan,
)
from src.core.prime_power_observer_genesis_p3og_semantic_intervention_plan_types import (
    P3OGSemanticContinuationSpec,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState


def _fixture(*, label: str = "semantic-intervention-plan"):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label,
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
    plan = p3og_semantic_intervention_plan(
        source,
        autonomous,
        semantic,
        bridge,
        ablation,
    )
    return source, autonomous, semantic, bridge, ablation, plan


def test_plan_commits_finite_catalog_cut_component_and_match_scope() -> None:
    fixture = _fixture()
    source, _, semantic, _, ablation, plan = fixture
    continuation = plan.continuation_catalog[0]
    cut = plan.comparison_cuts[0]

    assert len(plan.continuation_catalog) == 1
    assert continuation.steps == source.maintenance_credit == 2
    assert continuation.tick_rule_id == semantic.tick_rule_id
    assert cut.continuation_entry_id == continuation.entry_id
    assert cut.observation_input == 0
    assert plan.maintenance_component_id == ablation.component_id
    assert plan.semantic_scope_digest
    assert plan.max_continuations == 8
    assert plan.max_comparison_cuts == 8

    replay = validate_p3og_semantic_intervention_plan(*fixture)
    assert replay == plan
    assert replay is not plan


def test_plan_schema_is_selection_and_outcome_free() -> None:
    plan = _fixture()[-1]
    names = {field.name for field in fields(plan)}
    forbidden = {
        "selection",
        "selection_source_digest",
        "selection_receipt_digest",
        "selected_seed_digest",
        "formation_source_digest",
        "formation_evidence_digest",
        "criterion",
        "later_result",
        "status",
        "expected_status",
        "response",
    }
    assert names.isdisjoint(forbidden)
    assert plan.nonclaims == P3OG_SEMANTIC_INTERVENTION_PLAN_NONCLAIMS
    assert "standalone-plan-is-not-history-evidence" in plan.nonclaims
    assert "full-def-og-006-discharge" in plan.nonclaims
    assert "full-def-og-009-discharge" in plan.nonclaims
    assert "endogenous-observer-role" in plan.nonclaims


def test_foreign_source_contract_family_cannot_validate_plan() -> None:
    primary = _fixture(label="semantic-intervention-primary")
    foreign = _fixture(label="semantic-intervention-foreign")
    with pytest.raises(ValueError):
        validate_p3og_semantic_intervention_plan(
            foreign[0],
            foreign[1],
            foreign[2],
            foreign[3],
            foreign[4],
            primary[5],
        )


def test_tampered_continuation_catalog_fails_fresh_reconstruction() -> None:
    fixture = _fixture()
    plan = fixture[-1]
    continuation = replace(plan.continuation_catalog[0], steps=1)
    forged = replace(plan, continuation_catalog=(continuation,))
    with pytest.raises(ValueError):
        validate_p3og_semantic_intervention_plan(
            fixture[0],
            fixture[1],
            fixture[2],
            fixture[3],
            fixture[4],
            forged,
        )


def test_hostile_nested_continuation_is_rejected_before_codec_callback() -> None:
    fixture = _fixture()
    plan = fixture[-1]

    class HostileContinuation(P3OGSemanticContinuationSpec):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileContinuation)
    forged = replace(plan, continuation_catalog=(hostile,))
    with pytest.raises(ValueError, match="continuation-type"):
        validate_p3og_semantic_intervention_plan(
            fixture[0],
            fixture[1],
            fixture[2],
            fixture[3],
            fixture[4],
            forged,
        )
