"""Validation and diagnostic serialization for the R12.2 intrinsic VAM IR."""

from __future__ import annotations

import logging
from typing import NoReturn

from .intrinsic_ir_types import (
    IntrinsicAnchorIR,
    IntrinsicBlockedIR,
    IntrinsicDomainBlockedIR,
    IntrinsicEchoIR,
    IntrinsicIR,
    IntrinsicMarkIR,
    IntrinsicMarkValueIR,
    IntrinsicMismatchIR,
    IntrinsicObstructionCodeIR,
    IntrinsicObstructionIR,
    IntrinsicPairValueIR,
    IntrinsicPathStepIR,
    IntrinsicReadyIR,
    IntrinsicRecurrenceIR,
    IntrinsicRecurrenceValueIR,
    IntrinsicTactIR,
)

logger = logging.getLogger(__name__)
INTRINSIC_IR_SCHEMA = "veyra.vam.intrinsic-ir.r12.2.v1"
MAX_INTRINSIC_NODES = 4096
MAX_INTRINSIC_DEPTH = 128
MAX_RECURRENCE_TACTS = 2047
MAX_OBSTRUCTIONS = 2048
MAX_OBSTRUCTION_PATH = 128
_NODE_TYPES = {
    IntrinsicAnchorIR,
    IntrinsicTactIR,
    IntrinsicMarkIR,
    IntrinsicRecurrenceIR,
    IntrinsicRecurrenceValueIR,
    IntrinsicMarkValueIR,
    IntrinsicPairValueIR,
    IntrinsicObstructionIR,
    IntrinsicReadyIR,
    IntrinsicBlockedIR,
    IntrinsicEchoIR,
    IntrinsicMismatchIR,
    IntrinsicDomainBlockedIR,
}
_RESPONSE_TYPES = {
    IntrinsicRecurrenceValueIR,
    IntrinsicMarkValueIR,
    IntrinsicPairValueIR,
}


class IntrinsicIRError(ValueError):
    """A stable fail-closed R12.2 validation rejection."""


def _reject(reason: str) -> NoReturn:
    """Log and raise one intrinsic-IR rejection."""
    logger.error("intrinsic IR rejected reason=%s", reason)
    raise IntrinsicIRError(reason)


def silence_ir() -> IntrinsicRecurrenceIR:
    """Construct the exact anchored R9 silence image."""
    logger.debug("silence_ir entry")
    result = IntrinsicRecurrenceIR((), IntrinsicAnchorIR())
    logger.debug("silence_ir exit")
    return result


def pulse_ir(tail: object) -> IntrinsicRecurrenceIR:
    """Prepend one fixed successor tact to an exact recurrence image."""
    logger.debug("pulse_ir entry type=%s", type(tail).__name__)
    validate_intrinsic_ir(tail)
    if type(tail) is not IntrinsicRecurrenceIR:
        _reject("pulse-tail-not-recurrence")
    if len(tail.tacts) >= MAX_RECURRENCE_TACTS:
        _reject("recurrence-resource-limit")
    result = IntrinsicRecurrenceIR((IntrinsicTactIR(),) + tail.tacts, None)
    logger.debug("pulse_ir exit tacts=%d", len(result.tacts))
    return result


def crest_mark_ir(value: object) -> IntrinsicMarkIR:
    """Return the exact silent/pulse crest mark for one recurrence IR."""
    logger.debug("crest_mark_ir entry type=%s", type(value).__name__)
    validate_intrinsic_ir(value)
    if type(value) is not IntrinsicRecurrenceIR:
        _reject("crest-source-not-recurrence")
    result = IntrinsicMarkIR.SILENT if not value.tacts else IntrinsicMarkIR.PULSE
    logger.debug("crest_mark_ir exit mark=%s", result.value)
    return result


def _valid_obstruction_path(path: tuple[IntrinsicPathStepIR, ...]) -> bool:
    """Recognize the closed R11 path grammar: pair*, crest?, tail+."""
    logger.debug("_valid_obstruction_path entry steps=%d", len(path))
    index = 0
    while index < len(path) and path[index] in {
        IntrinsicPathStepIR.PAIR_LEFT,
        IntrinsicPathStepIR.PAIR_RIGHT,
    }:
        index += 1
    if index < len(path) and path[index] is IntrinsicPathStepIR.APPLY_CREST:
        index += 1
    tail_start = index
    while index < len(path) and path[index] is IntrinsicPathStepIR.APPLY_TAIL:
        index += 1
    result = index == len(path) and index > tail_start
    logger.debug("_valid_obstruction_path exit result=%s", result)
    return result


