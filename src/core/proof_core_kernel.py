"""Trusted inference checker for proof-carrying recurrence judgments."""
from __future__ import annotations

import logging
from typing import NoReturn

from .proof_core_substitution import instantiate_prop, shift_prop
from .proof_core_types import (
    Assume, Bound, CheckedJudgment, CoreProp, CoreTerm, CoreType, EqRefl, EqSym,
    EqTrans, Equal, Forall, ForallElim, ForallIntro, ImpElim, ImpIntro, Implies,
    NativeLaw, NativeLawId, ProofContext, ProofTerm, Pulse, ResonanceIntro,
    Resonates, RuleId, Silence, Stitch, Weave,
)

logger = logging.getLogger(__name__)
RULE_ORDER = tuple(RuleId)
LAW_ORDER = tuple(NativeLawId)


class ProofKernelError(ValueError):
    """A deterministic trusted-kernel rejection."""


def _reject(reason: str) -> NoReturn:
    logger.error("proof core rejected reason=%s", reason)
    raise ProofKernelError(reason)


def _exact_index(value: int, label: str) -> int:
    logger.debug("_exact_index entry label=%s value=%r", label, value)
    if type(value) is not int or value < 0:
        logger.error("_exact_index invalid label=%s value=%r", label, value)
        _reject(f"{label}-must-be-nonnegative-int")
    logger.debug("_exact_index exit value=%d", value)
    return value


def check_term(context: ProofContext, term: CoreTerm) -> CoreType:
    """Infer and validate the type of a recurrence term."""
    logger.debug("check_term entry context=%r term=%r", context, term)
    if type(term) is Bound:
        index = _exact_index(term.index, "bound-index")
        if index >= len(context.term_types):
            _reject("unbound-term-variable")
        result = context.term_types[index]
    elif type(term) is Silence:
        result = CoreType.RECURRENCE
    elif type(term) is Pulse:
        result = check_term(context, term.tail)
    elif type(term) in {Stitch, Weave}:
        left, right = check_term(context, term.left), check_term(context, term.right)
        if left != CoreType.RECURRENCE or right != CoreType.RECURRENCE:
            _reject("term-type-mismatch")
        result = CoreType.RECURRENCE
    else:
        _reject(f"unknown-term:{type(term).__name__}")
    if result != CoreType.RECURRENCE:
        _reject("unsupported-term-type")
    logger.debug("check_term exit result=%s", result.value)
    return result


def check_prop(context: ProofContext, prop: CoreProp) -> None:
    """Validate every term and binder in a proposition."""
    logger.debug("check_prop entry context=%r prop=%r", context, prop)
    if type(prop) is Equal:
        if check_term(context, prop.left) != check_term(context, prop.right):
            _reject("equality-type-mismatch")
    elif type(prop) is Implies:
        check_prop(context, prop.premise)
        check_prop(context, prop.conclusion)
    elif type(prop) is Forall:
        if type(prop.binder_type) is not CoreType:
            _reject("unknown-binder-type")
        check_prop(ProofContext((prop.binder_type,) + context.term_types, context.assumptions), prop.body)
    elif type(prop) is Resonates:
        if check_term(context, prop.factor) != CoreType.RECURRENCE or check_term(context, prop.carrier) != CoreType.RECURRENCE:
            _reject("resonance-type-mismatch")
    else:
        _reject(f"unknown-proposition:{type(prop).__name__}")
    logger.debug("check_prop exit valid")


def _closure(trace: tuple[RuleId, ...]) -> tuple[RuleId, ...]:
    logger.debug("_closure entry trace=%r", trace)
    result = tuple(rule for rule in RULE_ORDER if rule in trace)
    logger.debug("_closure exit result=%r", result)
    return result


def _law_closure(laws: tuple[NativeLawId, ...]) -> tuple[NativeLawId, ...]:
    logger.debug("_law_closure entry laws=%r", laws)
    result = tuple(law for law in LAW_ORDER if law in laws)
    logger.debug("_law_closure exit result=%r", result)
    return result


def _combine(context: ProofContext, conclusion: CoreProp, rule: RuleId, children: tuple[CheckedJudgment, ...] = (), laws: tuple[NativeLawId, ...] = ()) -> CheckedJudgment:
    logger.debug("_combine entry rule=%s children=%d", rule.value, len(children))
    check_prop(context, conclusion)
    trace = tuple(item for child in children for item in child.rule_trace) + (rule,)
    all_laws = tuple(item for child in children for item in child.native_law_closure) + laws
    result = CheckedJudgment(context, conclusion, trace, _closure(trace), _law_closure(all_laws))
    logger.debug("_combine exit conclusion=%r", conclusion)
    return result


def native_law_conclusion(context: ProofContext, law_id: NativeLawId, args: tuple[CoreTerm, ...]) -> Equal:
    """Instantiate one fixed native equality template."""
    logger.debug("native_law_conclusion entry law=%r args=%r", law_id, args)
    if type(law_id) is not NativeLawId:
        _reject("unknown-native-law")
    if type(args) is not tuple:
        _reject("native-law-args-must-be-tuple")
    expected = 2 if law_id is NativeLawId.WEAVE_PULSE else 1
    if len(args) != expected:
        _reject("native-law-bad-arity")
    for arg in args:
        if check_term(context, arg) != CoreType.RECURRENCE:
            _reject("native-law-type-mismatch")
    if law_id is NativeLawId.STITCH_SILENCE_LEFT:
        result = Equal(Stitch(Silence(), args[0]), args[0])
    elif law_id is NativeLawId.STITCH_SILENCE_RIGHT:
        result = Equal(Stitch(args[0], Silence()), args[0])
    elif law_id is NativeLawId.WEAVE_SILENCE_RIGHT:
        result = Equal(Weave(args[0], Silence()), Silence())
    elif law_id is NativeLawId.WEAVE_PULSE:
        result = Equal(Weave(args[0], Pulse(args[1])), Stitch(args[0], Weave(args[0], args[1])))
    elif law_id is NativeLawId.WEAVE_UNIT_RIGHT:
        result = Equal(Weave(args[0], Pulse(Silence())), args[0])
    else:
        _reject("unknown-native-law")
    logger.debug("native_law_conclusion exit result=%r", result)
    return result


