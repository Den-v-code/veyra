"""Focused/hostile tests for bounded P3-OG blind one-shot selection."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_one_shot_selection import (
    P3OGOneShotSelectionReceipt,
    SelectionCapabilityState,
    consume_p3og_selection_capability,
    p3og_initial_selection_capability,
    p3og_one_shot_selection_source,
    validate_p3og_one_shot_selection_receipt,
    validate_p3og_one_shot_selection_source,
    validate_p3og_selection_capability,
)


def _source(label: str = "one-shot"):
    return p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label,
        seed_rows=(
            ("alpha", (0, 1, 0)),
            ("beta", (0, 2, 0)),
            ("gamma", (0, 3, 0)),
        ),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=(TransitionKind.IDLE,),
    )


def _fixture(blind: str = "a" * 64):
    source = _source()
    selection_source = p3og_one_shot_selection_source(source, blind)
    available = p3og_initial_selection_capability(source, selection_source)
    return source, selection_source, available


def test_available_consumes_once_and_fresh_trace_validates() -> None:
    source, selection_source, available = _fixture()
    seed, consumed, receipt = consume_p3og_selection_capability(
        source,
        selection_source,
        available,
    )
    assert consumed.state is SelectionCapabilityState.CONSUMED
    assert source.seeds[receipt.selected_index] == seed
    assert receipt.selected_seed_label == seed.label
    assert receipt.selected_seed_digest == seed.seed_digest
    rebuilt_seed, rebuilt_consumed, rebuilt_receipt = (
        validate_p3og_one_shot_selection_receipt(
            source,
            selection_source,
            available,
            consumed,
            receipt,
        )
    )
    assert rebuilt_seed == seed
    assert rebuilt_consumed == consumed
    assert rebuilt_receipt == receipt


def test_returned_consumed_capability_cannot_be_retried() -> None:
    source, selection_source, available = _fixture()
    _, consumed, _ = consume_p3og_selection_capability(
        source,
        selection_source,
        available,
    )
    with pytest.raises(ValueError, match="capability-consumed"):
        consume_p3og_selection_capability(source, selection_source, consumed)


def test_tampered_available_restoration_is_rejected() -> None:
    source, selection_source, available = _fixture()
    _, consumed, _ = consume_p3og_selection_capability(
        source,
        selection_source,
        available,
    )
    forged = replace(consumed, state=SelectionCapabilityState.AVAILABLE)
    with pytest.raises(ValueError, match="capability-drift"):
        validate_p3og_selection_capability(source, selection_source, forged)


def test_foreign_pressure_source_cannot_reuse_selection_commitment() -> None:
    source, selection_source, _ = _fixture()
    foreign = _source("one-shot-foreign")
    assert foreign.source_digest != source.source_digest
    with pytest.raises(ValueError):
        validate_p3og_one_shot_selection_source(foreign, selection_source)


def test_blind_seed_drift_changes_commitment_and_rejects_splice() -> None:
    source, selection_source, available = _fixture()
    foreign_selection_source = p3og_one_shot_selection_source(source, "b" * 64)
    assert foreign_selection_source.source_digest != selection_source.source_digest
    with pytest.raises(ValueError):
        validate_p3og_selection_capability(
            source,
            foreign_selection_source,
            available,
        )


def test_selected_output_splice_fails_fresh_receipt_validation() -> None:
    source, selection_source, available = _fixture()
    _, consumed, receipt = consume_p3og_selection_capability(
        source,
        selection_source,
        available,
    )
    foreign_index = (receipt.selected_index + 1) % len(source.seeds)
    foreign_seed = source.seeds[foreign_index]
    forged = replace(
        receipt,
        selected_index=foreign_index,
        selected_seed_label=foreign_seed.label,
        selected_seed_digest=foreign_seed.seed_digest,
    )
    with pytest.raises(ValueError, match="receipt-drift"):
        validate_p3og_one_shot_selection_receipt(
            source,
            selection_source,
            available,
            consumed,
            forged,
        )


def test_source_schema_contains_no_outcome_or_future_fields() -> None:
    _, selection_source, _ = _fixture()
    names = {field.name for field in fields(selection_source)}
    forbidden = {
        "criterion",
        "later_result",
        "formation_status",
        "theorem_conclusion",
        "success",
        "retry",
        "selected_index",
        "selected_seed_digest",
        "selected_seed_label",
    }
    assert names.isdisjoint(forbidden)


def test_copied_available_replay_is_explicitly_deterministic_not_global_linear() -> None:
    source, selection_source, available = _fixture()
    first = consume_p3og_selection_capability(source, selection_source, available)
    second = consume_p3og_selection_capability(source, selection_source, available)
    assert first == second


def test_hostile_receipt_subclass_is_rejected_before_nested_access() -> None:
    source, selection_source, available = _fixture()
    _, consumed, _ = consume_p3og_selection_capability(
        source,
        selection_source,
        available,
    )

    class HostileReceipt(P3OGOneShotSelectionReceipt):
        def __getattribute__(self, name):
            if name != "__class__":
                raise AssertionError("hostile callback reached")
            return super().__getattribute__(name)

    hostile = object.__new__(HostileReceipt)
    with pytest.raises(ValueError, match="receipt-type"):
        validate_p3og_one_shot_selection_receipt(
            source,
            selection_source,
            available,
            consumed,
            hostile,
        )
