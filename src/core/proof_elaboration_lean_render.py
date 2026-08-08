"""Deterministic Lean export for one replayed proof-surface elaboration."""
from __future__ import annotations

import logging
from typing import NoReturn

from .proof_core_lean_render import lean_proof, lean_prop
from .proof_dependency_support import DependencyId
from .proof_elaboration_artifact import (
    ProofElaborationArtifact, verify_elaboration_artifact,
)
from .proof_surface_codec import surface_program_data
from .proof_surface_elaborator import ElaboratedProgram

logger = logging.getLogger(__name__)

_LEAN_DEPENDENCY = {
    DependencyId.RECURRENCE_FORMATION: "recurrenceFormation",
    DependencyId.PROPOSITION_FORMATION: "propositionFormation",
    DependencyId.SILENCE_DEFINITION: "silenceDefinition",
    DependencyId.PULSE_DEFINITION: "pulseDefinition",
    DependencyId.STITCH_DEFINITION: "stitchDefinition",
    DependencyId.WEAVE_DEFINITION: "weaveDefinition",
    DependencyId.EQUAL_DEFINITION: "equalDefinition",
    DependencyId.IMPLIES_DEFINITION: "impliesDefinition",
    DependencyId.FORALL_DEFINITION: "forallDefinition",
    DependencyId.RESONATES_DEFINITION: "resonatesDefinition",
    DependencyId.ASSUME_RULE: "assumeRule",
    DependencyId.IMP_INTRO_RULE: "impIntroRule",
    DependencyId.IMP_ELIM_RULE: "impElimRule",
    DependencyId.FORALL_INTRO_RULE: "forallIntroRule",
    DependencyId.FORALL_ELIM_RULE: "forallElimRule",
    DependencyId.EQ_REFL_RULE: "eqReflRule",
    DependencyId.EQ_SYM_RULE: "eqSymRule",
    DependencyId.EQ_TRANS_RULE: "eqTransRule",
    DependencyId.RESONANCE_INTRO_RULE: "resonanceIntroRule",
    DependencyId.STITCH_SILENCE_LEFT_LAW: "stitchSilenceLeftLaw",
    DependencyId.STITCH_SILENCE_RIGHT_LAW: "stitchSilenceRightLaw",
    DependencyId.WEAVE_SILENCE_RIGHT_LAW: "weaveSilenceRightLaw",
    DependencyId.WEAVE_PULSE_LAW: "weavePulseLaw",
    DependencyId.WEAVE_UNIT_RIGHT_LAW: "weaveUnitRightLaw",
    DependencyId.INTRINSIC_MODE_OBSERVER: "intrinsicModeObserver",
    DependencyId.FOREIGN_MODE_OBSTRUCTION: "foreignModeObstruction",
}


def _reject(reason: str) -> NoReturn:
    logger.error("proof_elaboration_lean_render rejected reason=%s", reason)
    raise ValueError(reason)


def _lean_list(items: tuple[DependencyId, ...]) -> str:
    logger.debug("proof_elaboration_lean_render._lean_list entry count=%d", len(items))
    try:
        result = "[" + ", ".join(f".{_LEAN_DEPENDENCY[item]}" for item in items) + "]"
    except KeyError as exc:
        logger.error("proof_elaboration_lean_render unknown dependency=%r", exc.args[0])
        _reject("unsupported-lean-dependency-id")
    logger.debug("proof_elaboration_lean_render._lean_list exit bytes=%d", len(result))
    return result


def render_elaboration_lean(
    artifact: ProofElaborationArtifact,
    source: bytes,
    elaborated: ElaboratedProgram,
) -> str:
    """Render exact proof acceptance, image soundness, and support parity checks."""
    logger.debug("render_elaboration_lean entry theorem=%r", getattr(artifact, "theorem_id", None))
    if type(elaborated) is not ElaboratedProgram:
        raise TypeError("invalid-elaborated-program")
    checked = verify_elaboration_artifact(
        artifact,
        source,
        surface_program_data(elaborated.surface),
        elaborated.claim,
        elaborated.proof,
    )
    if not checked.ok:
        _reject("noncanonical-elaboration-artifact")
    support_values = tuple(
        DependencyId(value)
        for _, values in artifact.dependency_support
        for value in values
    )
    catalog = _lean_list(tuple(DependencyId))
    support = _lean_list(support_values)
    statement = lean_prop(elaborated.claim)
    proof = lean_proof(elaborated.proof)
    result = f'''import VeyraElaborationSemantics

/- Generated from one source-replayed, kernel-checked R10 elaboration artifact. -/
namespace VeyraElaborationExport
open VeyraProof
open VeyraElaboration

def sourceDigest : String := "{artifact.source_digest}"
def surfaceSyntaxDigest : String := "{artifact.surface_syntax_digest}"
def semanticDigest : String := "{artifact.semantic_digest}"
def r7ArtifactDigest : String := "{artifact.r7_artifact_digest}"
def r9BindingDigest : String := "{artifact.r9_binding_digest}"
def elaborationBindingDigest : String := "{artifact.binding_digest}"
def elaboratedStatement : Formula 0 := {statement}
def elaboratedProof : Proof 0 := {proof}
def dependencyCatalog : List DependencyId := {catalog}
def declaredSupportIds : List DependencyId := {support}
def supportBits (support : DependencySupport) : List Bool :=
  dependencyCatalog.map fun dependency => support.contains dependency

theorem THM_R10_003_elaborated_proof_accepted :
    check [] elaboratedProof elaboratedStatement = true := by decide

def elaborationEmptyEnv : Env 0 := fun index => Fin.elim0 index

theorem THM_R10_004_elaborated_image_sound :
    ImageSemantics elaborationEmptyEnv elaboratedStatement := by
  exact THM_R10_002_checked_elaboration_image_sound elaborationEmptyEnv
    (context := []) (proof := elaboratedProof) (goal := elaboratedStatement)
    trivial THM_R10_003_elaborated_proof_accepted

theorem THM_R10_005_structural_support_matches :
    supportBits (elaborationSupport elaboratedProof elaboratedStatement) =
      supportBits (dependencies declaredSupportIds) := by decide

end VeyraElaborationExport
'''
    logger.debug("render_elaboration_lean exit bytes=%d", len(result.encode()))
    return result