def _obstruction_tuple(items: object, allow_empty: bool) -> tuple[IntrinsicObstructionIR, ...]:
    """Validate one bounded exact obstruction tuple."""
    logger.debug("_obstruction_tuple entry type=%s allow_empty=%s", type(items).__name__, allow_empty)
    if type(items) is not tuple or len(items) > MAX_OBSTRUCTIONS or (not items and not allow_empty):
        _reject("invalid-obstruction-set")
    if any(type(item) is not IntrinsicObstructionIR for item in items):
        _reject("invalid-obstruction-set")
    paths: set[tuple[IntrinsicPathStepIR, ...]] = set()
    for item in items:
        if (
            type(item.code) is not IntrinsicObstructionCodeIR
            or type(item.path) is not tuple
            or not item.path
            or len(item.path) > MAX_OBSTRUCTION_PATH
            or any(type(step) is not IntrinsicPathStepIR for step in item.path)
            or not _valid_obstruction_path(item.path)
            or item.path in paths
        ):
            _reject("invalid-obstruction")
        paths.add(item.path)
    logger.debug("_obstruction_tuple exit count=%d", len(items))
    return items


def _children(node: object) -> tuple[object, ...]:
    """Return exact child order while validating local scalar/container fields."""
    logger.debug("_children entry type=%s", type(node).__name__)
    if type(node) is IntrinsicRecurrenceIR:
        if (
            type(node.tacts) is not tuple
            or len(node.tacts) > MAX_RECURRENCE_TACTS
            or any(type(item) is not IntrinsicTactIR for item in node.tacts)
            or (not node.tacts and type(node.anchor) is not IntrinsicAnchorIR)
            or (bool(node.tacts) and node.anchor is not None)
        ):
            _reject("invalid-recurrence-ir")
        result = node.tacts + (() if node.anchor is None else (node.anchor,))
    elif type(node) in {IntrinsicAnchorIR, IntrinsicTactIR, IntrinsicMarkIR}:
        result = ()
    elif type(node) is IntrinsicRecurrenceValueIR:
        if type(node.recurrence) is not IntrinsicRecurrenceIR:
            _reject("invalid-recurrence-response")
        result = (node.recurrence,)
    elif type(node) is IntrinsicMarkValueIR:
        if type(node.mark) is not IntrinsicMarkIR:
            _reject("invalid-mark-ir")
        result = ()
    elif type(node) is IntrinsicPairValueIR:
        if type(node.left) not in _RESPONSE_TYPES or type(node.right) not in _RESPONSE_TYPES:
            _reject("invalid-pair-response")
        result = (node.left, node.right)
    elif type(node) is IntrinsicObstructionIR:
        _obstruction_tuple((node,), False)
        result = ()
    elif type(node) in {IntrinsicReadyIR, IntrinsicEchoIR}:
        if type(node.value) not in _RESPONSE_TYPES:
            _reject("invalid-response-wrapper")
        result = (node.value,)
    elif type(node) is IntrinsicBlockedIR:
        result = _obstruction_tuple(node.obstructions, False)
    elif type(node) is IntrinsicMismatchIR:
        if type(node.left) not in _RESPONSE_TYPES or type(node.right) not in _RESPONSE_TYPES:
            _reject("invalid-mismatch-response")
        result = (node.left, node.right)
    elif type(node) is IntrinsicDomainBlockedIR:
        left = _obstruction_tuple(node.left, True)
        right = _obstruction_tuple(node.right, True)
        if not left and not right or len(left) + len(right) > MAX_OBSTRUCTIONS:
            _reject("invalid-domain-obstruction-set")
        result = left + right
    else:
        _reject("invalid-intrinsic-node")
    logger.debug("_children exit count=%d", len(result))
    return result


