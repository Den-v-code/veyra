"""Finite executable kernel for Veyra observer descent."""

from __future__ import annotations

import logging

from .observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
    ObserverDescent,
    Response,
    State,
    StatePair,
)
from .observer_descent_validation import (
    snapshot_doctrine,
    snapshot_observer,
    snapshot_transition,
)

logger = logging.getLogger(__name__)


def observer_response_map(observer: FiniteObserver) -> dict[State, Response]:
    """Decode an observer table while rejecting duplicate states."""
    logger.debug("observer_response_map entry type=%s", type(observer).__name__)
    name, rows, _ = snapshot_observer(observer)
    result: dict[State, Response] = {}
    for state, response in rows:
        if state in result:
            logger.error("observer_response_map duplicate state observer=%s", name)
            raise ValueError("observer-response-duplicate-state")
        result[state] = response
    logger.debug("observer_response_map exit observer=%s rows=%d", name, len(result))
    return result


def transition_map(transition: FiniteTransition) -> dict[State, State]:
    """Decode and validate one total finite transition graph."""
    logger.debug("transition_map entry type=%s", type(transition).__name__)
    name, source, target_rows, graph = snapshot_transition(transition)
    result: dict[State, State] = {}
    target = set(target_rows)
    for state, image in graph:
        if state in result:
            logger.error("transition_map duplicate source transition=%s", name)
            raise ValueError("transition-duplicate-source")
        if image not in target:
            logger.error("transition_map image outside target transition=%s", name)
            raise ValueError("transition-image-outside-target")
        result[state] = image
    if set(result) != set(source) or len(result) != len(source):
        logger.error("transition_map non-total transition=%s", name)
        raise ValueError("transition-not-total")
    logger.debug("transition_map exit transition=%s rows=%d", name, len(result))
    return result


def distinction_set(
    observer: FiniteObserver,
    carrier: tuple[State, ...],
) -> frozenset[StatePair]:
    """Return the ordered pairs distinguished by a total observer."""
    name, _, _ = snapshot_observer(observer)
    if type(carrier) is not tuple:
        logger.error("distinction_set carrier is not exact tuple")
        raise TypeError("distinction-carrier-requires-exact-tuple")
    logger.debug("distinction_set entry observer=%s carrier=%d", name, len(carrier))
    responses = observer_response_map(observer)
    if set(responses) != set(carrier) or len(responses) != len(carrier):
        logger.error("distinction_set carrier mismatch observer=%s", name)
        raise ValueError("observer-carrier-mismatch")
    result = frozenset(
        (left, right)
        for left in carrier
        for right in carrier
        if left != right and responses[left] != responses[right]
    )
    logger.debug("distinction_set exit observer=%s pairs=%d", name, len(result))
    return result


def _unique_join(
    left: frozenset[StatePair],
    right: frozenset[StatePair],
    admitted: tuple[frozenset[StatePair], ...],
) -> frozenset[StatePair]:
    """Return the unique least admitted upper bound of two distinction sets."""
    logger.debug("_unique_join entry left=%d right=%d", len(left), len(right))
    upper = tuple(item for item in admitted if left <= item and right <= item)
    minimal = tuple(item for item in upper if not any(other < item for other in upper))
    if len(minimal) != 1:
        logger.error("_unique_join missing or ambiguous count=%d", len(minimal))
        raise ValueError("observer-doctrine-not-join-semilattice")
    logger.debug("_unique_join exit pairs=%d", len(minimal[0]))
    return minimal[0]


def validate_doctrine(doctrine: FiniteObserverDoctrine) -> None:
    """Require a nonempty finite doctrine with unique internal joins.

    This does not make descent total for arbitrary external pullbacks: an
    internal admitted join can overshoot the concrete relation.  Descent
    therefore remains a fail-closed partial operation unless a greatest
    admitted lower approximation exists for the particular pullback.
    """
    name, carrier, observers = snapshot_doctrine(doctrine)
    logger.debug("validate_doctrine entry doctrine=%s", name)
    if len(set(carrier)) != len(carrier):
        logger.error("validate_doctrine invalid carrier doctrine=%s", name)
        raise ValueError("observer-doctrine-invalid-carrier")
    names = tuple(snapshot_observer(observer)[0] for observer in observers)
    if not names or len(set(names)) != len(names):
        logger.error("validate_doctrine invalid names doctrine=%s", name)
        raise ValueError("observer-doctrine-invalid-names")
    admitted = tuple(distinction_set(observer, carrier) for observer in observers)
    if len(set(admitted)) != len(admitted) or frozenset() not in admitted:
        logger.error("validate_doctrine extensional duplicate or no bottom doctrine=%s", name)
        raise ValueError("observer-doctrine-invalid-extensional-order")
    for left in admitted:
        for right in admitted:
            _unique_join(left, right, admitted)
    logger.debug("validate_doctrine exit doctrine=%s observers=%d", name, len(admitted))


