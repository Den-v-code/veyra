"""Deterministic encodings and support closure for observer proofs."""
from __future__ import annotations

import json
import logging
from typing import NoReturn

from .observer_core_codec import canonical_observer_bytes
from .observer_core_semantics import MAX_OBSERVER_DEPTH, MAX_OBSERVER_NODES, validate_closed_recurrence
from .observer_core_proof_types import (
    Echoes, EmbeddedR7, Obstructed, ObserverConclusion, ObserverLawId,
    ObserverRuleId, ObserverSupportId,
)
from .observer_core_types import (
    Blocked, DomainBlocked, Echo, Mark, MarkValue, Mismatch, ObstructionCode,
    ObserverObstruction, PairValue, PathStep, Ready, RecurrenceValue,
    ResponseValue,
)
from .proof_core_codec import context_data, prop_data, term_data
from .proof_core_kernel import check_prop
from .proof_core_types import (
    Bound, CheckedJudgment, CoreType, Equal, Forall, Implies, NativeLawId,
    ProofContext, Pulse, Resonates, RuleId, Silence, Stitch, Weave,
)

logger = logging.getLogger(__name__)
SUPPORT_ORDER = tuple(ObserverSupportId)
MAX_OBSTRUCTIONS, MAX_OBSTRUCTION_PATH_STEPS = MAX_OBSERVER_NODES, MAX_OBSERVER_DEPTH
_CORE_NODES = frozenset({Bound, Silence, Pulse, Stitch, Weave, Equal, Implies, Forall, Resonates})


def _reject(reason: str) -> NoReturn:
    logger.error("observer_core_support rejected reason=%s", reason)
    raise ValueError(reason)


def _exact_obstructions(
    items: object, reason: str, allow_empty: bool,
) -> tuple[ObserverObstruction, ...]:
    logger.debug("_exact_obstructions entry type=%s", type(items).__name__)
    if type(items) is not tuple:
        _reject(reason)
    count = len(items)
    if count > MAX_OBSTRUCTIONS or (not allow_empty and count == 0):
        _reject(reason)
    if any(type(item) is not ObserverObstruction for item in items):
        _reject(reason)
    seen: set[tuple[PathStep, ...]] = set()
    for item in items:
        obstruction_data(item)
        if item.path in seen:
            _reject(reason)
        seen.add(item.path)
    logger.debug("_exact_obstructions exit count=%d", count)
    return items


def observer_data(observer: object) -> dict[str, object]:
    """Return the validated canonical observer envelope as data."""
    logger.debug("observer_data entry type=%s", type(observer).__name__)
    raw = json.loads(canonical_observer_bytes(observer))
    if type(raw) is not dict:
        _reject("invalid-canonical-observer")
    logger.debug("observer_data exit")
    return raw


def obstruction_data(item: ObserverObstruction) -> dict[str, object]:
    """Encode one exact native obstruction."""
    logger.debug("obstruction_data entry type=%s", type(item).__name__)
    if (
        type(item) is not ObserverObstruction
        or type(item.code) is not ObstructionCode or type(item.path) is not tuple
        or not item.path or len(item.path) > MAX_OBSTRUCTION_PATH_STEPS
        or item.path[-1] is not PathStep.APPLY_TAIL
        or any(type(step) is not PathStep for step in item.path)
    ):
        _reject("invalid-obstruction")
    result = {"code": item.code.value, "path": [step.value for step in item.path]}
    logger.debug("obstruction_data exit code=%s", item.code.value)
    return result


def response_data(value: ResponseValue) -> dict[str, object]:
    """Encode one branded observer response without Python equality hooks."""
    logger.debug("response_data entry type=%s", type(value).__name__)
    stack: list[tuple[bool, object, int]] = [(False, value, 0)]
    active: set[int] = set()
    values: list[dict[str, object]] = []
    nodes = 0
    while stack:
        exiting, node, depth = stack.pop()
        identity = id(node)
        if exiting:
            active.remove(identity)
            if type(node) is RecurrenceValue:
                validate_closed_recurrence(node.recurrence)
                values.append({"tag": "recurrence", "term": term_data(node.recurrence)})
            elif type(node) is MarkValue:
                if type(node.mark) is not Mark:
                    _reject("invalid-mark-value")
                values.append({"tag": "mark", "mark": node.mark.value})
            else:
                right, left = values.pop(), values.pop()
                values.append({"tag": "pair", "left": left, "right": right})
            continue
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH:
            _reject("response-resource-limit")
        if identity in active:
            _reject("circular-response-value")
        if type(node) not in {RecurrenceValue, MarkValue, PairValue}:
            _reject("invalid-response-value")
        active.add(identity)
        stack.append((True, node, depth))
        if type(node) is PairValue:
            stack.append((False, node.right, depth + 1))
            stack.append((False, node.left, depth + 1))
    if len(values) != 1:
        _reject("invalid-response-shape")
    result = values[0]
    logger.debug("response_data exit tag=%s", result["tag"])
    return result


