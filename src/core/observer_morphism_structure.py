"""Trusted structural projection checks for snapshotted P1-A inputs."""

from __future__ import annotations

import logging

from .observer_core_codec import canonical_observer_bytes, decode_observer
from .observer_core_types import Pair
from .positive_ontology_types import ObserverDoctrine
from .observer_morphism_types import ProjectionStep

logger = logging.getLogger(__name__)


def _project_observer(
    observer: object, projection: tuple[ProjectionStep, ...]
) -> object | None:
    """Follow an exact structural Pair path; empty path is identity."""
    logger.debug("_project_observer entry steps=%d", len(projection))
    cursor = observer
    for step in projection:
        if type(cursor) is not Pair:
            logger.debug("_project_observer exit factorizes=False")
            return None
        cursor = cursor.left if step is ProjectionStep.LEFT else cursor.right
    logger.debug("_project_observer exit factorizes=True")
    return cursor


def _projection_factorizes(
    doctrine: ObserverDoctrine,
    fine_id: str,
    coarse_id: str,
    projection: tuple[ProjectionStep, ...],
) -> bool:
    """Check exact canonical endpoint equality for one declared projection."""
    logger.debug("_projection_factorizes entry")
    members = {item.observer_id: item for item in doctrine.observers}
    endpoint = _project_observer(decode_observer(members[fine_id].canonical), projection)
    result = (
        endpoint is not None
        and canonical_observer_bytes(endpoint) == members[coarse_id].canonical
    )
    logger.debug("_projection_factorizes exit result=%s", result)
    return result
