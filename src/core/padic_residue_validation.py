"""Exact-type and resource gates for finite p-adic residue windows."""

from __future__ import annotations

import logging

from .padic_residue_types import PrimeBase, PadicResidueStage, PadicResidueWindow

logger = logging.getLogger(__name__)

MAX_PADIC_DEPTH = 128
MAX_PADIC_PRIME = 257
MAX_PADIC_SOURCE_BITS = 4096


class PadicResidueValidationError(ValueError):
    """A finite p-adic DTO failed exact structural validation."""


def is_bounded_prime(value: int) -> bool:
    """Decide primality inside the deliberately tiny I1 resource bound."""
    logger.debug("is_bounded_prime entry")
    if type(value) is not int or not 2 <= value <= MAX_PADIC_PRIME:
        logger.debug("is_bounded_prime exit result=False")
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            result = value == divisor
            logger.debug("is_bounded_prime exit result=%s", result)
            return result
        divisor += 1
    logger.debug("is_bounded_prime exit result=True")
    return True


def snapshot_prime_base(value: PrimeBase) -> PrimeBase:
    """Capture one exact bounded prime base."""
    logger.debug("snapshot_prime_base entry")
    if type(value) is not PrimeBase:
        logger.error("snapshot_prime_base invalid container type")
        raise PadicResidueValidationError("base must be an exact PrimeBase")
    try:
        prime = value.prime
    except AttributeError as exc:
        logger.error("snapshot_prime_base missing field")
        raise PadicResidueValidationError("prime is missing required fields") from exc
    if not is_bounded_prime(prime):
        logger.error("snapshot_prime_base invalid prime")
        raise PadicResidueValidationError("prime must be an exact bounded prime integer")
    result = PrimeBase(prime)
    logger.debug("snapshot_prime_base exit prime=%d", result.prime)
    return result


def snapshot_padic_stage(
    value: PadicResidueStage, prime: PrimeBase, expected_level: int
) -> PadicResidueStage:
    """Capture one canonical stage without checking predecessor agreement."""
    logger.debug("snapshot_padic_stage entry")
    prime = snapshot_prime_base(prime)
    if type(expected_level) is not int or not 0 <= expected_level < MAX_PADIC_DEPTH:
        logger.error("snapshot_padic_stage invalid expected level")
        raise PadicResidueValidationError("expected level must be a bounded exact integer")
    if type(value) is not PadicResidueStage:
        logger.error("snapshot_padic_stage invalid container type")
        raise PadicResidueValidationError("stage must be an exact PadicResidueStage")
    try:
        level, modulus, residue = value.level, value.modulus, value.residue
    except AttributeError as exc:
        logger.error("snapshot_padic_stage missing field")
        raise PadicResidueValidationError("stage is missing required fields") from exc
    if any(type(item) is not int for item in (level, modulus, residue)):
        logger.error("snapshot_padic_stage nonexact integer field")
        raise PadicResidueValidationError("stage fields must be exact integers")
    expected_modulus = prime.prime ** (expected_level + 1)
    if level != expected_level or modulus != expected_modulus:
        logger.error("snapshot_padic_stage level/modulus mismatch level=%r", level)
        raise PadicResidueValidationError("stage level or prime-power modulus is not canonical")
    if not 0 <= residue < modulus:
        logger.error("snapshot_padic_stage noncanonical residue level=%d", level)
        raise PadicResidueValidationError("stage residue must be canonical")
    result = PadicResidueStage(level, modulus, residue)
    logger.debug("snapshot_padic_stage exit level=%d", result.level)
    return result


def snapshot_padic_window(value: PadicResidueWindow) -> PadicResidueWindow:
    """Deep-capture a structural candidate while preserving incompatibility."""
    logger.debug("snapshot_padic_window entry")
    if type(value) is not PadicResidueWindow:
        logger.error("snapshot_padic_window invalid container type")
        raise PadicResidueValidationError("window must be an exact PadicResidueWindow")
    try:
        source_prime, source_stages = value.prime, value.stages
    except AttributeError as exc:
        logger.error("snapshot_padic_window missing field")
        raise PadicResidueValidationError("window is missing required fields") from exc
    prime = snapshot_prime_base(source_prime)
    if type(source_stages) is not tuple or not 1 <= len(source_stages) <= MAX_PADIC_DEPTH:
        logger.error("snapshot_padic_window invalid stages container")
        raise PadicResidueValidationError("stages must be a bounded nonempty exact tuple")
    stages = tuple(
        snapshot_padic_stage(stage, prime, level)
        for level, stage in enumerate(source_stages)
    )
    result = PadicResidueWindow(prime, stages)
    logger.debug("snapshot_padic_window exit levels=%d", len(stages))
    return result


def validate_padic_source_integer(value: int) -> int:
    """Reject bool/subclasses and integers beyond the constructor budget."""
    logger.debug("validate_padic_source_integer entry")
    if type(value) is not int or value.bit_length() > MAX_PADIC_SOURCE_BITS:
        logger.error("validate_padic_source_integer invalid source")
        raise PadicResidueValidationError("source must be a bounded exact integer")
    logger.debug("validate_padic_source_integer exit bits=%d", value.bit_length())
    return value
