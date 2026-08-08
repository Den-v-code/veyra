"""Structural, non-minimal dependency support for the R7/R9 proof lane."""
from __future__ import annotations

from enum import Enum
import logging
from typing import NoReturn

from .proof_core_types import (
    Assume, Bound, CoreProp, CoreTerm, EqRefl, EqSym, EqTrans, Equal, Forall,
    ForallElim, ForallIntro, ImpElim, ImpIntro, Implies, NativeLaw,
    NativeLawId, ProofTerm, Pulse, ResonanceIntro, Resonates, Silence, Stitch,
    Weave,
)

logger = logging.getLogger(__name__)


class DependencyCategory(str, Enum):
    """Disjoint roles of dependencies used by the elaborated proof lane."""

    FORMATION = "formation"
    DEFINITION = "definition"
    LOGICAL = "logical"
    DOMAIN = "domain"
    OBSERVER = "observer"
    OBSTRUCTION = "obstruction"


class DependencyId(str, Enum):
    """Stable identifiers; membership is computed from syntax, never declared."""

    RECURRENCE_FORMATION = "formation.recurrence"
    PROPOSITION_FORMATION = "formation.proposition"
    SILENCE_DEFINITION = "definition.silence"
    PULSE_DEFINITION = "definition.pulse"
    STITCH_DEFINITION = "definition.stitch"
    WEAVE_DEFINITION = "definition.weave"
    EQUAL_DEFINITION = "definition.equal"
    IMPLIES_DEFINITION = "definition.implies"
    FORALL_DEFINITION = "definition.forall"
    RESONATES_DEFINITION = "definition.resonates"
    ASSUME_RULE = "logical.assume"
    IMP_INTRO_RULE = "logical.imp-intro"
    IMP_ELIM_RULE = "logical.imp-elim"
    FORALL_INTRO_RULE = "logical.forall-intro"
    FORALL_ELIM_RULE = "logical.forall-elim"
    EQ_REFL_RULE = "logical.eq-refl"
    EQ_SYM_RULE = "logical.eq-sym"
    EQ_TRANS_RULE = "logical.eq-trans"
    RESONANCE_INTRO_RULE = "logical.resonance-intro"
    STITCH_SILENCE_LEFT_LAW = "domain.stitch-silence-left"
    STITCH_SILENCE_RIGHT_LAW = "domain.stitch-silence-right"
    WEAVE_SILENCE_RIGHT_LAW = "domain.weave-silence-right"
    WEAVE_PULSE_LAW = "domain.weave-pulse"
    WEAVE_UNIT_RIGHT_LAW = "domain.weave-unit-right"
    INTRINSIC_MODE_OBSERVER = "observer.intrinsic-mode"
    FOREIGN_MODE_OBSTRUCTION = "obstruction.foreign-mode"


Support = frozenset[DependencyId]
_FORMATION = {
    DependencyId.RECURRENCE_FORMATION,
    DependencyId.PROPOSITION_FORMATION,
}
_DEFINITION = {
    DependencyId.SILENCE_DEFINITION, DependencyId.PULSE_DEFINITION,
    DependencyId.STITCH_DEFINITION, DependencyId.WEAVE_DEFINITION,
    DependencyId.EQUAL_DEFINITION, DependencyId.IMPLIES_DEFINITION,
    DependencyId.FORALL_DEFINITION, DependencyId.RESONATES_DEFINITION,
}
_LOGICAL = {
    DependencyId.ASSUME_RULE, DependencyId.IMP_INTRO_RULE,
    DependencyId.IMP_ELIM_RULE, DependencyId.FORALL_INTRO_RULE,
    DependencyId.FORALL_ELIM_RULE, DependencyId.EQ_REFL_RULE,
    DependencyId.EQ_SYM_RULE, DependencyId.EQ_TRANS_RULE,
    DependencyId.RESONANCE_INTRO_RULE,
}
_DOMAIN = {
    DependencyId.STITCH_SILENCE_LEFT_LAW,
    DependencyId.STITCH_SILENCE_RIGHT_LAW,
    DependencyId.WEAVE_SILENCE_RIGHT_LAW,
    DependencyId.WEAVE_PULSE_LAW,
    DependencyId.WEAVE_UNIT_RIGHT_LAW,
}


def _reject(reason: str) -> NoReturn:
    logger.error("proof_dependency_support rejected reason=%s", reason)
    raise TypeError(reason)


