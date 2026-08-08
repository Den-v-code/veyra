"""Exact scalar/container guards for P2-S status and promotion audit."""

from __future__ import annotations

import logging
from typing import NoReturn

logger = logging.getLogger(__name__)
MAX_ID_BYTES = 128
MAX_STATIC_ROWS = 256


class StatusPromotionValidationError(ValueError):
    """A P2-S registry, audit, projection, or attack representation was invalid."""


def reject(reason: str) -> NoReturn:
    logger.error("status-promotion rejected reason=%s", reason)
    raise StatusPromotionValidationError(reason)


def exact_shape(value: object, expected_type: type, field: str) -> None:
    logger.debug("exact_shape entry field=%s", field)
    if type(value) is not expected_type:
        reject(f"{field}-must-be-exact")
    if set(vars(value)) != set(expected_type.__dataclass_fields__):
        reject(f"{field}-shape-drift")
    logger.debug("exact_shape exit field=%s", field)


def exact_identifier(value: object, field: str) -> str:
    logger.debug("exact_identifier entry field=%s", field)
    if type(value) is not str or not value:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_ID_BYTES:
        reject(f"invalid-{field}")
    logger.debug("exact_identifier exit field=%s", field)
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


def exact_tuple(value: object, field: str, *, nonempty: bool = False) -> tuple:
    logger.debug("exact_tuple entry field=%s", field)
    if type(value) is not tuple or (nonempty and not value) or len(value) > MAX_STATIC_ROWS:
        reject(f"invalid-{field}")
    logger.debug("exact_tuple exit field=%s rows=%d", field, len(value))
    return value


def exact_bool(value: object, field: str) -> bool:
    logger.debug("exact_bool entry field=%s", field)
    if type(value) is not bool:
        reject(f"invalid-{field}")
    logger.debug("exact_bool exit field=%s", field)
    return value


def exact_natural(value: object, field: str, maximum: int = 1_000_000) -> int:
    logger.debug("exact_natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= maximum:
        reject(f"invalid-{field}")
    logger.debug("exact_natural exit field=%s", field)
    return value
