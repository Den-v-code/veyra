"""Canonical R7 theorem: every intrinsic recurrence resonates with itself."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging

from .proof_core_artifact import ProofArtifact, make_proof_artifact, verify_proof_artifact
from .proof_core_kernel import infer_proof
from .proof_core_types import (
    Bound, CoreType, Forall, ForallIntro, NativeLaw, NativeLawId, ProofContext,
    ProofTerm, Pulse, ResonanceIntro, Resonates, RuleId, Silence,
)

logger = logging.getLogger(__name__)
THEOREM_ID = "THM-R7-004"
BOUNDARY = (
    "general only for intrinsic inductive recurrence resonance witnessed by "
    "weave(r, pulse(silence)) = r; cyclic phase, approximate, weighted, and "
    "profile resonance remain external shadows"
)


@dataclass(frozen=True)
class IntrinsicResonanceTheorem:
    """Checker-derived theorem data and its canonical replayable artifact."""

    theorem_id: str
    statement: Forall
    proof: ProofTerm
    artifact: ProofArtifact
    rule_closure: tuple[RuleId, ...]
    native_law_closure: tuple[NativeLawId, ...]
    status: str
    boundary: str


def intrinsic_resonance_statement() -> Forall:
    """Return ``forall r, intrinsic-resonates(r, r)`` in de Bruijn syntax."""
    logger.debug("intrinsic_resonance_statement entry")
    result = Forall(CoreType.RECURRENCE, Resonates(Bound(0), Bound(0)))
    logger.debug("intrinsic_resonance_statement exit result=%r", result)
    return result


def intrinsic_resonance_proof() -> ProofTerm:
    """Build the proof term; the kernel, not this builder, infers its claim."""
    logger.debug("intrinsic_resonance_proof entry")
    variable, unit = Bound(0), Pulse(Silence())
    equality = NativeLaw(NativeLawId.WEAVE_UNIT_RIGHT, (variable,))
    result: ProofTerm = ForallIntro(
        CoreType.RECURRENCE,
        ResonanceIntro(variable, variable, unit, equality),
    )
    logger.debug("intrinsic_resonance_proof exit result=%r", result)
    return result


@lru_cache(maxsize=1)
def intrinsic_resonance_theorem() -> IntrinsicResonanceTheorem:
    """Replay and bind the unique canonical intrinsic-resonance theorem."""
    logger.debug("intrinsic_resonance_theorem entry")
    proof = intrinsic_resonance_proof()
    judgment = infer_proof(ProofContext(), proof)
    expected = intrinsic_resonance_statement()
    artifact = make_proof_artifact(THEOREM_ID, ProofContext(), proof)
    artifact_check = verify_proof_artifact(artifact)
    valid = judgment.conclusion == expected and artifact_check.ok
    if not valid:
        logger.error(
            "intrinsic_resonance_theorem blocked conclusion=%r errors=%r",
            judgment.conclusion,
            artifact_check.errors,
        )
        raise ValueError("canonical-intrinsic-resonance-proof-invalid")
    result = IntrinsicResonanceTheorem(
        THEOREM_ID,
        expected,
        proof,
        artifact,
        judgment.rule_closure,
        judgment.native_law_closure,
        "kernel-checked",
        BOUNDARY,
    )
    logger.debug(
        "intrinsic_resonance_theorem exit theorem=%s digest=%s",
        result.theorem_id,
        result.artifact.proof_digest,
    )
    return result


def qualifies_as_intrinsic_resonance(artifact: object) -> bool:
    """Accept only the exact replayed R7 artifact, never a finite ledger row."""
    logger.debug("qualifies_as_intrinsic_resonance entry type=%s", type(artifact).__name__)
    canonical = make_proof_artifact(THEOREM_ID, ProofContext(), intrinsic_resonance_proof())
    result = type(artifact) is ProofArtifact and artifact == canonical and verify_proof_artifact(artifact).ok
    logger.debug("qualifies_as_intrinsic_resonance exit result=%s", result)
    return result


def verify_intrinsic_theorem_binding(theorem: object) -> bool:
    """Reject drift between theorem fields and the exact replayed artifact."""
    logger.debug("verify_intrinsic_theorem_binding entry type=%s", type(theorem).__name__)
    if type(theorem) is not IntrinsicResonanceTheorem:
        logger.error("verify_intrinsic_theorem_binding invalid theorem type")
        return False
    proof = intrinsic_resonance_proof()
    statement = intrinsic_resonance_statement()
    judgment = infer_proof(ProofContext(), proof)
    artifact = make_proof_artifact(THEOREM_ID, ProofContext(), proof)
    result = (
        theorem.theorem_id == THEOREM_ID
        and theorem.statement == statement
        and theorem.proof == proof
        and theorem.artifact == artifact
        and theorem.rule_closure == judgment.rule_closure
        and theorem.native_law_closure == judgment.native_law_closure
        and theorem.status == "kernel-checked"
        and theorem.boundary == BOUNDARY
        and qualifies_as_intrinsic_resonance(theorem.artifact)
    )
    if not result:
        logger.error("verify_intrinsic_theorem_binding rejected theorem=%r", theorem)
    logger.debug("verify_intrinsic_theorem_binding exit result=%s", result)
    return result
