"""Focused tests for P3-N2-derived P3-OG arithmetic input provenance."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

import src.core as root_core
from src.core.padic_completion_doctrine import padic_tower_doctrine
from src.core.padic_completion_prime import prime_source
from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_arithmetic_input import (
    P3OGArithmeticInputSource,
    P3OG_ARITHMETIC_INPUT_NONCLAIMS,
    p3og_arithmetic_input_source,
    validate_p3og_arithmetic_input_source,
)
from src.core.prime_power_observer_genesis_p3og_arithmetic_input_codec import (
    arithmetic_input_digest,
)
from src.core.prime_power_observer_genesis_p3og_codec import digest as pressure_digest
from src.core.prime_power_reduction_network_sources import finite_reduction_source


def _source(*, prime=3, depth=1, label="p3og-arithmetic-input"):
    return p3og_source(
        prime=prime,
        depth=depth,
        source_instance_label=label,
        seed_rows=(("alpha", (0, 1, 0)),),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=(TransitionKind.IDLE,),
    )


def test_exact_f0_f1_families_are_derived_from_existing_p3n2_source() -> None:
    source = _source()
    arithmetic = p3og_arithmetic_input_source(source)

    prime = prime_source(source.prime)
    doctrine = padic_tower_doctrine()
    finite = finite_reduction_source(
        prime,
        doctrine,
        depths=(source.depth,),
        family_integers=(0, 1),
    )
    by_integer = {family.integer: family for family in finite.families}
    left = by_integer[0]
    right = by_integer[1]

    assert arithmetic.prime_value == source.prime == 3
    assert arithmetic.depth == source.depth == 1
    assert arithmetic.modulus == 9
    assert arithmetic.left_input == arithmetic.left_residue == 0
    assert arithmetic.right_input == arithmetic.right_residue == 1
    assert arithmetic.p3n2_prime_source_digest == prime.source_digest
    assert arithmetic.p3n2_doctrine_digest == doctrine.doctrine_digest
    assert arithmetic.p3n2_finite_source_digest == finite.source_digest
    assert arithmetic.p3n2_network_digest == finite.p3t_raw_source.network_digest
    assert arithmetic.left_family_digest == left.family_digest
    assert arithmetic.right_family_digest == right.family_digest
    assert arithmetic.left_coordinate_digest == left.coordinates[0].coordinate_digest
    assert arithmetic.right_coordinate_digest == right.coordinates[0].coordinate_digest


def test_source_is_selection_free_and_contains_no_outcome_or_role_fields() -> None:
    arithmetic = p3og_arithmetic_input_source(_source())
    names = {field.name for field in fields(P3OGArithmeticInputSource)}
    assert {
        "selection",
        "selected_seed_digest",
        "candidate_id",
        "status",
        "expected_status",
        "observer_role",
        "historical_token_id",
        "birth_core_digest",
    }.isdisjoint(names)
    assert arithmetic.left_input != arithmetic.right_input
    assert arithmetic.left_residue != arithmetic.right_residue


def test_validation_freshly_reconstructs_complete_p3n2_provenance() -> None:
    source = _source()
    arithmetic = p3og_arithmetic_input_source(source)
    rebuilt_source, replay = validate_p3og_arithmetic_input_source(source, arithmetic)
    assert rebuilt_source == source
    assert replay == arithmetic
    assert replay is not arithmetic

    with pytest.raises(ValueError):
        validate_p3og_arithmetic_input_source(
            source,
            replace(arithmetic, right_coordinate_digest="f" * 64),
        )


def test_foreign_pressure_source_cannot_reuse_arithmetic_source() -> None:
    source = _source()
    arithmetic = p3og_arithmetic_input_source(source)
    foreign = _source(label="p3og-arithmetic-input-foreign")
    with pytest.raises(ValueError):
        validate_p3og_arithmetic_input_source(foreign, arithmetic)


def test_prime_outside_pomega2_envelope_fails_closed() -> None:
    source = _source(prime=65537, depth=0, label="p3og-arithmetic-input-large-prime")
    with pytest.raises(
        ValueError,
        match="p3og-arithmetic-input-prime-outside-p3n2-envelope",
    ):
        p3og_arithmetic_input_source(source)


def test_p3n2_finite_table_envelope_is_a_real_stop_condition() -> None:
    source = _source(prime=101, depth=2, label="p3og-arithmetic-input-large-table")
    with pytest.raises(
        ValueError,
        match="p3og-arithmetic-input-p3n2-resource-envelope",
    ):
        p3og_arithmetic_input_source(source)


def test_arithmetic_source_identity_changes_with_prime_or_depth() -> None:
    base = p3og_arithmetic_input_source(_source())
    other_prime = p3og_arithmetic_input_source(
        _source(prime=5, depth=1, label="p3og-arithmetic-input-p5"),
    )
    other_depth = p3og_arithmetic_input_source(
        _source(prime=3, depth=2, label="p3og-arithmetic-input-d2"),
    )
    assert len({base.source_digest, other_prime.source_digest, other_depth.source_digest}) == 3
    assert base.p3n2_finite_source_digest != other_prime.p3n2_finite_source_digest
    assert base.p3n2_finite_source_digest != other_depth.p3n2_finite_source_digest


def test_digest_domain_is_isolated_and_claim_boundary_stays_narrow() -> None:
    values = ("same", 0, 1)
    assert arithmetic_input_digest("arithmetic-input-source", *values) != pressure_digest(
        "arithmetic-input-source",
        *values,
    )
    assert {
        "p3n2-theorem-judgment",
        "p3t-observer-network-judgment",
        "semantic-coupling-execution",
        "retained-difference-after-coupling",
        "full-def-og-004-discharge",
        "semantic-preselection-history-binding",
        "full-def-og-009-discharge",
        "endogenous-observer-role",
        "promotion",
    }.issubset(P3OG_ARITHMETIC_INPUT_NONCLAIMS)
    assert not hasattr(root_core, "p3og_arithmetic_input_source")
