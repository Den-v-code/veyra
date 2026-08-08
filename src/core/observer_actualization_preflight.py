"""Shallow bounded container preflight for finite P1-E4 sources."""

from __future__ import annotations

import logging

from .observer_actualization_graph import reject
from .observer_actualization_types import (
    ActualizationResourceBound, ActualizationResourcePolicy, HistoryEvent,
)

logger = logging.getLogger(__name__)


def source_container_preflight(
    policy: ActualizationResourcePolicy, events: object, access: object,
    assumptions: object, counterfactuals: object,
) -> tuple[ActualizationResourceBound, int, int] | None:
    """Count raw containers and parent tuple lengths before deep snapshotting."""
    logger.debug("actualization source container preflight entry")
    values = (events, access, assumptions, counterfactuals)
    if any(type(item) is not tuple for item in values):
        reject("actualization-source-containers-must-be-tuples")
    checks = (
        (len(events), policy.max_events, ActualizationResourceBound.EVENTS),
        (len(access), policy.max_access_edges, ActualizationResourceBound.ACCESS_EDGES),
        (len(assumptions), policy.max_assumptions, ActualizationResourceBound.ASSUMPTIONS),
        (len(counterfactuals), policy.max_counterfactuals,
         ActualizationResourceBound.COUNTERFACTUALS),
    )
    for required, allowed, bound in checks:
        if required > allowed:
            logger.debug("actualization source preflight exit bound=%s", bound.value)
            return bound, required, allowed
    parent_count = 0
    for event in events:
        if type(event) is not HistoryEvent:
            reject("history-event-must-be-exact")
        try:
            parents = event.parent_ids
        except AttributeError:
            reject("history-event-fields-missing")
        if type(parents) is not tuple:
            reject("invalid-parent-ids")
        parent_count += len(parents)
    if parent_count > policy.max_parent_edges:
        logger.debug("actualization source preflight exit parent bound")
        return (
            ActualizationResourceBound.PARENT_EDGES, parent_count,
            policy.max_parent_edges,
        )
    logger.debug("actualization source container preflight exit clean")
    return None
