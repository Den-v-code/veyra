"""Capture-safe de Bruijn operations for proof-core terms and propositions."""
from __future__ import annotations

import logging
from typing import NoReturn

from .proof_core_types import (
    Bound, CoreProp, CoreTerm, Equal, Forall, Implies, Pulse, Resonates,
    Silence, Stitch, Weave,
)

logger = logging.getLogger(__name__)


def _value(reason: str) -> NoReturn:
    logger.error("proof_core_substitution value rejection reason=%s", reason)
    raise ValueError(reason)


def _type(reason: str) -> NoReturn:
    logger.error("proof_core_substitution type rejection reason=%s", reason)
    raise TypeError(reason)


def _index(value: int, label: str) -> int:
    logger.debug("_index entry label=%s value=%r", label, value)
    if type(value) is not int or value < 0:
        logger.error("_index invalid label=%s value=%r", label, value)
        raise ValueError(f"{label}-must-be-nonnegative-int")
    logger.debug("_index exit value=%d", value)
    return value


def shift_term(term: CoreTerm, delta: int, cutoff: int = 0) -> CoreTerm:
    """Shift free indices at or above ``cutoff`` by ``delta``."""
    logger.debug("shift_term entry term=%r delta=%r cutoff=%r", term, delta, cutoff)
    if type(delta) is not int:
        _value("shift-delta-must-be-int")
    boundary = _index(cutoff, "shift-cutoff")
    if type(term) is Bound:
        index = _index(term.index, "bound-index")
        moved = index + delta if index >= boundary else index
        if moved < 0:
            _value("shift-produced-negative-index")
        result: CoreTerm = Bound(moved)
    elif type(term) is Silence:
        result = term
    elif type(term) is Pulse:
        result = Pulse(shift_term(term.tail, delta, boundary))
    elif type(term) is Stitch:
        result = Stitch(shift_term(term.left, delta, boundary), shift_term(term.right, delta, boundary))
    elif type(term) is Weave:
        result = Weave(shift_term(term.left, delta, boundary), shift_term(term.right, delta, boundary))
    else:
        _type(f"unknown-core-term:{type(term).__name__}")
    logger.debug("shift_term exit result=%r", result)
    return result


def shift_prop(prop: CoreProp, delta: int, cutoff: int = 0) -> CoreProp:
    """Shift term indices through proposition binders."""
    logger.debug("shift_prop entry prop=%r delta=%r cutoff=%r", prop, delta, cutoff)
    boundary = _index(cutoff, "shift-cutoff")
    if type(prop) is Equal:
        result: CoreProp = Equal(shift_term(prop.left, delta, boundary), shift_term(prop.right, delta, boundary))
    elif type(prop) is Implies:
        result = Implies(shift_prop(prop.premise, delta, boundary), shift_prop(prop.conclusion, delta, boundary))
    elif type(prop) is Forall:
        result = Forall(prop.binder_type, shift_prop(prop.body, delta, boundary + 1))
    elif type(prop) is Resonates:
        result = Resonates(shift_term(prop.factor, delta, boundary), shift_term(prop.carrier, delta, boundary))
    else:
        _type(f"unknown-core-prop:{type(prop).__name__}")
    logger.debug("shift_prop exit result=%r", result)
    return result


def subst_term(term: CoreTerm, index: int, replacement: CoreTerm, depth: int = 0) -> CoreTerm:
    """Substitute one de Bruijn variable without removing its binder."""
    logger.debug("subst_term entry term=%r index=%r depth=%r", term, index, depth)
    target, nesting = _index(index, "subst-index"), _index(depth, "subst-depth")
    if type(term) is Bound:
        current = _index(term.index, "bound-index")
        result: CoreTerm = shift_term(replacement, nesting) if current == target + nesting else term
    elif type(term) is Silence:
        result = term
    elif type(term) is Pulse:
        result = Pulse(subst_term(term.tail, target, replacement, nesting))
    elif type(term) is Stitch:
        result = Stitch(subst_term(term.left, target, replacement, nesting), subst_term(term.right, target, replacement, nesting))
    elif type(term) is Weave:
        result = Weave(subst_term(term.left, target, replacement, nesting), subst_term(term.right, target, replacement, nesting))
    else:
        _type(f"unknown-core-term:{type(term).__name__}")
    logger.debug("subst_term exit result=%r", result)
    return result


def subst_prop(prop: CoreProp, index: int, replacement: CoreTerm, depth: int = 0) -> CoreProp:
    """Substitute a term through a proposition, respecting every binder."""
    logger.debug("subst_prop entry prop=%r index=%r depth=%r", prop, index, depth)
    target, nesting = _index(index, "subst-index"), _index(depth, "subst-depth")
    if type(prop) is Equal:
        result: CoreProp = Equal(subst_term(prop.left, target, replacement, nesting), subst_term(prop.right, target, replacement, nesting))
    elif type(prop) is Implies:
        result = Implies(subst_prop(prop.premise, target, replacement, nesting), subst_prop(prop.conclusion, target, replacement, nesting))
    elif type(prop) is Forall:
        result = Forall(prop.binder_type, subst_prop(prop.body, target, replacement, nesting + 1))
    elif type(prop) is Resonates:
        result = Resonates(subst_term(prop.factor, target, replacement, nesting), subst_term(prop.carrier, target, replacement, nesting))
    else:
        _type(f"unknown-core-prop:{type(prop).__name__}")
    logger.debug("subst_prop exit result=%r", result)
    return result


def instantiate_prop(body: CoreProp, argument: CoreTerm) -> CoreProp:
    """Remove the outer proposition binder by capture-safe substitution."""
    logger.debug("instantiate_prop entry body=%r argument=%r", body, argument)
    lifted = shift_term(argument, 1)
    result = shift_prop(subst_prop(body, 0, lifted), -1)
    logger.debug("instantiate_prop exit result=%r", result)
    return result


def free_term_indices(term: CoreTerm, depth: int = 0) -> frozenset[int]:
    """Return free indices normalized relative to ``depth`` binders."""
    logger.debug("free_term_indices entry term=%r depth=%r", term, depth)
    nesting = _index(depth, "free-depth")
    if type(term) is Bound:
        current = _index(term.index, "bound-index")
        result = frozenset({current - nesting}) if current >= nesting else frozenset()
    elif type(term) is Silence:
        result = frozenset()
    elif type(term) is Pulse:
        result = free_term_indices(term.tail, nesting)
    elif type(term) in {Stitch, Weave}:
        result = free_term_indices(term.left, nesting) | free_term_indices(term.right, nesting)
    else:
        _type(f"unknown-core-term:{type(term).__name__}")
    logger.debug("free_term_indices exit result=%r", result)
    return result


def free_prop_indices(prop: CoreProp, depth: int = 0) -> frozenset[int]:
    """Return free term indices of a proposition."""
    logger.debug("free_prop_indices entry prop=%r depth=%r", prop, depth)
    nesting = _index(depth, "free-depth")
    if type(prop) is Equal:
        result = free_term_indices(prop.left, nesting) | free_term_indices(prop.right, nesting)
    elif type(prop) is Implies:
        result = free_prop_indices(prop.premise, nesting) | free_prop_indices(prop.conclusion, nesting)
    elif type(prop) is Forall:
        result = free_prop_indices(prop.body, nesting + 1)
    elif type(prop) is Resonates:
        result = free_term_indices(prop.factor, nesting) | free_term_indices(prop.carrier, nesting)
    else:
        _type(f"unknown-core-prop:{type(prop).__name__}")
    logger.debug("free_prop_indices exit result=%r", result)
    return result
