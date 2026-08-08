"""Conservative proof checker joining unchanged R7 evidence to observers."""

from __future__ import annotations

import logging
from typing import NoReturn

from .observer_core_proof_types import (
    CrestPulseEcho,
    Echoes,
    EmbedR7,
    EmbeddedR7,
    EqualityReadyEcho,
    Obstructed,
    ObserverCheckedJudgment,
    ObserverLawId,
    ObserverProof,
    ObserverRuleId,
    TailSilenceObstruction,
)
from .observer_core_semantics import ObserverCoreError, echo, infer_observer_kind, observe, validate_closed_recurrence
from .observer_core_support import support_closure
from .observer_core_types import (
    Apply,
    Blocked,
    DomainBlocked,
    Echo,
    Input,
    Mark,
    MarkValue,
    ObserverExpr,
    ObstructionCode,
    Pair,
    PathStep,
    PrimitiveId,
)
from .proof_core_kernel import ProofKernelError, check_prop, check_term, infer_proof
from .proof_core_types import (
    Assume, CheckedJudgment, CoreType, EqRefl, EqSym, EqTrans, Equal, ForallElim, ForallIntro, ImpElim, ImpIntro,
    NativeLaw, ProofContext, Pulse, ResonanceIntro, Silence,
)

logger = logging.getLogger(__name__)
RULE_ORDER = tuple(ObserverRuleId)
LAW_ORDER = tuple(ObserverLawId)
MAX_OBSERVER_PROOF_DEPTH = 128
MAX_EMBEDDED_R7_PROOF_DEPTH = 128
MAX_EMBEDDED_R7_PROOF_NODES = 2048
_R7_PROOF_TYPES = frozenset(
    {Assume, ImpIntro, ImpElim, ForallIntro, ForallElim, EqRefl, EqSym, EqTrans, NativeLaw, ResonanceIntro}
)


class ObserverProofError(ValueError):
    """A deterministic conservative observer-proof rejection."""


def _reject(reason: str) -> NoReturn:
    logger.error("observer proof rejected reason=%s", reason)
    raise ObserverProofError(reason)


def crest_observer() -> Apply:
    """Return the only observer admitted by the crest-pulse law."""
    logger.debug("crest_observer entry")
    result = Apply(PrimitiveId.CREST, Input())
    logger.debug("crest_observer exit")
    return result


def tail_observer() -> Apply:
    """Return the only observer admitted by the tail-silence law."""
    logger.debug("tail_observer entry")
    result = Apply(PrimitiveId.TAIL, Input())
    logger.debug("tail_observer exit")
    return result


def is_structurally_total(observer: ObserverExpr) -> bool:
    """Decide totality structurally: a well-kinded AST contains no tail."""
    logger.debug("is_structurally_total entry type=%s", type(observer).__name__)
    infer_observer_kind(observer)
    stack: list[object] = [observer]
    result = True
    while stack:
        node = stack.pop()
        if type(node) is Apply:
            if node.primitive is PrimitiveId.TAIL:
                result = False
                break
            stack.append(node.child)
        elif type(node) is Pair:
            stack.extend((node.right, node.left))
    logger.debug("is_structurally_total exit result=%s", result)
    return result


def _paths(outcome: object) -> tuple[tuple[PathStep, ...], ...]:
    logger.debug("_paths entry type=%s", type(outcome).__name__)
    if type(outcome) is Blocked:
        result = tuple(item.path for item in outcome.obstructions)
    elif type(outcome) is DomainBlocked:
        result = tuple(item.path for item in outcome.left_obstructions + outcome.right_obstructions)
    else:
        result = ()
    logger.debug("_paths exit count=%d", len(result))
    return result


def _closed(term: object, label: str) -> None:
    logger.debug("_closed entry label=%s type=%s", label, type(term).__name__)
    try:
        validate_closed_recurrence(term)
    except ObserverCoreError:
        logger.error("_closed rejected label=%s", label)
        _reject(f"{label}-must-be-closed-recurrence-value")
    logger.debug("_closed exit label=%s", label)


