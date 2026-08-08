"""Immutable input snapshots for finite VAM theorem carriers."""

from __future__ import annotations

import logging
from types import MappingProxyType

from src.core.theorem_language import TheoremEnvironment

logger = logging.getLogger(__name__)


def snapshot_environments(
    environments: tuple[TheoremEnvironment, ...],
) -> tuple[TheoremEnvironment, ...]:
    """Read every assignment mapping once and freeze the exact transported values."""
    logger.debug("snapshot_environments entry count=%d", len(environments))
    rows = []
    for environment in environments:
        try:
            assignments = dict(environment.assignments.items())
        except (AttributeError, TypeError, ValueError) as exc:
            logger.error(
                "snapshot_environments invalid mapping env=%r error=%s",
                getattr(environment, "name", "<invalid>"),
                exc,
            )
            assignments = {}
        rows.append(
            TheoremEnvironment(environment.name, MappingProxyType(assignments))
        )
    result = tuple(rows)
    logger.debug("snapshot_environments exit count=%d", len(result))
    return result
