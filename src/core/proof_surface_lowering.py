"""Capture-safe named-syntax lowering into the R7 recurrence proof core."""
from __future__ import annotations

import logging
from typing import NoReturn

from .proof_core_types import (
    Assume, Bound, CoreProp, CoreTerm, CoreType, EqRefl, EqSym, EqTrans, Equal,
    Forall, ForallElim, ForallIntro, ImpElim, ImpIntro, Implies, NativeLaw,
    NativeLawId, ProofTerm, Pulse, ResonanceIntro, Resonates, Silence, Stitch,
    Weave,
)
from .proof_surface_trace import traced
from .proof_surface_types import (
    ElaborationLimits, ProofOp, ProofSyntax, PropOp, PropSyntax, SourceSpan,
    SurfaceLanguageError, SurfaceProgram, TermOp, TermSyntax,
)


logger = logging.getLogger(__name__)
trace = traced(logger)


@trace
def _fail(code: str, span: SourceSpan | None = None) -> NoReturn:
    logger.error("surface lowering rejection state code=%s span=%r", code, span)
    raise SurfaceLanguageError("elaborate", code, span)


@trace
def _depth(depth: int, limits: ElaborationLimits, span: SourceSpan) -> int:
    if type(depth) is not int or depth < 0 or depth >= limits.max_depth:
        _fail("elaboration-depth-limit", span)
    return depth + 1


@trace
def _term(term: TermSyntax, names: tuple[str, ...], depth: int, limits: ElaborationLimits) -> CoreTerm:
    if type(term) is not TermSyntax or type(term.op) is not TermOp:
        _fail("invalid-term-node", getattr(term, "span", None))
    child_depth = _depth(depth, limits, term.span)
    if term.op is TermOp.VARIABLE:
        if term.name is None or term.children:
            _fail("invalid-variable-shape", term.span)
        try:
            result: CoreTerm = Bound(names.index(term.name))
        except ValueError:
            _fail("unbound-term-variable", term.span)
    elif term.op is TermOp.SILENCE:
        if term.name is not None or term.children:
            _fail("invalid-silence-shape", term.span)
        result = Silence()
    elif term.op is TermOp.PULSE:
        if term.name is not None or len(term.children) != 1:
            _fail("pulse-bad-arity", term.span)
        result = Pulse(_term(term.children[0], names, child_depth, limits))
    elif term.op in {TermOp.STITCH, TermOp.WEAVE}:
        if term.name is not None or len(term.children) != 2:
            _fail(f"{term.op.value}-bad-arity", term.span)
        children = tuple(_term(item, names, child_depth, limits) for item in term.children)
        result = Stitch(*children) if term.op is TermOp.STITCH else Weave(*children)
    else:
        _fail("unsupported-term-node", term.span)
    logger.debug("_term state op=%s binders=%d", term.op.value, len(names))
    return result


@trace
def _fresh(name: str | None, own: tuple[str, ...], other: tuple[str, ...], kind: str, span: SourceSpan) -> str:
    if type(name) is not str or not name:
        _fail(f"invalid-{kind}-binder", span)
    if name in own:
        _fail(f"duplicate-{kind}-binder", span)
    if name in other:
        _fail("captured-binder-name", span)
    return name


@trace
def _prop(
    prop: PropSyntax, terms: tuple[str, ...], assumptions: tuple[str, ...],
    depth: int, limits: ElaborationLimits,
) -> CoreProp:
    if type(prop) is not PropSyntax or type(prop.op) is not PropOp:
        _fail("invalid-proposition-node", getattr(prop, "span", None))
    child_depth = _depth(depth, limits, prop.span)
    if prop.op in {PropOp.EQUAL, PropOp.RESONATES}:
        if len(prop.terms) != 2 or prop.props or prop.binder_name is not None or prop.binder_type is not None:
            _fail(f"{prop.op.value}-bad-shape", prop.span)
        items = tuple(_term(item, terms, child_depth, limits) for item in prop.terms)
        result: CoreProp = Equal(*items) if prop.op is PropOp.EQUAL else Resonates(*items)
    elif prop.op is PropOp.IMPLIES:
        if len(prop.props) != 2 or prop.terms or prop.binder_name is not None or prop.binder_type is not None:
            _fail("implies-bad-shape", prop.span)
        items = tuple(_prop(item, terms, assumptions, child_depth, limits) for item in prop.props)
        result = Implies(*items)
    elif prop.op is PropOp.FORALL:
        if len(prop.props) != 1 or prop.terms or prop.binder_type != CoreType.RECURRENCE.value:
            _fail("forall-bad-shape", prop.span)
        name = _fresh(prop.binder_name, terms, assumptions, "term", prop.span)
        if len(terms) + len(assumptions) >= limits.max_binders:
            _fail("binder-limit", prop.span)
        result = Forall(
            CoreType.RECURRENCE,
            _prop(prop.props[0], (name,) + terms, assumptions, child_depth, limits),
        )
    else:
        _fail("unsupported-proposition-node", prop.span)
    logger.debug("_prop state op=%s term-binders=%d", prop.op.value, len(terms))
    return result