def dependency_category(dependency: DependencyId) -> DependencyCategory:
    """Return the unique declared role of one dependency identifier."""
    logger.debug("dependency_category entry dependency=%r", dependency)
    if type(dependency) is not DependencyId:
        _reject("unknown-dependency-id")
    if dependency in _FORMATION:
        result = DependencyCategory.FORMATION
    elif dependency in _DEFINITION:
        result = DependencyCategory.DEFINITION
    elif dependency in _LOGICAL:
        result = DependencyCategory.LOGICAL
    elif dependency in _DOMAIN:
        result = DependencyCategory.DOMAIN
    elif dependency is DependencyId.INTRINSIC_MODE_OBSERVER:
        result = DependencyCategory.OBSERVER
    elif dependency is DependencyId.FOREIGN_MODE_OBSTRUCTION:
        result = DependencyCategory.OBSTRUCTION
    else:
        _reject("uncategorized-dependency-id")
    logger.debug("dependency_category exit result=%s", result.value)
    return result


def _term_support(term: CoreTerm, active: set[int]) -> Support:
    logger.debug("_term_support entry type=%s", type(term).__name__)
    identity = id(term)
    if identity in active:
        _reject("circular-core-term")
    active.add(identity)
    try:
        base = {DependencyId.RECURRENCE_FORMATION}
        if type(term) is Bound:
            result = frozenset(base)
        elif type(term) is Silence:
            result = frozenset(base | {DependencyId.SILENCE_DEFINITION})
        elif type(term) is Pulse:
            result = frozenset(base | {DependencyId.PULSE_DEFINITION} | set(_term_support(term.tail, active)))
        elif type(term) in {Stitch, Weave}:
            dependency = DependencyId.STITCH_DEFINITION if type(term) is Stitch else DependencyId.WEAVE_DEFINITION
            result = frozenset(base | {dependency} | set(_term_support(term.left, active)) | set(_term_support(term.right, active)))
        else:
            _reject(f"unknown-core-term:{type(term).__name__}")
    finally:
        active.remove(identity)
    logger.debug("_term_support exit count=%d", len(result))
    return result


def term_support(term: CoreTerm) -> Support:
    """Compute exact constructor support of a recurrence term."""
    logger.debug("term_support entry type=%s", type(term).__name__)
    result = _term_support(term, set())
    logger.debug("term_support exit count=%d", len(result))
    return result


def _prop_support(prop: CoreProp, active: set[int]) -> Support:
    logger.debug("_prop_support entry type=%s", type(prop).__name__)
    identity = id(prop)
    if identity in active:
        _reject("circular-core-proposition")
    active.add(identity)
    try:
        base = {DependencyId.PROPOSITION_FORMATION}
        if type(prop) is Equal:
            result = base | {DependencyId.EQUAL_DEFINITION} | set(term_support(prop.left)) | set(term_support(prop.right))
        elif type(prop) is Implies:
            result = base | {DependencyId.IMPLIES_DEFINITION} | set(_prop_support(prop.premise, active)) | set(_prop_support(prop.conclusion, active))
        elif type(prop) is Forall:
            result = base | {DependencyId.FORALL_DEFINITION} | set(_prop_support(prop.body, active))
        elif type(prop) is Resonates:
            result = base | {DependencyId.RESONATES_DEFINITION} | set(term_support(prop.factor)) | set(term_support(prop.carrier))
        else:
            _reject(f"unknown-core-proposition:{type(prop).__name__}")
    finally:
        active.remove(identity)
    frozen = frozenset(result)
    logger.debug("_prop_support exit count=%d", len(frozen))
    return frozen


def prop_support(prop: CoreProp) -> Support:
    """Compute formation/definition support of a proposition."""
    logger.debug("prop_support entry type=%s", type(prop).__name__)
    result = _prop_support(prop, set())
    logger.debug("prop_support exit count=%d", len(result))
    return result


_LAW_SUPPORT = {
    NativeLawId.STITCH_SILENCE_LEFT: frozenset({
        DependencyId.STITCH_SILENCE_LEFT_LAW, DependencyId.STITCH_DEFINITION,
        DependencyId.SILENCE_DEFINITION,
    }),
    NativeLawId.STITCH_SILENCE_RIGHT: frozenset({
        DependencyId.STITCH_SILENCE_RIGHT_LAW, DependencyId.STITCH_DEFINITION,
        DependencyId.SILENCE_DEFINITION,
    }),
    NativeLawId.WEAVE_SILENCE_RIGHT: frozenset({
        DependencyId.WEAVE_SILENCE_RIGHT_LAW, DependencyId.WEAVE_DEFINITION,
        DependencyId.SILENCE_DEFINITION,
    }),
    NativeLawId.WEAVE_PULSE: frozenset({
        DependencyId.WEAVE_PULSE_LAW, DependencyId.WEAVE_DEFINITION,
        DependencyId.PULSE_DEFINITION, DependencyId.STITCH_DEFINITION,
    }),
    NativeLawId.WEAVE_UNIT_RIGHT: frozenset({
        DependencyId.WEAVE_UNIT_RIGHT_LAW, DependencyId.WEAVE_DEFINITION,
        DependencyId.PULSE_DEFINITION, DependencyId.SILENCE_DEFINITION,
    }),
}