def _validate_context(context: ProofContext) -> None:
    logger.debug("_validate_context entry type=%s", type(context).__name__)
    if type(context) is not ProofContext:
        _reject("invalid-proof-context")
    if type(context.term_types) is not tuple or type(context.assumptions) is not tuple:
        _reject("invalid-context-containers")
    if any(type(item) is not CoreType for item in context.term_types):
        _reject("invalid-context-type")
    for assumption in context.assumptions:
        check_prop(context, assumption)
    logger.debug("_validate_context exit valid")


def _preflight_r7_proof(proof: object) -> None:
    """Bound exact R7 proof structure before entering its recursive kernel."""
    logger.debug("_preflight_r7_proof entry proof=%s", type(proof).__name__)
    stack: list[tuple[bool, object, int]] = [(False, proof, 0)]
    active: set[int] = set()
    nodes = 0
    while stack:
        exiting, node, depth = stack.pop()
        identity = id(node)
        if exiting:
            active.remove(identity)
            continue
        nodes += 1
        if depth > MAX_EMBEDDED_R7_PROOF_DEPTH or nodes > MAX_EMBEDDED_R7_PROOF_NODES:
            _reject("embedded-r7-proof-resource-limit")
        if identity in active:
            _reject("circular-embedded-r7-proof")
        kind = type(node)
        if kind not in _R7_PROOF_TYPES:
            _reject(f"unknown-embedded-r7-proof:{kind.__name__}")
        active.add(identity)
        stack.append((True, node, depth))
        if kind in {ImpIntro, ForallIntro}:
            children = (node.body,)
        elif kind is ImpElim:
            children = (node.function, node.argument)
        elif kind is ForallElim:
            children = (node.universal,)
        elif kind is EqSym:
            children = (node.evidence,)
        elif kind is EqTrans:
            children = (node.left, node.right)
        elif kind is ResonanceIntro:
            children = (node.equality,)
        else:
            children = ()
        stack.extend((False, child, depth + 1) for child in reversed(children))
    logger.debug("_preflight_r7_proof exit nodes=%d", nodes)


def _closure(trace: tuple[ObserverRuleId, ...]) -> tuple[ObserverRuleId, ...]:
    logger.debug("_closure entry trace=%r", trace)
    result = tuple(item for item in RULE_ORDER if item in trace)
    logger.debug("_closure exit result=%r", result)
    return result


def _law_closure(laws: tuple[ObserverLawId, ...]) -> tuple[ObserverLawId, ...]:
    logger.debug("_law_closure entry laws=%r", laws)
    result = tuple(item for item in LAW_ORDER if item in laws)
    logger.debug("_law_closure exit result=%r", result)
    return result


def _combine(
    context: ProofContext, conclusion: object, outcome: object, rule: ObserverRuleId,
    children: tuple[ObserverCheckedJudgment, ...] = (),
    laws: tuple[ObserverLawId, ...] = (),
) -> ObserverCheckedJudgment:
    logger.debug("_combine entry rule=%s children=%d", rule.value, len(children))
    trace = tuple(item for child in children for item in child.rule_trace) + (rule,)
    all_laws = tuple(item for child in children for item in child.observer_law_closure) + laws
    rules, law_set = _closure(trace), _law_closure(all_laws)
    r7_rules = tuple(dict.fromkeys(item for child in children for item in child.r7_rule_closure))
    r7_laws = tuple(dict.fromkeys(item for child in children for item in child.r7_native_law_closure))
    if type(outcome) is CheckedJudgment:
        r7_rules = tuple(item.value for item in outcome.rule_closure)
        r7_laws = tuple(item.value for item in outcome.native_law_closure)
    result = ObserverCheckedJudgment(
        context, conclusion, outcome, _paths(outcome), trace, rules, law_set,
        r7_rules, r7_laws, support_closure(rules, law_set),
    )
    logger.debug("_combine exit conclusion=%s", type(conclusion).__name__)
    return result


