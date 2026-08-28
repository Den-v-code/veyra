"""Replayable P3-N2 finite-family provenance for P3-OG arithmetic inputs."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .padic_completion_doctrine import padic_tower_doctrine
from .padic_completion_prime import prime_source
from .prime_power_observer_genesis_p3og_arithmetic_input_codec import (
    arithmetic_input_digest,
)
from .prime_power_observer_genesis_p3og_arithmetic_input_types import (
    P3OGArithmeticInputSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_source import validate_source
from .prime_power_observer_genesis_p3og_types import P3OGSource
from .prime_power_reduction_network_sources import finite_reduction_source
from .prime_power_reduction_network_types import FiniteFamilySource, FamilyCoordinate

SOURCE_VERSION = "p3og-arithmetic-input-source-v1"
DERIVATION_RULE_ID = "p3n2-finite-family-f0-f1-at-p3og-depth-v1"
LEFT_INPUT = 0
RIGHT_INPUT = 1


def _family_coordinate(family: FiniteFamilySource, depth: int) -> FamilyCoordinate:
    if type(family) is not FiniteFamilySource or type(family.coordinates) is not tuple:
        raise ValueError("p3og-arithmetic-input-family-shape")
    matches = tuple(
        coordinate
        for coordinate in family.coordinates
        if type(coordinate) is FamilyCoordinate and coordinate.depth == depth
    )
    if len(matches) != 1:
        raise ValueError("p3og-arithmetic-input-coordinate-coverage")
    return matches[0]


def p3og_arithmetic_input_source(source: P3OGSource) -> P3OGArithmeticInputSource:
    """Derive exact F0/F1 finite-family inputs from the P3-OG prime/depth only."""
    source = validate_source(source)
    try:
        prime = prime_source(source.prime)
    except ValueError as exc:
        raise ValueError("p3og-arithmetic-input-prime-outside-p3n2-envelope") from exc
    doctrine = padic_tower_doctrine()
    try:
        finite = finite_reduction_source(
            prime,
            doctrine,
            depths=(source.depth,),
            family_integers=(LEFT_INPUT, RIGHT_INPUT),
        )
    except ValueError as exc:
        raise ValueError("p3og-arithmetic-input-p3n2-resource-envelope") from exc

    by_integer = {family.integer: family for family in finite.families}
    if len(by_integer) != 2 or set(by_integer) != {LEFT_INPUT, RIGHT_INPUT}:
        raise ValueError("p3og-arithmetic-input-family-coverage")
    left_family = by_integer[LEFT_INPUT]
    right_family = by_integer[RIGHT_INPUT]
    left_coordinate = _family_coordinate(left_family, source.depth)
    right_coordinate = _family_coordinate(right_family, source.depth)
    modulus = source.prime ** (source.depth + 1)
    if (
        left_coordinate.residue != LEFT_INPUT % modulus
        or right_coordinate.residue != RIGHT_INPUT % modulus
        or left_coordinate.residue == right_coordinate.residue
    ):
        raise ValueError("p3og-arithmetic-input-coordinate-drift")

    fields = (
        SOURCE_VERSION,
        source.source_digest,
        source.prime,
        source.depth,
        modulus,
        prime.source_digest,
        doctrine.doctrine_digest,
        finite.source_digest,
        finite.p3t_raw_source.network_digest,
        left_family.family_digest,
        right_family.family_digest,
        left_coordinate.coordinate_digest,
        right_coordinate.coordinate_digest,
        LEFT_INPUT,
        RIGHT_INPUT,
        left_coordinate.residue,
        right_coordinate.residue,
        DERIVATION_RULE_ID,
    )
    return P3OGArithmeticInputSource(
        *fields,
        arithmetic_input_digest("arithmetic-input-source", *fields),
    )


def validate_p3og_arithmetic_input_source(
    source: P3OGSource,
    arithmetic_source: P3OGArithmeticInputSource,
) -> tuple[P3OGSource, P3OGArithmeticInputSource]:
    """Freshly reconstruct the exact finite-family source and reject any drift."""
    source = validate_source(source)
    if type(arithmetic_source) is not P3OGArithmeticInputSource:
        raise ValueError("p3og-arithmetic-input-source-type")
    try:
        expected = p3og_arithmetic_input_source(source)
        equal = compare_digest(
            canonical_bytes(arithmetic_source),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-arithmetic-input-source-malformed") from exc
    if not equal:
        raise ValueError("p3og-arithmetic-input-source-drift")
    return source, replace(expected)
