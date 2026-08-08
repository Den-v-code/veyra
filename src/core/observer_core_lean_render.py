"""Deterministic Lean export for the exact canonical R11 observer artifact."""
from __future__ import annotations

from hashlib import sha256
import json
import logging
import re
from typing import NoReturn

from .observer_core_artifact import (
    ObserverProofArtifact,
    make_observer_proof_artifact,
    verify_observer_proof_artifact,
)
from .observer_core_codec import canonical_observer_bytes, observer_digest
from .observer_core_kernel import crest_observer, infer_observer_proof
from .observer_core_proof_types import CrestPulseEcho
from .observer_core_support import outcome_data
from .observer_core_types import Echo, Mark, MarkValue
from .proof_core_codec import canonical_json
from .proof_core_types import ProofContext, Pulse, Silence

logger = logging.getLogger(__name__)
CANONICAL_THEOREM_ID = "THM-R11-006"
_DIGEST = re.compile(r"[0-9a-f]{64}")


def _reject(reason: str) -> NoReturn:
    logger.error("observer_core_lean_render rejected reason=%s", reason)
    raise ValueError(reason)


def canonical_observer_proof() -> CrestPulseEcho:
    """Return the fixed non-collapse proof; no theorem-name dispatch exists."""
    logger.debug("canonical_observer_proof entry")
    result = CrestPulseEcho(Silence(), Pulse(Silence()))
    logger.debug("canonical_observer_proof exit")
    return result


def canonical_observer_artifact() -> ObserverProofArtifact:
    """Replay the fixed proof into its complete ordered R11 artifact."""
    logger.debug("canonical_observer_artifact entry")
    result = make_observer_proof_artifact(
        CANONICAL_THEOREM_ID, ProofContext(), canonical_observer_proof(),
    )
    logger.debug("canonical_observer_artifact exit digest=%s", result.proof_digest)
    return result


def _lean_strings(values: tuple[str, ...]) -> str:
    logger.debug("observer_core_lean_render._lean_strings entry count=%d", len(values))
    if any(type(value) is not str for value in values):
        _reject("r11-invalid-lean-string-list")
    result = "[" + ", ".join(json.dumps(value) for value in values) + "]"
    logger.debug("observer_core_lean_render._lean_strings exit bytes=%d", len(result))
    return result


def render_observer_core_lean(
    artifact: ObserverProofArtifact, r10_binding_digest: str,
) -> str:
    """Render only the exact replayed canonical artifact and R10 continuity digest."""
    logger.debug(
        "render_observer_core_lean entry artifact=%s binding=%s",
        type(artifact).__name__, type(r10_binding_digest).__name__,
    )
    if type(artifact) is not ObserverProofArtifact:
        _reject("r11-invalid-observer-artifact-type")
    if type(r10_binding_digest) is not str:
        _reject("r11-invalid-r10-binding-digest")
    logger.debug(
        "render_observer_core_lean validated theorem=%r r10=%s",
        artifact.theorem_id, r10_binding_digest[:12],
    )
    proof = canonical_observer_proof()
    expected = canonical_observer_artifact()
    checked = verify_observer_proof_artifact(artifact, ProofContext(), proof)
    if not checked.ok or type(artifact) is not ObserverProofArtifact or artifact != expected:
        _reject("r11-noncanonical-observer-artifact")
    if not _DIGEST.fullmatch(r10_binding_digest):
        _reject("r11-invalid-r10-binding-digest")
    judgment = infer_observer_proof(ProofContext(), proof)
    outcome = judgment.outcome
    if (
        type(outcome) is not Echo
        or type(outcome.value) is not MarkValue
        or outcome.value.mark is not Mark.PULSE
    ):
        _reject("r11-canonical-outcome-mismatch")
    observer_ast_digest = observer_digest(crest_observer())
    observer_ast_bytes = canonical_observer_bytes(crest_observer())
    result_bytes = canonical_json(outcome_data(outcome)).encode()
    observer_result_digest = sha256(result_bytes).hexdigest()
    support = _lean_strings(artifact.support)
    result = f'''import VeyraObserverProof

/- Generated from one replayed R11 artifact and an independently verified R10 report. -/
namespace VeyraObserverExport
open Veyra
open VeyraObserver

def theoremIds : List String :=
  ["THM-R11-001", "THM-R11-002", "THM-R11-003",
   "THM-R11-004", "THM-R11-005", "THM-R11-006"]
def observerAstDigest : String := "{observer_ast_digest}"
def observerAstBytes : Nat := {len(observer_ast_bytes)}
def observerResultDigest : String := "{observer_result_digest}"
def observerResultBytes : Nat := {len(result_bytes)}
def observerArtifactDigest : String := "{artifact.proof_digest}"
def observerArtifactRoot : String := "{artifact.root_id}"
def observerArtifactRules : List String := {_lean_strings(artifact.rule_closure)}
def observerArtifactLaws : List String := {_lean_strings(artifact.observer_law_closure)}
def observerArtifactSupport : List String := {support}
def r10BindingDigest : String := "{r10_binding_digest}"

def canonicalObserver : Observer .recurrence .mark := crestObserver
def canonicalLeft : Recurrence := .pulse .silence
def canonicalRight : Recurrence := .pulse (.pulse .silence)
def canonicalResult : EchoOutcome .mark := .echo (.mark .pulse)

theorem canonicalOutcomeAndSeparation :
    echo canonicalObserver canonicalLeft canonicalRight = canonicalResult ∧
      canonicalLeft ≠ canonicalRight :=
  THM_R11_006_crest_noncollapse_witness

#check THM_R11_001_ready_echo_characterization
#check THM_R11_002_ready_domain_reflexivity
#check THM_R11_003_r7_equality_implies_ready_echo
#check THM_R11_004_tail_silence_obstruction
#check THM_R11_005_both_side_echo_domain_obstruction
#check THM_R11_006_crest_noncollapse_witness

end VeyraObserverExport
'''
    logger.debug("render_observer_core_lean exit bytes=%d", len(result.encode()))
    return result


def canonical_observer_lean(
    artifact: ObserverProofArtifact, r10_binding_digest: str,
) -> bytes:
    """Return canonical UTF-8 bytes for immutable snapshot capture."""
    logger.debug("canonical_observer_lean entry")
    result = render_observer_core_lean(artifact, r10_binding_digest).encode()
    logger.debug("canonical_observer_lean exit bytes=%d", len(result))
    return result