def _preflight_r7_payload(context: object, conclusion: object) -> ProofContext:
    """Bound and type-check exact R7 data before recursive codec access."""
    logger.debug("_preflight_r7_payload entry context_type=%s", type(context).__name__)
    if type(context) is not ProofContext:
        _reject("invalid-r7-outcome-context")
    term_types, assumptions = context.term_types, context.assumptions
    if (
        type(term_types) is not tuple or type(assumptions) is not tuple
        or len(term_types) > MAX_OBSERVER_NODES or len(assumptions) > MAX_OBSERVER_NODES
        or any(type(item) is not CoreType for item in term_types)
    ):
        _reject("invalid-r7-outcome-context")
    propositions = assumptions + (conclusion,)
    stack = [(False, item, 0) for item in propositions]
    active: set[int] = set()
    nodes = 0
    while stack:
        exiting, node, depth = stack.pop()
        identity, kind = id(node), type(node)
        if exiting:
            active.remove(identity)
            continue
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH or identity in active:
            _reject("invalid-r7-outcome-payload")
        if kind not in _CORE_NODES:
            _reject("invalid-r7-outcome-payload")
        active.add(identity)
        stack.append((True, node, depth))
        if kind is Bound:
            if type(node.index) is not int or node.index < 0:
                _reject("invalid-r7-outcome-payload")
            children = ()
        elif kind is Pulse:
            children = (node.tail,)
        elif kind in {Stitch, Weave, Equal, Implies, Resonates}:
            children = (node.left, node.right) if kind in {Stitch, Weave, Equal} else (
                (node.premise, node.conclusion) if kind is Implies else (node.factor, node.carrier)
            )
        elif kind is Forall:
            if type(node.binder_type) is not CoreType:
                _reject("invalid-r7-outcome-payload")
            children = (node.body,)
        else:
            children = ()
        stack.extend((False, child, depth + 1) for child in reversed(children))
    for proposition in propositions:
        check_prop(context, proposition)
    logger.debug("_preflight_r7_payload exit nodes=%d", nodes)
    return context


def _r7_outcome_parts(outcome: CheckedJudgment) -> tuple[ProofContext, tuple[RuleId, ...], tuple[NativeLawId, ...]]:
    """Preflight exact bounded kernel metadata before nested context access."""
    logger.debug("_r7_outcome_parts entry")
    context = _preflight_r7_payload(outcome.context, outcome.conclusion)
    trace, rules, laws = outcome.rule_trace, outcome.rule_closure, outcome.native_law_closure
    if (
        type(trace) is not tuple or not trace or len(trace) > MAX_OBSERVER_NODES
        or type(rules) is not tuple or type(laws) is not tuple
        or len(rules) > len(RuleId) or len(laws) > len(NativeLawId)
        or any(type(item) is not RuleId for item in trace + rules)
        or any(type(item) is not NativeLawId for item in laws)
        or rules != tuple(item for item in RuleId if item in trace)
        or laws != tuple(item for item in NativeLawId if item in laws)
        or bool(laws) != (RuleId.NATIVE_LAW in trace)
    ):
        _reject("invalid-r7-outcome-closures")
    logger.debug("_r7_outcome_parts exit trace=%d rules=%d laws=%d", len(trace), len(rules), len(laws))
    return context, rules, laws


