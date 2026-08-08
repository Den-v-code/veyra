"""Semantic A05/A08 pressure without canonical package mutation."""

from __future__ import annotations

import logging

from .prime_power_observer_actualization_common import digest, reject
from .prime_power_observer_actualization_pressure_validation import (
    validate_discrimination_candidate, validate_discrimination_inputs,
    validate_pressure_context, validate_separator_candidate, validate_separator_inputs,
)
from .prime_power_observer_actualization_types import (
    N0DiscriminationPressureCandidate, N0History, N0SeparatorPressureCandidate,
    N0Source, PremiseStatus,
)

logger = logging.getLogger(__name__)


def discrimination_candidate(source: N0Source, history: N0History, family_ids,
                             claimed_residues, claimed_distinct=True):
    """Build one well-formed claim against immutable canonical bridge rows."""
    logger.debug("discrimination_candidate entry")
    validate_pressure_context(source, history)
    validate_discrimination_inputs(family_ids, claimed_residues, claimed_distinct)
    value = digest("veyra.p3n0.discrimination-pressure.v1", (
        ("package", source.strict_package.wrapper_digest.encode()),
        ("bridge", source.bridge.bridge_digest.encode()),
        ("token", history.historical_token_id.encode()),
        ("scope", source.scope.scope_digest.encode()),
        ("families", repr(family_ids).encode()),
        ("residues", repr(claimed_residues).encode()),
        ("distinct", str(claimed_distinct).encode()),
    ))
    result = N0DiscriminationPressureCandidate(
        source.strict_package.wrapper_digest, source.bridge.bridge_digest,
        history.historical_token_id, source.scope.scope_digest, family_ids,
        claimed_residues, claimed_distinct, value,
    )
    logger.debug("discrimination_candidate exit")
    return result


def refute_discrimination(source, history, candidate) -> PremiseStatus:
    """Refute a false distinctness claim while rejecting identity mutation."""
    logger.debug("refute_discrimination entry")
    validate_pressure_context(source, history)
    raw = validate_discrimination_candidate(source, history, candidate)
    rows = {row.family_id: row for row in source.bridge.rows}
    if any(name not in rows for name in raw["family_ids"]):
        reject("n0-discrimination-family-not-bridged")
    try:
        residues = tuple(next(x.residue for x in rows[name].finite_family.coordinates
                              if x.depth == source.depth) for name in raw["family_ids"])
    except StopIteration:
        reject("n0-discrimination-coordinate-missing")
    if raw["claimed_residues"] != residues:
        reject("n0-discrimination-typed-residue-drift")
    actual = residues[0] != residues[1]
    result = (PremiseStatus.ESTABLISHED if raw["claimed_distinct"] == actual
              else PremiseStatus.REFUTED)
    logger.debug("refute_discrimination exit status=%s", result.value)
    return result


def separator_candidate(source: N0Source, history: N0History,
                        claimed_fine_residues, claimed_equal_at_fine=True):
    """Build a typed equality claim at rho_(n+1) for the canonical strict pair."""
    logger.debug("separator_candidate entry")
    validate_pressure_context(source, history)
    validate_separator_inputs(claimed_fine_residues, claimed_equal_at_fine)
    value = digest("veyra.p3n0.separator-pressure.v1", (
        ("package", source.strict_package.wrapper_digest.encode()),
        ("bridge", source.bridge.bridge_digest.encode()),
        ("token", history.historical_token_id.encode()),
        ("scope", source.scope.scope_digest.encode()),
        ("residues", repr(claimed_fine_residues).encode()),
        ("equal", str(claimed_equal_at_fine).encode()),
    ))
    result = N0SeparatorPressureCandidate(
        source.strict_package.wrapper_digest, source.bridge.bridge_digest,
        history.historical_token_id, source.scope.scope_digest,
        claimed_fine_residues, claimed_equal_at_fine, value,
    )
    logger.debug("separator_candidate exit")
    return result


def refute_separator(source, history, candidate) -> PremiseStatus:
    """Refute equality at n+1 for F0/Fsep without mutating canonical rows."""
    logger.debug("refute_separator entry")
    validate_pressure_context(source, history)
    raw = validate_separator_candidate(source, history, candidate)
    rows = {row.family_id: row for row in source.bridge.rows}
    names = ("integer:0", f"integer:{source.n1_packages[2].integer.z}")
    try:
        residues = tuple(next(x.residue for x in rows[name].finite_family.coordinates
                              if x.depth == source.depth + 1) for name in names)
    except (KeyError, StopIteration):
        reject("n0-separator-coordinate-missing")
    if raw["claimed_fine_residues"] != residues:
        reject("n0-separator-typed-residue-drift")
    actual_equal = residues[0] == residues[1]
    result = (PremiseStatus.ESTABLISHED if raw["claimed_equal_at_fine"] == actual_equal
              else PremiseStatus.REFUTED)
    logger.debug("refute_separator exit status=%s", result.value)
    return result
