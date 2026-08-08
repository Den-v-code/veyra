"""Typed partial semantics for the closed R11 observer core."""

from __future__ import annotations

import logging
from typing import NoReturn

from .observer_core_types import (
    Apply,
    Blocked,
    DomainBlocked,
    Echo,
    EchoOutcome,
    Input,
    LeafKind,
    Mark,
    MarkValue,
    Mismatch,
    ObstructionCode,
    Observation,
    ObserverExpr,
    ObserverObstruction,
    Pair,
    PairKind,
    PairValue,
    PathStep,
    PrimitiveId,
    Ready,
    RecurrenceValue,
    ResponseKind,
    ResponseValue,
)
from .proof_core_types import CoreTerm, Pulse, Silence

logger = logging.getLogger(__name__)
MAX_OBSERVER_NODES = 2048
MAX_OBSERVER_DEPTH = 128
MAX_RECURRENCE_NODES = 2048
MAX_RECURRENCE_DEPTH = 128


class ObserverCoreError(ValueError):
    """A deterministic observer-core validation rejection."""


def _reject(reason: str) -> NoReturn:
    logger.error("observer core rejected reason=%s", reason)
    raise ObserverCoreError(reason)


def infer_observer_kind(observer: ObserverExpr) -> ResponseKind:
    """Validate an observer iteratively and infer its unique response kind."""
    logger.debug("infer_observer_kind entry type=%s", type(observer).__name__)
    stack: list[tuple[bool, object, int]] = [(False, observer, 0)]
    active: set[int] = set()
    kinds: list[ResponseKind] = []
    nodes = 0
    while stack:
        exiting, node, depth = stack.pop()
        identity = id(node)
        if exiting:
            active.remove(identity)
            if type(node) is Input:
                kinds.append(LeafKind.RECURRENCE)
            elif type(node) is Apply:
                child_kind = kinds.pop()
                if type(node.primitive) is not PrimitiveId or child_kind is not LeafKind.RECURRENCE:
                    _reject("invalid-primitive-application")
                kinds.append(LeafKind.RECURRENCE if node.primitive is PrimitiveId.TAIL else LeafKind.MARK)
            else:
                right, left = kinds.pop(), kinds.pop()
                kinds.append(PairKind(left, right))
            continue
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH:
            _reject("observer-resource-limit")
        if identity in active:
            _reject("circular-observer")
        if type(node) not in {Input, Apply, Pair}:
            _reject(f"unknown-observer-node:{type(node).__name__}")
        active.add(identity)
        stack.append((True, node, depth))
        if type(node) is Apply:
            stack.append((False, node.child, depth + 1))
        elif type(node) is Pair:
            stack.append((False, node.right, depth + 1))
            stack.append((False, node.left, depth + 1))
    if len(kinds) != 1:
        _reject("invalid-observer-shape")
    result = kinds[0]
    logger.debug("infer_observer_kind exit kind=%r nodes=%d", result, nodes)
    return result


def validate_closed_recurrence(term: CoreTerm) -> None:
    """Accept only finite, closed R7 Silence/Pulse recurrence values."""
    logger.debug("validate_closed_recurrence entry type=%s", type(term).__name__)
    stack: list[tuple[bool, object, int]] = [(False, term, 0)]
    active: set[int] = set()
    nodes = 0
    while stack:
        exiting, node, depth = stack.pop()
        identity = id(node)
        if exiting:
            active.remove(identity)
            continue
        nodes += 1
        if nodes > MAX_RECURRENCE_NODES or depth > MAX_RECURRENCE_DEPTH:
            _reject("recurrence-resource-limit")
        if identity in active:
            _reject("circular-recurrence")
        if type(node) not in {Silence, Pulse}:
            _reject(f"non-value-recurrence:{type(node).__name__}")
        active.add(identity)
        stack.append((True, node, depth))
        if type(node) is Pulse:
            stack.append((False, node.tail, depth + 1))
    logger.debug("validate_closed_recurrence exit nodes=%d", nodes)


def _prefixed(step: PathStep, blocked: Blocked) -> Blocked:
    logger.debug("_prefixed entry step=%s count=%d", step.value, len(blocked.obstructions))
    result = Blocked(tuple(ObserverObstruction(item.code, (step,) + item.path) for item in blocked.obstructions))
    logger.debug("_prefixed exit count=%d", len(result.obstructions))
    return result


