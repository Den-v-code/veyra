"""Hostile-safe context and candidate validation for semantic N0 pressure."""

from __future__ import annotations

import logging

from .prime_power_observer_actualization_common import digest, exact_hex, exact_shape, reject
from .prime_power_observer_actualization_history_validation import validate_rehashed_history
from .prime_power_observer_actualization_nested_validation import (
    bounded_text, exact_bounded_int, exact_tuple,
)
from .prime_power_observer_actualization_source_validation import validate_n0_source
from .prime_power_observer_actualization_types import (
    N0DiscriminationPressureCandidate, N0SeparatorPressureCandidate,
)

logger = logging.getLogger(__name__)
MAX_RESIDUE = 2**4096 - 1


def validate_pressure_context(source, history) -> None:
    """Authenticate the complete canonical source and rehashed history first."""
    logger.debug("validate_pressure_context entry")
    validate_n0_source(source)
    validate_rehashed_history(source, history)
    logger.debug("validate_pressure_context exit")


def validate_discrimination_inputs(family_ids, residues, claimed_distinct) -> None:
    """Validate builder inputs before repr, hashing, or bridge lookup."""
    logger.debug("validate_discrimination_inputs entry")
    families = exact_tuple(family_ids, "n0-pressure-families", maximum=2, length=2)
    for index, item in enumerate(families):
        bounded_text(item, f"n0-pressure-family-{index}", maximum=256)
    values = exact_tuple(residues, "n0-pressure-residues", maximum=2, length=2)
    for index, item in enumerate(values):
        exact_bounded_int(item, f"n0-pressure-residue-{index}", maximum=MAX_RESIDUE)
    if type(claimed_distinct) is not bool:
        reject("n0-pressure-distinct-bool-required")
    logger.debug("validate_discrimination_inputs exit")


def validate_separator_inputs(residues, claimed_equal) -> None:
    """Validate separator builder inputs before repr or hashing."""
    logger.debug("validate_separator_inputs entry")
    values = exact_tuple(residues, "n0-separator-residues", maximum=2, length=2)
    for index, item in enumerate(values):
        exact_bounded_int(item, f"n0-separator-residue-{index}", maximum=MAX_RESIDUE)
    if type(claimed_equal) is not bool:
        reject("n0-separator-equal-bool-required")
    logger.debug("validate_separator_inputs exit")


def validate_discrimination_candidate(source, history, candidate) -> dict:
    """Validate every candidate field, binding, and digest without DTO equality."""
    logger.debug("validate_discrimination_candidate entry")
    raw = exact_shape(
        candidate, N0DiscriminationPressureCandidate, "n0-discrimination-candidate",
    )
    for name in ("package_digest", "bridge_digest", "token_id", "scope_digest"):
        exact_hex(raw[name], f"n0-discrimination-{name}")
    validate_discrimination_inputs(
        raw["family_ids"], raw["claimed_residues"], raw["claimed_distinct"],
    )
    exact_hex(raw["candidate_digest"], "n0-discrimination-candidate-digest")
    bindings = (
        source.strict_package.wrapper_digest, source.bridge.bridge_digest,
        history.historical_token_id, source.scope.scope_digest,
    )
    if tuple(raw[name] for name in (
            "package_digest", "bridge_digest", "token_id", "scope_digest")) != bindings:
        reject("n0-discrimination-candidate-binding-drift")
    expected = digest("veyra.p3n0.discrimination-pressure.v1", (
        ("package", raw["package_digest"].encode()),
        ("bridge", raw["bridge_digest"].encode()),
        ("token", raw["token_id"].encode()), ("scope", raw["scope_digest"].encode()),
        ("families", repr(raw["family_ids"]).encode()),
        ("residues", repr(raw["claimed_residues"]).encode()),
        ("distinct", str(raw["claimed_distinct"]).encode()),
    ))
    if raw["candidate_digest"] != expected:
        reject("n0-discrimination-candidate-digest-drift")
    logger.debug("validate_discrimination_candidate exit")
    return raw


def validate_separator_candidate(source, history, candidate) -> dict:
    """Validate every separator field, binding, and digest without DTO equality."""
    logger.debug("validate_separator_candidate entry")
    raw = exact_shape(candidate, N0SeparatorPressureCandidate, "n0-separator-candidate")
    for name in ("package_digest", "bridge_digest", "token_id", "scope_digest"):
        exact_hex(raw[name], f"n0-separator-{name}")
    validate_separator_inputs(raw["claimed_fine_residues"], raw["claimed_equal_at_fine"])
    exact_hex(raw["candidate_digest"], "n0-separator-candidate-digest")
    bindings = (
        source.strict_package.wrapper_digest, source.bridge.bridge_digest,
        history.historical_token_id, source.scope.scope_digest,
    )
    if tuple(raw[name] for name in (
            "package_digest", "bridge_digest", "token_id", "scope_digest")) != bindings:
        reject("n0-separator-candidate-binding-drift")
    expected = digest("veyra.p3n0.separator-pressure.v1", (
        ("package", raw["package_digest"].encode()),
        ("bridge", raw["bridge_digest"].encode()),
        ("token", raw["token_id"].encode()), ("scope", raw["scope_digest"].encode()),
        ("residues", repr(raw["claimed_fine_residues"]).encode()),
        ("equal", str(raw["claimed_equal_at_fine"]).encode()),
    ))
    if raw["candidate_digest"] != expected:
        reject("n0-separator-candidate-digest-drift")
    logger.debug("validate_separator_candidate exit")
    return raw