def _proof_support(proof: ProofTerm, active: set[int]) -> Support:
    logger.debug("_proof_support entry type=%s", type(proof).__name__)
    identity = id(proof)
    if identity in active:
        _reject("circular-proof-term")
    active.add(identity)
    try:
        if type(proof) is Assume:
            result = {DependencyId.ASSUME_RULE}
        elif type(proof) is ImpIntro:
            result = {
                DependencyId.IMP_INTRO_RULE, DependencyId.IMPLIES_DEFINITION,
                DependencyId.PROPOSITION_FORMATION,
            } | set(prop_support(proof.premise)) | set(_proof_support(proof.body, active))
        elif type(proof) is ImpElim:
            result = {DependencyId.IMP_ELIM_RULE} | set(_proof_support(proof.function, active)) | set(_proof_support(proof.argument, active))
        elif type(proof) is ForallIntro:
            result = {
                DependencyId.FORALL_INTRO_RULE, DependencyId.FORALL_DEFINITION,
                DependencyId.PROPOSITION_FORMATION,
                DependencyId.RECURRENCE_FORMATION,
            } | set(_proof_support(proof.body, active))
        elif type(proof) is ForallElim:
            result = {DependencyId.FORALL_ELIM_RULE} | set(_proof_support(proof.universal, active)) | set(term_support(proof.argument))
        elif type(proof) is EqRefl:
            result = {
                DependencyId.EQ_REFL_RULE, DependencyId.EQUAL_DEFINITION,
                DependencyId.PROPOSITION_FORMATION,
            } | set(term_support(proof.term))
        elif type(proof) is EqSym:
            result = {DependencyId.EQ_SYM_RULE} | set(_proof_support(proof.evidence, active))
        elif type(proof) is EqTrans:
            result = {DependencyId.EQ_TRANS_RULE} | set(_proof_support(proof.left, active)) | set(_proof_support(proof.right, active))
        elif type(proof) is NativeLaw:
            dependencies = _LAW_SUPPORT.get(proof.law_id)
            if dependencies is None:
                _reject("unknown-native-law")
            result = {
                DependencyId.EQUAL_DEFINITION,
                DependencyId.PROPOSITION_FORMATION,
            } | set(dependencies) | {
                item for arg in proof.args for item in term_support(arg)
            }
        elif type(proof) is ResonanceIntro:
            terms = (proof.factor, proof.carrier, proof.witness)
            result = {
                DependencyId.RESONANCE_INTRO_RULE,
                DependencyId.RESONATES_DEFINITION,
                DependencyId.PROPOSITION_FORMATION,
            }
            result |= {item for term in terms for item in term_support(term)}
            result |= set(_proof_support(proof.equality, active))
        else:
            _reject(f"unknown-proof-term:{type(proof).__name__}")
    finally:
        active.remove(identity)
    frozen = frozenset(result)
    logger.debug("_proof_support exit count=%d", len(frozen))
    return frozen


def proof_support(proof: ProofTerm) -> Support:
    """Compute used support by structural traversal; no minimality is claimed."""
    logger.debug("proof_support entry type=%s", type(proof).__name__)
    result = _proof_support(proof, set())
    logger.debug("proof_support exit count=%d", len(result))
    return result


def image_composition_support(proof: ProofTerm) -> Support:
    """Add the exact R9 image observer used to interpret an R7 proof."""
    logger.debug("image_composition_support entry type=%s", type(proof).__name__)
    result = proof_support(proof) | {DependencyId.INTRINSIC_MODE_OBSERVER}
    logger.debug("image_composition_support exit count=%d", len(result))
    return result


def support_by_category(support: Support) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return a deterministic categorized serialization of computed support."""
    logger.debug("support_by_category entry count=%d", len(support))
    if type(support) is not frozenset or any(type(item) is not DependencyId for item in support):
        _reject("invalid-dependency-support")
    result = tuple(
        (category.value, tuple(sorted(item.value for item in support if dependency_category(item) is category)))
        for category in DependencyCategory
    )
    logger.debug("support_by_category exit categories=%d", len(result))
    return result