def _render(node: object, children: list[dict[str, object]]) -> dict[str, object]:
    """Render one locally validated node from ordered rendered children."""
    logger.debug("_render entry type=%s children=%d", type(node).__name__, len(children))
    if type(node) is IntrinsicAnchorIR:
        result = {"tag": "anchor", "name": "intrinsic-origin", "mark": "intrinsic-origin"}
    elif type(node) is IntrinsicTactIR:
        result = {"tag": "tact", "start": "intrinsic-origin", "end": "intrinsic-origin", "mark": "intrinsic-successor"}
    elif type(node) is IntrinsicMarkIR:
        result = {"tag": "mark", "value": node.value}
    elif type(node) is IntrinsicRecurrenceIR:
        count = len(node.tacts)
        result = {"tag": "recurrence", "tacts": children[:count], "anchor": None if node.anchor is None else children[-1]}
    elif type(node) is IntrinsicRecurrenceValueIR:
        result = {"tag": "recurrence-value", "recurrence": children[0]}
    elif type(node) is IntrinsicMarkValueIR:
        result = {"tag": "mark-value", "mark": node.mark.value}
    elif type(node) is IntrinsicPairValueIR:
        result = {"tag": "pair-value", "left": children[0], "right": children[1]}
    elif type(node) is IntrinsicObstructionIR:
        result = {"tag": "obstruction", "code": node.code.value, "path": [step.value for step in node.path]}
    elif type(node) is IntrinsicReadyIR:
        result = {"tag": "ready", "value": children[0]}
    elif type(node) is IntrinsicBlockedIR:
        result = {"tag": "blocked", "obstructions": children}
    elif type(node) is IntrinsicEchoIR:
        result = {"tag": "echo", "value": children[0]}
    elif type(node) is IntrinsicMismatchIR:
        if children[0] == children[1]:
            _reject("invalid-mismatch")
        if _response_kind(children[0]) != _response_kind(children[1]):
            _reject("invalid-mismatch-kind")
        result = {"tag": "mismatch", "left": children[0], "right": children[1]}
    elif type(node) is IntrinsicDomainBlockedIR:
        split = len(node.left)
        result = {"tag": "domain-blocked", "left": children[:split], "right": children[split:]}
    else:
        _reject("invalid-intrinsic-node")
    logger.debug("_render exit tag=%s", result["tag"])
    return result


def _response_kind(value: dict[str, object]) -> tuple[object, ...]:
    """Derive one response kind from already validated diagnostic data."""
    logger.debug("_response_kind entry tag=%s", value.get("tag"))
    tag = value.get("tag")
    if tag == "recurrence-value":
        result = ("recurrence",)
    elif tag == "mark-value":
        result = ("mark",)
    elif tag == "pair-value":
        result = ("pair", _response_kind(value["left"]), _response_kind(value["right"]))  # type: ignore[arg-type]
    else:
        _reject("invalid-response-kind")
    logger.debug("_response_kind exit kind=%s", result[0])
    return result


def intrinsic_ir_data(value: object) -> dict[str, object]:
    """Validate and serialize one IR value as diagnostic, non-evidence data."""
    logger.debug("intrinsic_ir_data entry type=%s", type(value).__name__)
    stack: list[tuple[bool, object, int, int]] = [(False, value, 0, 0)]
    active: set[int] = set()
    rendered: list[dict[str, object]] = []
    nodes = 0
    while stack:
        exiting, node, depth, child_count = stack.pop()
        identity = id(node)
        if exiting:
            active.remove(identity)
            children = rendered[-child_count:] if child_count else []
            if child_count:
                del rendered[-child_count:]
            rendered.append(_render(node, children))
            continue
        nodes += 1
        if nodes > MAX_INTRINSIC_NODES or depth > MAX_INTRINSIC_DEPTH:
            _reject("intrinsic-resource-limit")
        if identity in active:
            _reject("circular-intrinsic-value")
        if type(node) not in _NODE_TYPES:
            _reject("invalid-intrinsic-node")
        children = _children(node)
        active.add(identity)
        stack.append((True, node, depth, len(children)))
        stack.extend((False, child, depth + 1, 0) for child in reversed(children))
    if len(rendered) != 1:
        _reject("invalid-intrinsic-shape")
    result = {"schema": INTRINSIC_IR_SCHEMA, "value": rendered[0]}
    logger.debug("intrinsic_ir_data exit nodes=%d tag=%s", nodes, rendered[0]["tag"])
    return result


def validate_intrinsic_ir(value: object) -> IntrinsicIR:
    """Return an exact value after full bounded validation."""
    logger.debug("validate_intrinsic_ir entry type=%s", type(value).__name__)
    intrinsic_ir_data(value)
    logger.debug("validate_intrinsic_ir exit")
    return value
