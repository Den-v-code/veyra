"""Closed DTOs for P3-N2-derived P3-OG arithmetic input provenance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class P3OGArithmeticInputSource:
    """Selection-free exact F0/F1 source derived from the finite prime-power tower."""

    version: str
    pressure_source_digest: str
    prime_value: int
    depth: int
    modulus: int
    p3n2_prime_source_digest: str
    p3n2_doctrine_digest: str
    p3n2_finite_source_digest: str
    p3n2_network_digest: str
    left_family_digest: str
    right_family_digest: str
    left_coordinate_digest: str
    right_coordinate_digest: str
    left_input: int
    right_input: int
    left_residue: int
    right_residue: int
    derivation_rule_id: str
    source_digest: str


P3OG_ARITHMETIC_INPUT_NONCLAIMS = (
    "p3n2-theorem-judgment",
    "p3t-observer-network-judgment",
    "semantic-coupling-execution",
    "retained-difference-after-coupling",
    "common-continuation-preservation",
    "later-transition-or-response-efficacy",
    "full-def-og-004-discharge",
    "full-def-og-005-discharge",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "birth-core-or-historical-token",
    "endogenous-observer-role",
    "doctrine-admission",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "promotion",
)
