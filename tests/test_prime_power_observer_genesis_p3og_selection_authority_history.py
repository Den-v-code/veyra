"""POSIX hostile tests for P3-OG local-authority to typed-history binding."""

from dataclasses import fields, replace
from pathlib import Path

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
)
from src.core.prime_power_observer_genesis_p3og_formation_history_types import (
    FormationHistoryStatus,
)
from src.core.prime_power_observer_genesis_p3og_native_formation import (
    p3og_native_formation_source,
    run_p3og_native_formation,
)
from src.core.prime_power_observer_genesis_p3og_one_shot_selection import (
    consume_p3og_selection_capability_locally,
    p3og_initial_selection_capability,
    p3og_one_shot_selection_source,
    reserve_p3og_selection_local_authority,
)
from src.core.prime_power_observer_genesis_p3og_selection_authority_history import (
    P3OG_SELECTION_AUTHORITY_HISTORY_BOUNDARY,
    P3OG_SELECTION_AUTHORITY_HISTORY_NONCLAIMS,
    build_p3og_selection_authority_history_binding,
    consume_p3og_selection_for_authority_history_plan,
    p3og_selection_authority_history_plan,
    validate_p3og_selection_authority_history_binding,
)
from src.core.prime_power_observer_genesis_p3og_selection_authority_history_types import (
    P3OGSelectionAuthorityHistoryBinding,
    P3OGSelectionAuthorityHistoryPlan,
)
from src.core.prime_power_observer_genesis_p3og_selection_local_authority import (
    p3og_selection_local_authority_attempt_digest,
)
from src.core.prime_power_observer_genesis_p3og_selection_local_authority_types import (
    P3OGSelectionLocalAuthorityState,
)
from src.core.prime_power_observer_genesis_p3og_types import MaintenanceControlState

pytestmark = pytest.mark.requires_posix_file_locks


def _secure(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def _prefix(
    tmp_path: Path,
    *,
    name: str = "authority-history",
    reservation_id: str = "selection-1",
    low: TransitionKind = TransitionKind.MAINTAIN,
):
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=name,
        seed_rows=(("alpha", (0, 1, 0)),),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=(TransitionKind.IDLE,),
    )
    rules = (
        autonomous_tick_rule(MaintenanceControlState.ACTIVE, MaintenanceCreditClass.HIGH, TransitionKind.IDLE),
        autonomous_tick_rule(MaintenanceControlState.ACTIVE, MaintenanceCreditClass.LOW, low),
        autonomous_tick_rule(MaintenanceControlState.DISABLED, MaintenanceCreditClass.HIGH, TransitionKind.IDLE),
        autonomous_tick_rule(MaintenanceControlState.DISABLED, MaintenanceCreditClass.LOW, TransitionKind.IDLE),
    )
    autonomous = p3og_autonomous_tick_source(source, rules)
    selection_source = p3og_one_shot_selection_source(source, "f" * 64)
    available = p3og_initial_selection_capability(source, selection_source)
    history_plan = p3og_formation_history_plan(source, autonomous, selection_source, available)
    directory = _secure(tmp_path / reservation_id)
    secret = (reservation_id.encode("utf-8") + b"x" * 64)[:32]
    reserved = reserve_p3og_selection_local_authority(
        directory,
        source,
        selection_source,
        available,
        reservation_id,
        secret,
    )
    authority_plan = p3og_selection_authority_history_plan(
        directory,
        source,
        autonomous,
        history_plan,
        selection_source,
        available,
        reserved,
    )
    return source, autonomous, selection_source, available, history_plan, directory, secret, reserved, authority_plan


