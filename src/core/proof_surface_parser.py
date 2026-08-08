"""Typed parser for the versioned proof-grade recurrence surface syntax."""
from __future__ import annotations

import logging
import re
from typing import NoReturn

from .proof_core_types import NativeLawId
from .proof_surface_sexpr import AtomNode, ListNode, SExprNode, read_sexpr
from .proof_surface_trace import traced
from .proof_surface_types import (
    DEFAULT_SOURCE_LIMITS, ProofOp, ProofSyntax, PropOp, PropSyntax,
    SourceLimits, SourceSpan, SurfaceLanguageError, SurfaceProgram,
    SURFACE_LANGUAGE_ID, SURFACE_VERSION, TermOp, TermSyntax,
)


logger = logging.getLogger(__name__)
trace = traced(logger)
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*\Z")
NATIVE_LAW_ARITY = {
    NativeLawId.STITCH_SILENCE_LEFT.value: 1,
    NativeLawId.STITCH_SILENCE_RIGHT.value: 1,
    NativeLawId.WEAVE_SILENCE_RIGHT.value: 1,
    NativeLawId.WEAVE_PULSE.value: 2,
    NativeLawId.WEAVE_UNIT_RIGHT.value: 1,
}


@trace
def _fail(code: str, span: SourceSpan | None = None) -> NoReturn:
    logger.error("surface parser rejection state code=%s span=%r", code, span)
    raise SurfaceLanguageError("parse", code, span)


@trace
def _items(node: SExprNode, minimum: int = 1) -> tuple[SExprNode, ...]:
    if type(node) is not ListNode:
        _fail("list-required", node.span)
    if len(node.items) < minimum:
        _fail("empty-or-short-form", node.span)
    return node.items


@trace
def _atom(node: SExprNode, role: str) -> str:
    if type(node) is not AtomNode:
        _fail(f"{role}-atom-required", node.span)
    return node.text


@trace
def _identifier(node: SExprNode, role: str) -> str:
    text = _atom(node, role)
    if IDENTIFIER.fullmatch(text) is None:
        _fail(f"invalid-{role}", node.span)
    return text


@trace
def _head(node: SExprNode) -> tuple[str, tuple[SExprNode, ...], SourceSpan]:
    items = _items(node)
    return _atom(items[0], "form-head"), items[1:], node.span


@trace
def _arity(args: tuple[SExprNode, ...], expected: int, head: str, span: SourceSpan) -> None:
    if len(args) != expected:
        _fail(f"{head}-bad-arity", span)


@trace
def parse_term(node: SExprNode) -> TermSyntax:
    """Parse one recurrence term; variables are always explicit ``(var x)``."""
    head, args, span = _head(node)
    if head == TermOp.VARIABLE.value:
        _arity(args, 1, head, span)
        result = TermSyntax(TermOp.VARIABLE, span, name=_identifier(args[0], "term-name"))
    elif head == TermOp.SILENCE.value:
        _arity(args, 0, head, span)
        result = TermSyntax(TermOp.SILENCE, span)
    elif head == TermOp.PULSE.value:
        _arity(args, 1, head, span)
        result = TermSyntax(TermOp.PULSE, span, (parse_term(args[0]),))
    elif head in {TermOp.STITCH.value, TermOp.WEAVE.value}:
        _arity(args, 2, head, span)
        op = TermOp.STITCH if head == TermOp.STITCH.value else TermOp.WEAVE
        result = TermSyntax(op, span, tuple(parse_term(item) for item in args))
    else:
        _fail("unsupported-term-syntax", span)
    logger.debug("parse_term state op=%s", result.op.value)
    return result


@trace
def parse_prop(node: SExprNode) -> PropSyntax:
    """Parse equality, implication, universal quantification, or resonance."""
    head, args, span = _head(node)
    if head == PropOp.EQUAL.value:
        _arity(args, 2, head, span)
        result = PropSyntax(PropOp.EQUAL, span, terms=tuple(parse_term(item) for item in args))
    elif head == PropOp.IMPLIES.value:
        _arity(args, 2, head, span)
        result = PropSyntax(PropOp.IMPLIES, span, props=tuple(parse_prop(item) for item in args))
    elif head == PropOp.FORALL.value:
        _arity(args, 3, head, span)
        binder = _identifier(args[0], "binder-name")
        binder_type = _atom(args[1], "binder-type")
        if binder_type != "recurrence":
            _fail("unsupported-binder-type", args[1].span)
        result = PropSyntax(
            PropOp.FORALL, span, props=(parse_prop(args[2]),),
            binder_name=binder, binder_type=binder_type,
        )
    elif head == PropOp.RESONATES.value:
        _arity(args, 2, head, span)
        result = PropSyntax(PropOp.RESONATES, span, terms=tuple(parse_term(item) for item in args))
    elif head in {"iff", "ready", "blocked", "unknown", "status"}:
        _fail("unsupported-proposition-syntax", span)
    else:
        _fail("unsupported-proposition-syntax", span)
    logger.debug("parse_prop state op=%s", result.op.value)
    return result


