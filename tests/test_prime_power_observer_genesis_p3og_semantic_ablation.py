"""Focused tests for selection-free P3-OG semantic maintenance ablation."""

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
    P3OGSemanticAblationContract,
    P3OG_SEMANTIC_ABLATION_NONCLAIMS,
    SemanticAblationReceipt,
    p3og_semantic_ablation_contract,
    validate_semantic_ablation_contract,
    semantic_ablate_maintenance,
    validate_semantic_ablation_result,
)
from src.core.prime_power_observer_genesis_p3og_semantic_configuration import (
    p3og_semantic_configuration_contract,
    semantic_couple,
    semantic_q_seed,
    semantic_tick,
)
from src.core.prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
)


def _fixture(*, low=TransitionKind.MAINTAIN, label="semantic-ablation"):
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
    ablation_contract = p3og_semantic_ablation_contract(
        source,
        autonomous,
        semantic_contract,
    )
    seed = source.seeds[0]
    return source, autonomous, semantic_contract, ablation_contract, seed


def test_ablation_contract_is_selection_free_and_names_exact_component() -> None:
    _, _, semantic_contract, ablation_contract, _ = _fixture()
    names = {field.name for field in fields(ablation_contract)}

    assert "selection" not in names
    assert "selected_seed_digest" not in names
    assert ablation_contract.semantic_configuration_contract_digest == semantic_contract.contract_digest
    assert ablation_contract.component_id == "maintenance-control-v1"
    assert ablation_contract.unchanged_fields == (
        "run_id",
        "seed_digest",
        "boundary",
        "phase",
        "retained_residue",
        "maintenance_credit",
    )
    assert "standalone-ablation-is-not-history-evidence" in P3OG_SEMANTIC_ABLATION_NONCLAIMS
    assert "post-formation-chronology-without-history" in P3OG_SEMANTIC_ABLATION_NONCLAIMS
    assert "matched-control-history" in P3OG_SEMANTIC_ABLATION_NONCLAIMS
    assert "full-def-og-009-discharge" in P3OG_SEMANTIC_ABLATION_NONCLAIMS
    assert "endogenous-observer-role" in P3OG_SEMANTIC_ABLATION_NONCLAIMS


def test_ablation_changes_only_maintenance_control() -> None:
    source, autonomous, semantic_contract, ablation_contract, seed = _fixture()
    before = semantic_q_seed(source, seed)
    after, receipt = semantic_ablate_maintenance(
        source,
        autonomous,
        semantic_contract,
        ablation_contract,
        seed,
        before,
    )

    assert before.maintenance_control is MaintenanceControlState.ACTIVE
    assert after.maintenance_control is MaintenanceControlState.DISABLED
    assert after.run_id == before.run_id
    assert after.seed_digest == before.seed_digest
    assert after.boundary is before.boundary
    assert after.phase == before.phase
    assert after.retained_residue == before.retained_residue
    assert after.maintenance_credit == before.maintenance_credit
    assert receipt.read_before is None
    assert receipt.read_after is None
    assert receipt.component_id == ablation_contract.component_id


def test_ablation_preserves_current_read_after_real_semantic_coupling() -> None:
    source, autonomous, semantic_contract, ablation_contract, seed = _fixture()
    q_seed = semantic_q_seed(source, seed)
    coupled, coupling = semantic_couple(
        source,
        autonomous,
        semantic_contract,
        seed,
        q_seed,
        1,
    )
    after, receipt = semantic_ablate_maintenance(
        source,
        autonomous,
        semantic_contract,
        ablation_contract,
        seed,
        coupled,
    )

    assert coupling.response == 1
    assert receipt.read_before == coupling.response
    assert receipt.read_after == coupling.response
    assert after.retained_residue == coupled.retained_residue
    assert after.phase == coupled.phase


def test_repeated_or_removed_ablation_is_rejected() -> None:
    source, autonomous, semantic_contract, ablation_contract, seed = _fixture()
    before = semantic_q_seed(source, seed)
    disabled, _ = semantic_ablate_maintenance(
        source,
        autonomous,
        semantic_contract,
        ablation_contract,
        seed,
        before,
    )
    with pytest.raises(ValueError, match="requires-active-component"):
        semantic_ablate_maintenance(
            source,
            autonomous,
            semantic_contract,
            ablation_contract,
            seed,
            disabled,
        )

    source2, autonomous2, semantic_contract2, ablation_contract2, seed2 = _fixture(
        low=TransitionKind.IDLE,
        label="semantic-ablation-removed",
    )
    state = semantic_q_seed(source2, seed2)
    state, _ = semantic_tick(source2, autonomous2, semantic_contract2, seed2, state)
    state, _ = semantic_tick(source2, autonomous2, semantic_contract2, seed2, state)
    assert state.boundary is BoundaryState.REMOVED
    with pytest.raises(ValueError, match="requires-live-boundary"):
        semantic_ablate_maintenance(
            source2,
            autonomous2,
            semantic_contract2,
            ablation_contract2,
            seed2,
            state,
        )


def test_tampered_ablation_receipt_fails_fresh_replay() -> None:
    source, autonomous, semantic_contract, ablation_contract, seed = _fixture()
    before = semantic_q_seed(source, seed)
    after, receipt = semantic_ablate_maintenance(
        source,
        autonomous,
        semantic_contract,
        ablation_contract,
        seed,
        before,
    )
    forged = replace(receipt, after_configuration_digest="0" * 64)

    with pytest.raises(ValueError):
        validate_semantic_ablation_result(
            source,
            autonomous,
            semantic_contract,
            ablation_contract,
            seed,
            before,
            after,
            forged,
        )


def test_foreign_ablation_contract_and_contract_subclass_fail_closed() -> None:
    source, autonomous, semantic_contract, ablation_contract, _ = _fixture()
    source2, autonomous2, semantic_contract2, _, _ = _fixture(
        label="semantic-ablation-foreign",
    )
    with pytest.raises(ValueError):
        validate_semantic_ablation_contract(
            source2,
            autonomous2,
            semantic_contract2,
            ablation_contract,
        )

    class HostileContract(P3OGSemanticAblationContract):
        pass

    hostile = HostileContract(
        *tuple(getattr(ablation_contract, field.name) for field in fields(ablation_contract))
    )
    with pytest.raises(ValueError, match="contract-type"):
        validate_semantic_ablation_contract(
            source,
            autonomous,
            semantic_contract,
            hostile,
        )


def test_hostile_ablation_receipt_subclass_is_rejected_before_replay() -> None:
    source, autonomous, semantic_contract, ablation_contract, seed = _fixture()
    before = semantic_q_seed(source, seed)
    after, receipt = semantic_ablate_maintenance(
        source,
        autonomous,
        semantic_contract,
        ablation_contract,
        seed,
        before,
    )

    class HostileReceipt(SemanticAblationReceipt):
        pass

    hostile = HostileReceipt(
        *tuple(getattr(receipt, field.name) for field in fields(receipt))
    )
    with pytest.raises(ValueError, match="receipt-type"):
        validate_semantic_ablation_result(
            source,
            autonomous,
            semantic_contract,
            ablation_contract,
            seed,
            before,
            after,
            hostile,
        )