def _finish(prefix, *, direct_attempt: str | None = None):
    source, autonomous, selection_source, available, history_plan, directory, secret, reserved, authority_plan = prefix
    if direct_attempt is None:
        _seed, consumed, selection, authority = consume_p3og_selection_for_authority_history_plan(
            directory,
            source,
            autonomous,
            history_plan,
            selection_source,
            available,
            reserved,
            authority_plan,
            secret,
        )
    else:
        _seed, consumed, selection, authority = consume_p3og_selection_capability_locally(
            directory,
            source,
            selection_source,
            available,
            reserved.reservation.reservation_id,
            secret,
            direct_attempt,
        )
    formation_source = p3og_native_formation_source(
        source,
        autonomous,
        selection_source,
        available,
        consumed,
        selection,
    )
    formation = run_p3og_native_formation(source, autonomous, formation_source)
    criterion = "a" * 64 if formation.status.value.startswith("witnessed") else None
    later = "b" * 64 if criterion is not None else None
    history = build_p3og_formation_history_evidence(
        source,
        autonomous,
        history_plan,
        formation_source,
        formation,
        criterion,
        later,
    )
    return (*prefix, formation_source, formation, criterion, later, history, authority)


def _case(tmp_path: Path, *, low: TransitionKind = TransitionKind.MAINTAIN):
    prefix = _prefix(tmp_path, low=low)
    artifacts = _finish(prefix)
    source, autonomous, _ss, _available, history_plan, directory, _secret, _reserved, authority_plan, formation_source, formation, criterion, later, history, authority = artifacts
    binding = build_p3og_selection_authority_history_binding(
        directory,
        source,
        autonomous,
        history_plan,
        authority_plan,
        formation_source,
        formation,
        criterion,
        later,
        history,
        authority,
    )
    return (*artifacts, binding)


def test_preselection_plan_and_final_binding_share_one_exact_local_consume(tmp_path: Path) -> None:
    artifacts = _case(tmp_path)
    source, autonomous, _ss, _available, history_plan, directory, _secret, reserved, authority_plan, formation_source, formation, criterion, later, history, authority, binding = artifacts
    assert authority.claimed.attempt_digest == p3og_selection_local_authority_attempt_digest(
        reserved.receipt_digest,
        authority_plan.plan_digest,
    )
    assert binding.authority_history_plan_digest == authority_plan.plan_digest
    assert binding.formation_history_plan_digest == history_plan.plan_digest
    assert binding.formation_history_evidence_digest == history.evidence_digest
    assert binding.selection_receipt_digest == formation_source.selection.receipt_digest
    assert binding.authority_terminal_receipt_digest == authority.terminal.receipt_digest
    assert binding.authority_attempt_digest == authority.claimed.attempt_digest
    assert binding.promotions == 0
    assert binding.nonclaims == P3OG_SELECTION_AUTHORITY_HISTORY_NONCLAIMS
    assert binding.boundary == P3OG_SELECTION_AUTHORITY_HISTORY_BOUNDARY
    replay = validate_p3og_selection_authority_history_binding(
        directory,
        source,
        autonomous,
        history_plan,
        authority_plan,
        formation_source,
        formation,
        criterion,
        later,
        history,
        authority,
        binding,
    )
    assert replay == binding
    assert replay is not binding


def test_plan_is_outcome_free_and_cannot_be_built_after_same_store_is_consumed(tmp_path: Path) -> None:
    artifacts = _case(tmp_path)
    source, autonomous, selection_source, available, history_plan, directory, _secret, reserved, _authority_plan, *_rest = artifacts
    names = {field.name for field in fields(P3OGSelectionAuthorityHistoryPlan)}
    assert {"selected_seed_digest", "selection_receipt_digest", "criterion", "later_result"}.isdisjoint(names)
    with pytest.raises(ValueError, match="store-not-reserved"):
        p3og_selection_authority_history_plan(
            directory,
            source,
            autonomous,
            history_plan,
            selection_source,
            available,
            reserved,
        )


