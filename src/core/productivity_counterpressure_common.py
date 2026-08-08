"""Shared exact validators for P1-D2."""

from __future__ import annotations

import logging
from typing import NoReturn

logger = logging.getLogger(__name__)
MAX_NATURAL = 1_000_000_000
MAX_IDENTIFIER_BYTES = 64


class CounterpressureValidationError(ValueError):
    """A D2 representation, source, result, or commitment was invalid."""


def reject(reason: str) -> NoReturn:
    logger.error("counterpressure rejected reason=%s", reason)
    raise CounterpressureValidationError(reason)


def exact_natural(value: object, field: str) -> int:
    logger.debug("exact_natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= MAX_NATURAL:
        reject(f"invalid-{field}")
    logger.debug("exact_natural exit field=%s", field)
    return value


def exact_identifier(value: object, field: str) -> str:
    logger.debug("exact_identifier entry field=%s", field)
    if type(value) is not str or not value:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_IDENTIFIER_BYTES:
        reject(f"invalid-{field}")
    logger.debug("exact_identifier exit field=%s bytes=%d", field, size)
    return value


def exact_digest(value: object, field: str) -> str:
    logger.debug("exact_digest entry field=%s", field)
    if (
        type(value) is not str or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        reject(f"invalid-{field}")
    logger.debug("exact_digest exit field=%s", field)
    return value


def exact_dataclass_shape(value: object, expected_type: type, field: str) -> None:
    """Reject subclasses, missing fields, and injected instance attributes."""
    logger.debug("exact_dataclass_shape entry field=%s", field)
    if type(value) is not expected_type:
        reject(f"{field}-must-be-exact")
    if set(vars(value)) != set(expected_type.__dataclass_fields__):
        reject(f"{field}-shape-drift")
    logger.debug("exact_dataclass_shape exit field=%s", field)
