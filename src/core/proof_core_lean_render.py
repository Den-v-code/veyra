"""Deterministic Lean renderer for the checked R7 proof-core syntax."""
from __future__ import annotations

import logging
from typing import NoReturn

from .proof_core_resonance import IntrinsicResonanceTheorem, verify_intrinsic_theorem_binding
from .proof_core_types import (
    Assume, Bound, CoreProp, CoreTerm, CoreType, EqRefl, EqSym, EqTrans, Equal,
    Forall, ForallElim, ForallIntro, ImpElim, ImpIntro, Implies, NativeLaw,
    NativeLawId, ProofTerm, Pulse, ResonanceIntro, Resonates, Silence, Stitch,
    Weave,
)

logger = logging.getLogger(__name__)
LAW_NAMES = {
    NativeLawId.STITCH_SILENCE_LEFT: "stitchSilenceLeft",
    NativeLawId.STITCH_SILENCE_RIGHT: "stitchSilenceRight",
    NativeLawId.WEAVE_SILENCE_RIGHT: "weaveSilenceRight",
    NativeLawId.WEAVE_PULSE: "weavePulse",
    NativeLawId.WEAVE_UNIT_RIGHT: "weaveUnitRight",
}


def _value(reason: str) -> NoReturn:
    logger.error("proof_core_lean_render value rejection reason=%s", reason)
    raise ValueError(reason)


def _type(reason: str) -> NoReturn:
    logger.error("proof_core_lean_render type rejection reason=%s", reason)
    raise TypeError(reason)


def _kind(kind: CoreType) -> str:
    logger.debug("proof_core_lean_render._kind entry kind=%r", kind)
    if kind is not CoreType.RECURRENCE:
        logger.error("proof_core_lean_render._kind unsupported=%r", kind)
        _value("unsupported-lean-core-type")
    result = ".recurrence"
    logger.debug("proof_core_lean_render._kind exit result=%s", result)
    return result


def lean_term(term: CoreTerm) -> str:
    """Render one checked de Bruijn term into the mirrored Lean syntax."""
    logger.debug("lean_term entry term=%r", term)
    if type(term) is Bound:
        if type(term.index) is not int or term.index < 0:
            _value("invalid-bound-index")
        result = f"(.var ⟨{term.index}, by decide⟩)"
    elif type(term) is Silence:
        result = ".silence"
    elif type(term) is Pulse:
        result = f"(.pulse {lean_term(term.tail)})"
    elif type(term) is Stitch:
        result = f"(.stitch {lean_term(term.left)} {lean_term(term.right)})"
    elif type(term) is Weave:
        result = f"(.weave {lean_term(term.left)} {lean_term(term.right)})"
    else:
        _type(f"unknown-core-term:{type(term).__name__}")
    logger.debug("lean_term exit result=%s", result)
    return result


def lean_prop(prop: CoreProp) -> str:
    """Render one checked proposition into the mirrored Lean syntax."""
    logger.debug("lean_prop entry prop=%r", prop)
    if type(prop) is Equal:
        result = f"(.equal {lean_term(prop.left)} {lean_term(prop.right)})"
    elif type(prop) is Implies:
        result = f"(.implies {lean_prop(prop.premise)} {lean_prop(prop.conclusion)})"
    elif type(prop) is Forall:
        result = f"(.forallE {_kind(prop.binder_type)} {lean_prop(prop.body)})"
    elif type(prop) is Resonates:
        result = f"(.resonates {lean_term(prop.factor)} {lean_term(prop.carrier)})"
    else:
        _type(f"unknown-core-prop:{type(prop).__name__}")
    logger.debug("lean_prop exit result=%s", result)
    return result


def lean_proof(proof: ProofTerm) -> str:
    """Render every proof constructor supported by both trusted kernels."""
    logger.debug("lean_proof entry proof=%r", proof)
    if type(proof) is Assume:
        if type(proof.index) is not int or proof.index < 0:
            _value("invalid-assumption-index")
        result = f"(.hyp {proof.index})"
    elif type(proof) is ImpIntro:
        result = f"(.impIntro {lean_prop(proof.premise)} {lean_proof(proof.body)})"
    elif type(proof) is ImpElim:
        result = f"(.impElim {lean_proof(proof.function)} {lean_proof(proof.argument)})"
    elif type(proof) is ForallIntro:
        result = f"(.forallIntro {_kind(proof.binder_type)} {lean_proof(proof.body)})"
    elif type(proof) is ForallElim:
        result = f"(.forallElim {lean_proof(proof.universal)} {lean_term(proof.argument)})"
    elif type(proof) is EqRefl:
        result = f"(.eqRefl {lean_term(proof.term)})"
    elif type(proof) is EqSym:
        result = f"(.eqSymm {lean_proof(proof.evidence)})"
    elif type(proof) is EqTrans:
        result = f"(.eqTrans {lean_proof(proof.left)} {lean_proof(proof.right)})"
    elif type(proof) is NativeLaw:
        law = LAW_NAMES.get(proof.law_id)
        if law is None:
            _value("unsupported-native-law")
        arguments = ", ".join(lean_term(item) for item in proof.args)
        result = f"(.nativeLaw .{law} [{arguments}])"
    elif type(proof) is ResonanceIntro:
        result = (
            f"(.resonanceIntro {lean_term(proof.factor)} {lean_term(proof.carrier)} "
            f"{lean_term(proof.witness)} {lean_proof(proof.equality)})"
        )
    else:
        _type(f"unknown-proof-term:{type(proof).__name__}")
    logger.debug("lean_proof exit result=%s", result)
    return result


def render_resonance_lean(theorem: IntrinsicResonanceTheorem) -> str:
    """Render the exact canonical theorem, including its artifact digest."""
    logger.debug("render_resonance_lean entry theorem=%r", theorem.theorem_id)
    if not verify_intrinsic_theorem_binding(theorem):
        logger.error("render_resonance_lean rejected theorem/artifact drift")
        _value("noncanonical-intrinsic-resonance-theorem")
    statement, proof = lean_prop(theorem.statement), lean_proof(theorem.proof)
    digest = theorem.artifact.proof_digest
    result = f'''import VeyraProofSoundness

/- Generated from the canonically replayed Python proof artifact. -/
namespace VeyraProof
open Veyra

def resonanceArtifactDigest : String := "{digest}"
def emptyEnv : Env 0 := fun index => Fin.elim0 index
def resonanceStatement : Formula 0 := {statement}
def resonanceProof : Proof 0 := {proof}

theorem THM_R7_002_resonance_proof_accepted : check [] resonanceProof resonanceStatement = true := by rfl
theorem THM_R7_003_checked_reflexive_resonance : Semantics emptyEnv resonanceStatement := by
  exact THM_R7_001_check_sound emptyEnv (context := []) (proof := resonanceProof)
    (goal := resonanceStatement) trivial THM_R7_002_resonance_proof_accepted
theorem THM_R7_004_every_recurrence_resonates_with_itself :
    ∀ recurrence : Recurrence, resonates recurrence recurrence :=
  THM_R7_003_checked_reflexive_resonance

end VeyraProof
'''
    logger.debug("render_resonance_lean exit bytes=%d", len(result.encode()))
    return result