def test_wrong_attempt_id_cannot_be_relabelled_as_plan_backed_history(tmp_path: Path) -> None:
    prefix = _prefix(tmp_path)
    artifacts = _finish(prefix, direct_attempt="wrong-attempt")
    source, autonomous, _ss, _available, history_plan, directory, _secret, _reserved, authority_plan, formation_source, formation, criterion, later, history, authority = artifacts
    assert authority.terminal.state is P3OGSelectionLocalAuthorityState.CONSUMED
    with pytest.raises(ValueError, match="attempt-drift"):
        build_p3og_selection_authority_history_binding(
            directory,
            source,
            autonomous,
            history_plan,
            authority_plan,
            formation_source,
            formation,
            criterion,
            later,
            history,
            authority,
        )


def test_foreign_reservation_cannot_be_spliced_into_precommitted_plan(tmp_path: Path) -> None:
    prefix_a = _prefix(tmp_path, name="same-source", reservation_id="selection-a")
    source, autonomous, selection_source, available, history_plan, _dir_a, _secret_a, _reserved_a, plan_a = prefix_a
    directory_b = _secure(tmp_path / "selection-b")
    secret_b = b"b" * 32
    reserved_b = reserve_p3og_selection_local_authority(
        directory_b,
        source,
        selection_source,
        available,
        "selection-b",
        secret_b,
    )
    _seed, consumed, selection, authority_b = consume_p3og_selection_capability_locally(
        directory_b,
        source,
        selection_source,
        available,
        "selection-b",
        secret_b,
        plan_a.plan_digest,
    )
    formation_source = p3og_native_formation_source(source, autonomous, selection_source, available, consumed, selection)
    formation = run_p3og_native_formation(source, autonomous, formation_source)
    history = build_p3og_formation_history_evidence(source, autonomous, history_plan, formation_source, formation, "a" * 64, "b" * 64)
    assert reserved_b.receipt_digest != plan_a.authority_reserved_receipt_digest
    with pytest.raises(ValueError, match="plan-(?:malformed|drift)|reservation-drift"):
        build_p3og_selection_authority_history_binding(
            directory_b,
            source,
            autonomous,
            history_plan,
            plan_a,
            formation_source,
            formation,
            "a" * 64,
            "b" * 64,
            history,
            authority_b,
        )


def test_binding_field_splice_fails_fresh_store_and_history_replay(tmp_path: Path) -> None:
    artifacts = _case(tmp_path)
    source, autonomous, _ss, _available, history_plan, directory, _secret, _reserved, authority_plan, formation_source, formation, criterion, later, history, authority, binding = artifacts
    forged = replace(binding, selection_receipt_digest="0" * 64)
    with pytest.raises(ValueError, match="binding-drift"):
        validate_p3og_selection_authority_history_binding(
            directory,
            source,
            autonomous,
            history_plan,
            authority_plan,
            formation_source,
            formation,
            criterion,
            later,
            history,
            authority,
            forged,
        )
    names = {field.name for field in fields(P3OGSelectionAuthorityHistoryBinding)}
    assert {"observer_role", "historical_token_id", "hap_witness", "actualized"}.isdisjoint(names)
    assert "full-def-og-002-discharge" in binding.nonclaims
    assert "cross-store-or-process-global-uniqueness" in binding.nonclaims
    assert "historical-actualization" in binding.nonclaims


def test_refuted_selection_remains_authority_consumed_and_has_no_future_seals(tmp_path: Path) -> None:
    artifacts = _case(tmp_path, low=TransitionKind.IDLE)
    (
        _source,
        _autonomous,
        _selection_source,
        _available,
        _history_plan,
        _directory,
        _secret,
        _reserved,
        _authority_plan,
        formation_source,
        formation,
        criterion,
        later,
        history,
        authority,
        binding,
    ) = artifacts
    assert formation.status.value.startswith("refuted")
    assert criterion is None
    assert later is None
    assert history.status is FormationHistoryStatus.REFUTED
    assert history.future_event_ids == ()
    assert authority.terminal.state is P3OGSelectionLocalAuthorityState.CONSUMED
    assert authority.selection_receipt_digest == formation_source.selection.receipt_digest
    assert binding.selection_receipt_digest == formation_source.selection.receipt_digest
    assert binding.promotions == 0