@trace
def _plain(proof: ProofSyntax) -> bool:
    """Return whether rule-specific metadata fields are all absent."""
    result = proof.name is None and proof.binder_type is None and proof.law_id is None
    logger.debug("_plain state result=%s", result)
    return result


@trace
def _proof(
    proof: ProofSyntax, terms: tuple[str, ...], assumptions: tuple[str, ...],
    depth: int, limits: ElaborationLimits,
) -> ProofTerm:
    if type(proof) is not ProofSyntax or type(proof.op) is not ProofOp:
        _fail("invalid-proof-node", getattr(proof, "span", None))
    next_depth = _depth(depth, limits, proof.span)
    if proof.op is ProofOp.ASSUME:
        if proof.name is None or proof.proofs or proof.terms or proof.props or proof.binder_type is not None or proof.law_id is not None:
            _fail("assume-bad-shape", proof.span)
        try:
            result: ProofTerm = Assume(assumptions.index(proof.name))
        except ValueError:
            _fail("unbound-assumption", proof.span)
    elif proof.op is ProofOp.IMP_INTRO:
        if len(proof.proofs) != 1 or len(proof.props) != 1 or proof.terms or proof.binder_type is not None or proof.law_id is not None:
            _fail("imp-intro-bad-shape", proof.span)
        name = _fresh(proof.name, assumptions, terms, "assumption", proof.span)
        if len(terms) + len(assumptions) >= limits.max_binders:
            _fail("binder-limit", proof.span)
        premise = _prop(proof.props[0], terms, assumptions, next_depth, limits)
        body = _proof(proof.proofs[0], terms, (name,) + assumptions, next_depth, limits)
        result = ImpIntro(premise, body)
    elif proof.op in {ProofOp.IMP_ELIM, ProofOp.EQ_TRANS}:
        if len(proof.proofs) != 2 or proof.terms or proof.props or not _plain(proof):
            _fail(f"{proof.op.value}-bad-shape", proof.span)
        children = tuple(_proof(item, terms, assumptions, next_depth, limits) for item in proof.proofs)
        result = ImpElim(*children) if proof.op is ProofOp.IMP_ELIM else EqTrans(*children)
    elif proof.op is ProofOp.FORALL_INTRO:
        if len(proof.proofs) != 1 or proof.terms or proof.props or proof.binder_type != CoreType.RECURRENCE.value or proof.law_id is not None:
            _fail("forall-intro-bad-shape", proof.span)
        name = _fresh(proof.name, terms, assumptions, "term", proof.span)
        if len(terms) + len(assumptions) >= limits.max_binders:
            _fail("binder-limit", proof.span)
        body = _proof(proof.proofs[0], (name,) + terms, assumptions, next_depth, limits)
        result = ForallIntro(CoreType.RECURRENCE, body)
    elif proof.op is ProofOp.FORALL_ELIM:
        if len(proof.proofs) != 1 or len(proof.terms) != 1 or proof.props or not _plain(proof):
            _fail("forall-elim-bad-shape", proof.span)
        universal = _proof(proof.proofs[0], terms, assumptions, next_depth, limits)
        result = ForallElim(universal, _term(proof.terms[0], terms, next_depth, limits))
    elif proof.op is ProofOp.EQ_REFL:
        if proof.proofs or len(proof.terms) != 1 or proof.props or not _plain(proof):
            _fail("eq-refl-bad-shape", proof.span)
        result = EqRefl(_term(proof.terms[0], terms, next_depth, limits))
    elif proof.op is ProofOp.EQ_SYM:
        if len(proof.proofs) != 1 or proof.terms or proof.props or not _plain(proof):
            _fail("eq-sym-bad-shape", proof.span)
        result = EqSym(_proof(proof.proofs[0], terms, assumptions, next_depth, limits))
    elif proof.op is ProofOp.NATIVE_LAW:
        if proof.proofs or proof.props or proof.law_id is None or proof.name is not None or proof.binder_type is not None:
            _fail("native-law-bad-shape", proof.span)
        try:
            law = NativeLawId(proof.law_id)
        except ValueError:
            _fail("unknown-native-law", proof.span)
        result = NativeLaw(law, tuple(_term(item, terms, next_depth, limits) for item in proof.terms))
    elif proof.op is ProofOp.RESONANCE_INTRO:
        if len(proof.proofs) != 1 or len(proof.terms) != 3 or proof.props or not _plain(proof):
            _fail("resonance-intro-bad-shape", proof.span)
        items = tuple(_term(item, terms, next_depth, limits) for item in proof.terms)
        equality = _proof(proof.proofs[0], terms, assumptions, next_depth, limits)
        result = ResonanceIntro(*items, equality)
    else:
        _fail("unsupported-proof-node", proof.span)
    logger.debug("_proof state op=%s assumption-binders=%d", proof.op.value, len(assumptions))
    return result


@trace
def lower_surface_program(program: SurfaceProgram, limits: ElaborationLimits) -> tuple[CoreProp, ProofTerm]:
    """Lower a previously origin-validated closed surface program."""
    result = _prop(program.claim, (), (), 0, limits), _proof(program.proof, (), (), 0, limits)
    logger.debug("lower_surface_program state claim=%s proof=%s", type(result[0]).__name__, type(result[1]).__name__)
    return result