def _infer_rule(
    context: ProofContext, proof: ObserverProof, active: set[int], depth: int,
) -> ObserverCheckedJudgment:
    logger.debug("_infer_rule entry proof=%s", type(proof).__name__)
    if type(proof) is EmbedR7:
        _preflight_r7_proof(proof.evidence)
        outcome = infer_proof(context, proof.evidence)
        result = _combine(context, EmbeddedR7(outcome.conclusion), outcome, ObserverRuleId.EMBED_R7)
    elif type(proof) is EqualityReadyEcho:
        child = _infer(context, proof.equality, active, depth + 1)
        if type(child.conclusion) is not EmbeddedR7 or type(child.conclusion.proposition) is not Equal:
            _reject("equality-ready-echo-needs-r7-equality")
        if not is_structurally_total(proof.observer):
            _reject("equality-ready-echo-needs-total-observer")
        equality = child.conclusion.proposition
        _closed(equality.left, "equality-left")
        _closed(equality.right, "equality-right")
        outcome = echo(proof.observer, equality.left, equality.right)
        if type(outcome) is not Echo:
            _reject("equality-ready-echo-replay-not-echo")
        result = _combine(
            context, Echoes(proof.observer, equality.left, equality.right), outcome,
            ObserverRuleId.EQUALITY_READY_ECHO, (child,), (ObserverLawId.EQUALITY_READY_ECHO,),
        )
    elif type(proof) is CrestPulseEcho:
        check_term(context, proof.left_tail)
        check_term(context, proof.right_tail)
        _closed(proof.left_tail, "crest-left-tail")
        _closed(proof.right_tail, "crest-right-tail")
        left, right, observer = Pulse(proof.left_tail), Pulse(proof.right_tail), crest_observer()
        outcome = echo(observer, left, right)
        if type(outcome) is not Echo or type(outcome.value) is not MarkValue or outcome.value.mark is not Mark.PULSE:
            _reject("crest-pulse-law-replay-mismatch")
        result = _combine(
            context, Echoes(observer, left, right), outcome, ObserverRuleId.CREST_PULSE_ECHO,
            laws=(ObserverLawId.CREST_PULSE_ECHO,),
        )
    elif type(proof) is TailSilenceObstruction:
        observer, recurrence = tail_observer(), Silence()
        outcome = observe(observer, recurrence)
        expected_path = (PathStep.APPLY_TAIL,)
        if (
            type(outcome) is not Blocked
            or len(outcome.obstructions) != 1
            or outcome.obstructions[0].code is not ObstructionCode.TAIL_OF_SILENCE
            or outcome.obstructions[0].path != expected_path
        ):
            _reject("tail-silence-law-replay-mismatch")
        result = _combine(
            context, Obstructed(observer, recurrence), outcome, ObserverRuleId.TAIL_SILENCE_OBSTRUCTION,
            laws=(ObserverLawId.TAIL_SILENCE_OBSTRUCTION,),
        )
    else:
        _reject(f"unknown-observer-proof:{type(proof).__name__}")
    logger.debug("_infer_rule exit rule=%s", result.rule_trace[-1].value)
    return result


def _infer(
    context: ProofContext, proof: ObserverProof, active: set[int], depth: int,
) -> ObserverCheckedJudgment:
    logger.debug("_infer entry proof=%s", type(proof).__name__)
    if depth > MAX_OBSERVER_PROOF_DEPTH:
        _reject("observer-proof-resource-limit")
    identity = id(proof)
    if identity in active:
        _reject("circular-observer-proof")
    active.add(identity)
    try:
        result = _infer_rule(context, proof, active, depth)
    finally:
        active.remove(identity)
    logger.debug("_infer exit conclusion=%s", type(result.conclusion).__name__)
    return result


def infer_observer_proof(context: ProofContext, proof: ObserverProof) -> ObserverCheckedJudgment:
    """Replay an observer proof without trusting any declared claim or outcome."""
    logger.debug("infer_observer_proof entry context=%r proof=%s", context, type(proof).__name__)
    _validate_context(context)
    try:
        result = _infer(context, proof, set(), 0)
    except ProofKernelError:
        logger.error("infer_observer_proof rejected by r7 kernel")
        raise
    logger.debug("infer_observer_proof exit conclusion=%s", type(result.conclusion).__name__)
    return result