def observer_by_name(doctrine: FiniteObserverDoctrine, name: str) -> FiniteObserver:
    """Select exactly one admitted observer by stable name."""
    doctrine_name, _, observers = snapshot_doctrine(doctrine)
    if type(name) is not str:
        logger.error("observer_by_name invalid name type=%s", type(name).__name__)
        raise TypeError("observer-name-requires-exact-string")
    logger.debug("observer_by_name entry doctrine=%s name=%s", doctrine_name, name)
    matches = tuple(
        observer
        for observer in observers
        if snapshot_observer(observer)[0] == name
    )
    if len(matches) != 1:
        logger.error("observer_by_name invalid match count=%d name=%s", len(matches), name)
        raise ValueError("observer-name-not-unique")
    logger.debug("observer_by_name exit name=%s", name)
    return matches[0]


def pullback_observer(
    transition: FiniteTransition,
    target_observer: FiniteObserver,
) -> FiniteObserver:
    """Pull a total observer response backward through a transition."""
    transition_name, source, target, _ = snapshot_transition(transition)
    observer_name, _, observer_cost = snapshot_observer(target_observer)
    logger.debug(
        "pullback_observer entry transition=%s observer=%s",
        transition_name,
        observer_name,
    )
    graph = transition_map(transition)
    target_responses = observer_response_map(target_observer)
    if set(target_responses) != set(target):
        logger.error("pullback_observer target carrier mismatch")
        raise ValueError("pullback-target-carrier-mismatch")
    result = FiniteObserver(
        f"{transition_name}^sharp({observer_name})",
        tuple((state, target_responses[graph[state]]) for state in source),
        observer_cost,
    )
    logger.debug("pullback_observer exit observer=%s", result.name)
    return result


def observer_descent(
    source_doctrine: FiniteObserverDoctrine,
    transition: FiniteTransition,
    target_observer: FiniteObserver,
) -> ObserverDescent:
    """Compute a unique greatest admitted source observer, or fail closed."""
    doctrine_name, carrier, observers = snapshot_doctrine(source_doctrine)
    transition_name, source, _, _ = snapshot_transition(transition)
    target_name, _, _ = snapshot_observer(target_observer)
    logger.debug(
        "observer_descent entry doctrine=%s transition=%s target=%s",
        doctrine_name,
        transition_name,
        target_name,
    )
    validate_doctrine(source_doctrine)
    if source != carrier:
        logger.error("observer_descent source carrier mismatch")
        raise ValueError("descent-source-carrier-mismatch")
    raw_observer = pullback_observer(transition, target_observer)
    raw = distinction_set(raw_observer, source)
    rows = tuple(
        (observer, distinction_set(observer, carrier))
        for observer in observers
    )
    candidates = tuple((observer, marks) for observer, marks in rows if marks <= raw)
    greatest = tuple(
        item
        for item in candidates
        if not any(item[1] < other[1] for other in candidates)
    )
    if len(greatest) != 1:
        logger.error("observer_descent greatest observer count=%d", len(greatest))
        raise ValueError("descent-not-unique")
    observer, admitted = greatest[0]
    result = ObserverDescent(
        transition_name,
        target_name,
        snapshot_observer(observer)[0],
        raw,
        admitted,
        raw - admitted,
    )
    logger.debug(
        "observer_descent exit descended=%s residual=%d",
        result.descended_observer,
        len(result.residual),
    )
    return result


def compose_transitions(
    first: FiniteTransition,
    second: FiniteTransition,
) -> FiniteTransition:
    """Compose `first` then `second` as an exact finite graph."""
    first_name, first_source, first_target, _ = snapshot_transition(first)
    second_name, second_source, second_target, _ = snapshot_transition(second)
    logger.debug("compose_transitions entry first=%s second=%s", first_name, second_name)
    if first_target != second_source:
        logger.error("compose_transitions carrier mismatch")
        raise ValueError("transition-composition-carrier-mismatch")
    first_map = transition_map(first)
    second_map = transition_map(second)
    result = FiniteTransition(
        f"{second_name}∘{first_name}",
        first_source,
        second_target,
        tuple((state, second_map[first_map[state]]) for state in first_source),
    )
    logger.debug("compose_transitions exit transition=%s", result.name)
    return result
