"""Hook-free exact-instance primitives for P1-C2 result validation."""

from __future__ import annotations

from dataclasses import fields
from enum import Enum
import logging

from .confluence_preflight import ConfluenceValidationError

logger = logging.getLogger(__name__)


def reject(reason: str) -> None:
    """Raise the closed C2 validation error without rendering attacker data."""
    logger.error("aggregate result rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


def exact_instance(value: object, kind: type, field: str) -> None:
    """Require exact DTO type and exactly its declared instance-field set."""
    logger.debug("aggregate exact instance entry field=%s", field)
    if type(value) is not kind:
        reject(f"confluence-aggregate-{field}-must-be-exact")
    try:
        mapping = vars(value)
    except TypeError as exc:
        logger.error("aggregate exact instance missing dictionary field=%s", field)
        raise ConfluenceValidationError(
            f"confluence-aggregate-{field}-instance-fields"
        ) from exc
    expected = tuple(item.name for item in fields(kind))
    if type(mapping) is not dict or len(mapping) != len(expected):
        reject(f"confluence-aggregate-{field}-instance-fields")
    keys = tuple(mapping.keys())
    if any(type(item) is not str for item in keys):
        reject(f"confluence-aggregate-{field}-instance-fields")
    if tuple(sorted(keys)) != tuple(sorted(expected)):
        reject(f"confluence-aggregate-{field}-instance-fields")
    logger.debug("aggregate exact instance exit field=%s", field)


def exact_fields(
    raw: object, expected: object, schema: tuple[tuple[str, type], ...], reason: str,
) -> None:
    """Compare exact primitive/enum fields without coercive equality hooks."""
    logger.debug("aggregate exact fields entry reason=%s", reason)
    for name, kind in schema:
        try:
            supplied, wanted = getattr(raw, name), getattr(expected, name)
        except AttributeError as exc:
            logger.error("aggregate exact fields missing reason=%s", reason)
            raise ConfluenceValidationError(reason) from exc
        if type(supplied) is not kind:
            reject(reason)
        if issubclass(kind, Enum):
            if supplied is not wanted:
                reject(reason)
        elif supplied != wanted:
            reject(reason)
    logger.debug("aggregate exact fields exit reason=%s", reason)


def exact_optional_string(raw: object, expected: object, reason: str) -> None:
    """Compare an optional string without accepting subclasses or coercions."""
    logger.debug("aggregate optional string entry reason=%s", reason)
    if expected is None:
        if raw is not None:
            reject(reason)
    elif type(raw) is not str or raw != expected:
        reject(reason)
    logger.debug("aggregate optional string exit reason=%s", reason)