def _infer(context: ProofContext, proof: ProofTerm, active: set[int]) -> CheckedJudgment:
    logger.debug("_infer entry context=%r proof=%r", context, proof)
    identity = id(proof)
    if identity in active:
        _reject("circular-proof-term")
    active.add(identity)
    try:
        result = _infer_rule(context, proof, active)
    finally:
        active.remove(identity)
    logger.debug("_infer exit conclusion=%r", result.conclusion)
    return result


def _infer_rule(context: ProofContext, proof: ProofTerm, active: set[int]) -> CheckedJudgment:
    logger.debug("_infer_rule entry proof_type=%s", type(proof).__name__)
    if type(proof) is Assume:
        index = _exact_index(proof.index, "assumption-index")
        if index >= len(context.assumptions):
            _reject("unbound-assumption")
        result = _combine(context, context.assumptions[index], RuleId.ASSUME)
    elif type(proof) is ImpIntro:
        check_prop(context, proof.premise)
        child = _infer(ProofContext(context.term_types, (proof.premise,) + context.assumptions), proof.body, active)
        result = _combine(context, Implies(proof.premise, child.conclusion), RuleId.IMP_INTRO, (child,))
    elif type(proof) is ImpElim:
        function, argument = _infer(context, proof.function, active), _infer(context, proof.argument, active)
        if type(function.conclusion) is not Implies or function.conclusion.premise != argument.conclusion:
            _reject("imp-elim-premise-mismatch")
        result = _combine(context, function.conclusion.conclusion, RuleId.IMP_ELIM, (function, argument))
    elif type(proof) is ForallIntro:
        if type(proof.binder_type) is not CoreType:
            _reject("unknown-binder-type")
        assumptions = tuple(shift_prop(item, 1) for item in context.assumptions)
        child_context = ProofContext((proof.binder_type,) + context.term_types, assumptions)
        child = _infer(child_context, proof.body, active)
        result = _combine(context, Forall(proof.binder_type, child.conclusion), RuleId.FORALL_INTRO, (child,))
    elif type(proof) is ForallElim:
        universal = _infer(context, proof.universal, active)
        if type(universal.conclusion) is not Forall:
            _reject("forall-elim-non-universal")
        if check_term(context, proof.argument) != universal.conclusion.binder_type:
            _reject("forall-elim-type-mismatch")
        conclusion = instantiate_prop(universal.conclusion.body, proof.argument)
        result = _combine(context, conclusion, RuleId.FORALL_ELIM, (universal,))
    elif type(proof) is EqRefl:
        check_term(context, proof.term)
        result = _combine(context, Equal(proof.term, proof.term), RuleId.EQ_REFL)
    elif type(proof) is EqSym:
        child = _infer(context, proof.evidence, active)
        if type(child.conclusion) is not Equal:
            _reject("eq-sym-non-equality")
        result = _combine(context, Equal(child.conclusion.right, child.conclusion.left), RuleId.EQ_SYM, (child,))
    elif type(proof) is EqTrans:
        left, right = _infer(context, proof.left, active), _infer(context, proof.right, active)
        if type(left.conclusion) is not Equal or type(right.conclusion) is not Equal or left.conclusion.right != right.conclusion.left:
            _reject("eq-trans-middle-mismatch")
        result = _combine(context, Equal(left.conclusion.left, right.conclusion.right), RuleId.EQ_TRANS, (left, right))
    elif type(proof) is NativeLaw:
        conclusion = native_law_conclusion(context, proof.law_id, proof.args)
        result = _combine(context, conclusion, RuleId.NATIVE_LAW, laws=(proof.law_id,))
    elif type(proof) is ResonanceIntro:
        check_term(context, proof.factor)
        check_term(context, proof.carrier)
        check_term(context, proof.witness)
        equality = _infer(context, proof.equality, active)
        expected = Equal(Weave(proof.factor, proof.witness), proof.carrier)
        if equality.conclusion != expected:
            _reject("resonance-witness-mismatch")
        result = _combine(context, Resonates(proof.factor, proof.carrier), RuleId.RESONANCE_INTRO, (equality,))
    else:
        _reject(f"unknown-proof-term:{type(proof).__name__}")
    logger.debug("_infer_rule exit rule=%s", result.rule_trace[-1].value)
    return result


def infer_proof(context: ProofContext, proof: ProofTerm) -> CheckedJudgment:
    """Infer a proof conclusion without trusting any caller-declared claim."""
    logger.debug("infer_proof entry context=%r proof=%r", context, proof)
    if type(context) is not ProofContext:
        _reject("invalid-proof-context")
    if type(context.term_types) is not tuple or type(context.assumptions) is not tuple:
        _reject("invalid-context-containers")
    for kind in context.term_types:
        if type(kind) is not CoreType:
            _reject("invalid-context-type")
    for assumption in context.assumptions:
        check_prop(context, assumption)
    result = _infer(context, proof, set())
    logger.debug("infer_proof exit conclusion=%r", result.conclusion)
    return result