def outcome_data(outcome: object) -> dict[str, object]:
    """Encode only kernel-produced R7, observation, or echo outcomes."""
    logger.debug("outcome_data entry type=%s", type(outcome).__name__)
    if type(outcome) is CheckedJudgment:
        context, rules, laws = _r7_outcome_parts(outcome)
        result = {
            "tag": "r7", "context": context_data(context),
            "conclusion": prop_data(outcome.conclusion),
            "rules": [item.value for item in rules], "laws": [item.value for item in laws],
        }
    elif type(outcome) in {Ready, Echo}:
        result = {"tag": "ready" if type(outcome) is Ready else "echo", "value": response_data(outcome.value)}
    elif type(outcome) is Blocked:
        items = _exact_obstructions(outcome.obstructions, "invalid-blocked-obstructions", False)
        result = {"tag": "blocked", "obstructions": [obstruction_data(item) for item in items]}
    elif type(outcome) is Mismatch:
        left, right = response_data(outcome.left), response_data(outcome.right)
        if left == right:
            _reject("invalid-mismatch")
        result = {"tag": "mismatch", "left": left, "right": right}
    elif type(outcome) is DomainBlocked:
        left = _exact_obstructions(outcome.left_obstructions, "invalid-left-obstructions", True)
        right = _exact_obstructions(outcome.right_obstructions, "invalid-right-obstructions", True)
        if (not left and not right) or len(left) + len(right) > MAX_OBSTRUCTIONS:
            _reject("invalid-domain-obstructions")
        result = {
            "tag": "domain-blocked",
            "left": [obstruction_data(item) for item in left],
            "right": [obstruction_data(item) for item in right],
        }
    else:
        _reject("invalid-observer-outcome")
    logger.debug("outcome_data exit tag=%s", result["tag"])
    return result


def conclusion_data(conclusion: ObserverConclusion) -> dict[str, object]:
    """Encode one exact inferred observer conclusion."""
    logger.debug("conclusion_data entry type=%s", type(conclusion).__name__)
    if type(conclusion) is EmbeddedR7:
        result = {"tag": "embedded-r7", "proposition": prop_data(conclusion.proposition)}
    elif type(conclusion) is Echoes:
        result = {
            "tag": "echoes", "observer": observer_data(conclusion.observer),
            "left": term_data(conclusion.left), "right": term_data(conclusion.right),
        }
    elif type(conclusion) is Obstructed:
        result = {
            "tag": "obstructed", "observer": observer_data(conclusion.observer),
            "recurrence": term_data(conclusion.recurrence),
        }
    else:
        _reject("invalid-observer-conclusion")
    logger.debug("conclusion_data exit tag=%s", result["tag"])
    return result


def paths_data(paths: tuple[tuple[object, ...], ...]) -> list[list[str]]:
    """Encode replay-derived obstruction paths in their exact order."""
    logger.debug("paths_data entry type=%s", type(paths).__name__)
    if type(paths) is not tuple:
        _reject("invalid-obstruction-paths")
    if len(paths) > MAX_OBSTRUCTIONS or any(type(path) is not tuple for path in paths):
        _reject("invalid-obstruction-paths")
    if any(not path or len(path) > MAX_OBSTRUCTION_PATH_STEPS or path[-1] is not PathStep.APPLY_TAIL for path in paths):
        _reject("invalid-obstruction-paths")
    if any(type(step) is not PathStep for path in paths for step in path):
        _reject("invalid-obstruction-paths")
    if len(set(paths)) != len(paths):
        _reject("invalid-obstruction-paths")
    result = [[step.value for step in path] for path in paths]
    logger.debug("paths_data exit count=%d", len(result))
    return result


def support_closure(
    rules: tuple[ObserverRuleId, ...], laws: tuple[ObserverLawId, ...],
) -> tuple[ObserverSupportId, ...]:
    """Derive support identifiers solely from replayed rule/law closures."""
    logger.debug("support_closure entry rule_type=%s law_type=%s", type(rules).__name__, type(laws).__name__)
    if (
        type(rules) is not tuple or type(laws) is not tuple
        or len(rules) > len(ObserverRuleId) or len(laws) > len(ObserverLawId)
        or any(type(item) is not ObserverRuleId for item in rules)
        or any(type(item) is not ObserverLawId for item in laws)
        or rules != tuple(item for item in ObserverRuleId if item in rules)
        or laws != tuple(item for item in ObserverLawId if item in laws)
    ):
        _reject("invalid-support-input")
    chosen: set[ObserverSupportId] = {ObserverSupportId.OBSERVER_CODEC}
    if ObserverRuleId.EMBED_R7 in rules:
        chosen.add(ObserverSupportId.R7_KERNEL)
    if any(rule is not ObserverRuleId.EMBED_R7 for rule in rules):
        chosen.add(ObserverSupportId.OBSERVER_SEMANTICS)
    if ObserverLawId.EQUALITY_READY_ECHO in laws:
        chosen.add(ObserverSupportId.STRUCTURAL_TOTALITY)
    if ObserverLawId.CREST_PULSE_ECHO in laws:
        chosen.add(ObserverSupportId.CREST_PULSE_LAW)
    if ObserverLawId.TAIL_SILENCE_OBSTRUCTION in laws:
        chosen.add(ObserverSupportId.TAIL_SILENCE_LAW)
    result = tuple(item for item in SUPPORT_ORDER if item in chosen)
    logger.debug("support_closure exit result=%r", result)
    return result