@trace
def parse_proof(node: SExprNode) -> ProofSyntax:
    """Parse one explicit R7 proof constructor."""
    head, args, span = _head(node)
    try:
        op = ProofOp(head)
    except ValueError:
        _fail("unsupported-proof-syntax", span)
    if op is ProofOp.ASSUME:
        _arity(args, 1, head, span)
        result = ProofSyntax(op, span, name=_identifier(args[0], "assumption-name"))
    elif op is ProofOp.IMP_INTRO:
        _arity(args, 3, head, span)
        result = ProofSyntax(
            op, span, proofs=(parse_proof(args[2]),), props=(parse_prop(args[1]),),
            name=_identifier(args[0], "assumption-name"),
        )
    elif op in {ProofOp.IMP_ELIM, ProofOp.EQ_TRANS}:
        _arity(args, 2, head, span)
        result = ProofSyntax(op, span, proofs=tuple(parse_proof(item) for item in args))
    elif op is ProofOp.FORALL_INTRO:
        _arity(args, 3, head, span)
        name = _identifier(args[0], "binder-name")
        binder_type = _atom(args[1], "binder-type")
        if binder_type != "recurrence":
            _fail("unsupported-binder-type", args[1].span)
        result = ProofSyntax(
            op, span, proofs=(parse_proof(args[2]),), name=name, binder_type=binder_type,
        )
    elif op is ProofOp.FORALL_ELIM:
        _arity(args, 2, head, span)
        result = ProofSyntax(op, span, proofs=(parse_proof(args[0]),), terms=(parse_term(args[1]),))
    elif op is ProofOp.EQ_REFL:
        _arity(args, 1, head, span)
        result = ProofSyntax(op, span, terms=(parse_term(args[0]),))
    elif op is ProofOp.EQ_SYM:
        _arity(args, 1, head, span)
        result = ProofSyntax(op, span, proofs=(parse_proof(args[0]),))
    elif op is ProofOp.NATIVE_LAW:
        if not args:
            _fail("native-law-bad-arity", span)
        law = _atom(args[0], "native-law")
        if law not in NATIVE_LAW_ARITY:
            _fail("unknown-native-law", args[0].span)
        _arity(args[1:], NATIVE_LAW_ARITY[law], head, span)
        result = ProofSyntax(op, span, terms=tuple(parse_term(item) for item in args[1:]), law_id=law)
    elif op is ProofOp.RESONANCE_INTRO:
        _arity(args, 4, head, span)
        result = ProofSyntax(
            op, span, proofs=(parse_proof(args[3]),),
            terms=tuple(parse_term(item) for item in args[:3]),
        )
    else:
        _fail("unsupported-proof-syntax", span)
    logger.debug("parse_proof state op=%s", result.op.value)
    return result


@trace
def parse_surface_program(
    source: str, limits: SourceLimits = DEFAULT_SOURCE_LIMITS,
) -> SurfaceProgram:
    """Parse ``(veyra-proof 1 (claim PROP) (proof PROOF))`` exactly."""
    if type(limits) is not SourceLimits:
        _fail("invalid-source-limits")
    root = read_sexpr(source, limits)
    head, args, span = _head(root)
    if head != "veyra-proof":
        _fail("invalid-language-header", span)
    _arity(args, 3, head, span)
    version_text = _atom(args[0], "language-version")
    if version_text != str(SURFACE_VERSION):
        _fail("unsupported-language-version", args[0].span)
    claim_head, claim_args, claim_span = _head(args[1])
    proof_head, proof_args, proof_span = _head(args[2])
    if claim_head != "claim":
        _fail("claim-form-required", claim_span)
    if proof_head != "proof":
        _fail("proof-form-required", proof_span)
    _arity(claim_args, 1, "claim", claim_span)
    _arity(proof_args, 1, "proof", proof_span)
    result = SurfaceProgram(
        SURFACE_LANGUAGE_ID, SURFACE_VERSION,
        parse_prop(claim_args[0]), parse_proof(proof_args[0]), span,
    )
    logger.debug("parse_surface_program state version=%d", result.version)
    return result
