"""Fail-closed exact snapshots for finite observer-descent data."""

from __future__ import annotations

import logging
from typing import TypeAlias

from .observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
    Response,
    State,
)

logger = logging.getLogger(__name__)

OBSERVER_DOCTRINE_SCHEMA = "veyra.observer-doctrine.r16.v1"
OBSERVER_DESCENT_SCHEMA = "veyra.observer-descent.r16.v1"
OBSERVER_BALANCE_SCHEMA = "veyra.observer-descent-balance.r16.v1"
CREST_BRAID_SCHEMA = "veyra.crest-braid.r16.v1"

ObserverSnapshot: TypeAlias = tuple[
    str,
    tuple[tuple[State, Response], ...],
    int,
]
DoctrineSnapshot: TypeAlias = tuple[
    str,
    tuple[State, ...],
    tuple[FiniteObserver, ...],
]
TransitionSnapshot: TypeAlias = tuple[
    str,
    tuple[State, ...],
    tuple[State, ...],
    tuple[tuple[State, State], ...],
]

MAX_CARRIER = 256
MAX_OBSERVERS = 256
MAX_NAME_BYTES = 128
MAX_VALUE_DEPTH = 8
MAX_VALUE_WIDTH = 64


def _exact_value(value: object, depth: int = 0) -> bool:
    """Accept only bounded canonical scalar/tuple values, never subclasses."""
    logger.debug("_exact_value entry type=%s depth=%d", type(value).__name__, depth)
    if depth > MAX_VALUE_DEPTH:
        logger.error("_exact_value depth exceeded depth=%d", depth)
        return False
    if type(value) in (type(None), int, str, bytes):
        result = not (
            type(value) in (str, bytes)
            and len(value) > MAX_NAME_BYTES
        )
        logger.debug("_exact_value exit scalar result=%s", result)
        return result
    if type(value) is tuple and len(value) <= MAX_VALUE_WIDTH:
        result = all(_exact_value(item, depth + 1) for item in value)
        logger.debug("_exact_value exit tuple result=%s", result)
        return result
    logger.error("_exact_value rejected type=%s", type(value).__name__)
    return False


def snapshot_observer(observer: object) -> ObserverSnapshot:
    """Read one exact slotted observer once and validate its closed payload."""
    logger.debug("snapshot_observer entry type=%s", type(observer).__name__)
    if type(observer) is not FiniteObserver:
        logger.error("snapshot_observer wrong type=%s", type(observer).__name__)
        raise TypeError("observer-requires-exact-dto")
    try:
        name, responses, cost = observer.name, observer.responses, observer.cost
    except AttributeError as error:
        logger.exception("snapshot_observer missing slot")
        raise TypeError("observer-requires-complete-slots") from error
    if (
        type(name) is not str
        or not name
        or len(name.encode("utf-8")) > MAX_NAME_BYTES
        or type(responses) is not tuple
        or type(cost) is not int
        or cost < 0
    ):
        logger.error("snapshot_observer invalid scalar fields name=%r cost=%r", name, cost)
        raise ValueError("observer-invalid-fields")
    for row in responses:
        if (
            type(row) is not tuple
            or len(row) != 2
            or not _exact_value(row[0])
            or not _exact_value(row[1])
        ):
            logger.error("snapshot_observer invalid response row")
            raise ValueError("observer-invalid-response-row")
    result = (name, responses, cost)
    logger.debug("snapshot_observer exit name=%s rows=%d", name, len(responses))
    return result


def snapshot_doctrine(doctrine: object) -> DoctrineSnapshot:
    """Read one exact doctrine once and enforce bounded canonical carriers."""
    logger.debug("snapshot_doctrine entry type=%s", type(doctrine).__name__)
    if type(doctrine) is not FiniteObserverDoctrine:
        logger.error("snapshot_doctrine wrong type=%s", type(doctrine).__name__)
        raise TypeError("doctrine-requires-exact-dto")
    try:
        name, carrier, observers = doctrine.name, doctrine.carrier, doctrine.observers
    except AttributeError as error:
        logger.exception("snapshot_doctrine missing slot")
        raise TypeError("doctrine-requires-complete-slots") from error
    if (
        type(name) is not str
        or not name
        or len(name.encode("utf-8")) > MAX_NAME_BYTES
        or type(carrier) is not tuple
        or not 0 < len(carrier) <= MAX_CARRIER
        or type(observers) is not tuple
        or not 0 < len(observers) <= MAX_OBSERVERS
        or any(not _exact_value(state) for state in carrier)
    ):
        logger.error("snapshot_doctrine invalid fields")
        raise ValueError("doctrine-invalid-fields")
    for observer in observers:
        snapshot_observer(observer)
    result = (name, carrier, observers)
    logger.debug(
        "snapshot_doctrine exit name=%s carrier=%d observers=%d",
        name,
        len(carrier),
        len(observers),
    )
    return result


def snapshot_transition(transition: object) -> TransitionSnapshot:
    """Read one exact finite transition once and validate closed graph rows."""
    logger.debug("snapshot_transition entry type=%s", type(transition).__name__)
    if type(transition) is not FiniteTransition:
        logger.error("snapshot_transition wrong type=%s", type(transition).__name__)
        raise TypeError("transition-requires-exact-dto")
    try:
        name = transition.name
        source = transition.source
        target = transition.target
        graph = transition.graph
    except AttributeError as error:
        logger.exception("snapshot_transition missing slot")
        raise TypeError("transition-requires-complete-slots") from error
    if (
        type(name) is not str
        or not name
        or len(name.encode("utf-8")) > MAX_NAME_BYTES
        or type(source) is not tuple
        or not 0 < len(source) <= MAX_CARRIER
        or type(target) is not tuple
        or not 0 < len(target) <= MAX_CARRIER
        or type(graph) is not tuple
        or len(graph) > MAX_CARRIER
        or any(not _exact_value(state) for state in source + target)
    ):
        logger.error("snapshot_transition invalid fields")
        raise ValueError("transition-invalid-fields")
    for row in graph:
        if (
            type(row) is not tuple
            or len(row) != 2
            or not _exact_value(row[0])
            or not _exact_value(row[1])
        ):
            logger.error("snapshot_transition invalid graph row")
            raise ValueError("transition-invalid-graph-row")
    result = (name, source, target, graph)
    logger.debug("snapshot_transition exit name=%s graph=%d", name, len(graph))
    return result