def observe(observer: ObserverExpr, recurrence: CoreTerm) -> Observation:
    """Evaluate a closed observer without exception-based extension hooks."""
    logger.debug("observe entry observer=%s recurrence=%s", type(observer).__name__, type(recurrence).__name__)
    infer_observer_kind(observer)
    validate_closed_recurrence(recurrence)
    stack: list[tuple[bool, object]] = [(False, observer)]
    values: list[Observation] = []
    while stack:
        exiting, node = stack.pop()
        if not exiting:
            stack.append((True, node))
            if type(node) is Apply:
                stack.append((False, node.child))
            elif type(node) is Pair:
                stack.append((False, node.right))
                stack.append((False, node.left))
            continue
        if type(node) is Input:
            values.append(Ready(RecurrenceValue(recurrence)))
            continue
        if type(node) is Apply:
            child = values.pop()
            step = PathStep.APPLY_TAIL if node.primitive is PrimitiveId.TAIL else PathStep.APPLY_CREST
            if type(child) is Blocked:
                values.append(_prefixed(step, child))
                continue
            if type(child) is not Ready or type(child.value) is not RecurrenceValue:
                _reject("internal-response-kind-mismatch")
            value = child.value.recurrence
            if node.primitive is PrimitiveId.TAIL:
                values.append(
                    Blocked((ObserverObstruction(ObstructionCode.TAIL_OF_SILENCE, (step,)),))
                    if type(value) is Silence
                    else Ready(RecurrenceValue(value.tail))
                )
            else:
                values.append(Ready(MarkValue(Mark.SILENT if type(value) is Silence else Mark.PULSE)))
            continue
        right, left = values.pop(), values.pop()
        if type(left) is Ready and type(right) is Ready:
            values.append(Ready(PairValue(left.value, right.value)))
        else:
            left_obs = () if type(left) is Ready else _prefixed(PathStep.PAIR_LEFT, left).obstructions
            right_obs = () if type(right) is Ready else _prefixed(PathStep.PAIR_RIGHT, right).obstructions
            values.append(Blocked(left_obs + right_obs))
    if len(values) != 1 or type(values[0]) not in {Ready, Blocked}:
        _reject("invalid-observation-result")
    result = values[0]
    if type(result) is Blocked and not result.obstructions:
        _reject("empty-obstruction-set")
    logger.debug("observe exit status=%s", type(result).__name__)
    return result


def _response_equal(left: ResponseValue, right: ResponseValue) -> bool:
    logger.debug("_response_equal entry left=%s right=%s", type(left).__name__, type(right).__name__)
    stack: list[tuple[object, object]] = [(left, right)]
    while stack:
        first, second = stack.pop()
        if type(first) is not type(second):
            logger.debug("_response_equal exit result=False type-mismatch")
            return False
        if type(first) is MarkValue:
            if first.mark is not second.mark:
                logger.debug("_response_equal exit result=False mark-mismatch")
                return False
        elif type(first) is RecurrenceValue:
            lterm, rterm = first.recurrence, second.recurrence
            while type(lterm) is Pulse and type(rterm) is Pulse:
                lterm, rterm = lterm.tail, rterm.tail
            if type(lterm) is not Silence or type(rterm) is not Silence:
                logger.debug("_response_equal exit result=False recurrence-mismatch")
                return False
        elif type(first) is PairValue:
            stack.append((first.right, second.right))
            stack.append((first.left, second.left))
        else:
            _reject("invalid-response-value")
    logger.debug("_response_equal exit result=True")
    return True


def echo(observer: ObserverExpr, left: CoreTerm, right: CoreTerm) -> EchoOutcome:
    """Compare only defined responses; blockage never becomes echo."""
    logger.debug("echo entry observer=%s", type(observer).__name__)
    left_result, right_result = observe(observer, left), observe(observer, right)
    if type(left_result) is Blocked or type(right_result) is Blocked:
        result: EchoOutcome = DomainBlocked(
            left_result.obstructions if type(left_result) is Blocked else (),
            right_result.obstructions if type(right_result) is Blocked else (),
        )
    elif _response_equal(left_result.value, right_result.value):
        result = Echo(left_result.value)
    else:
        result = Mismatch(left_result.value, right_result.value)
    logger.debug("echo exit outcome=%s", type(result).__name__)
    return result
