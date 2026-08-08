"""Canonical source-replayed R10 elaboration used by the immutable bridge."""
from __future__ import annotations

import logging

from .proof_elaboration_artifact import (
    ProofElaborationArtifact, make_surface_elaboration_artifact,
)
from .proof_elaboration_lean_render import render_elaboration_lean
from .proof_surface_elaborator import ElaboratedProgram, compile_surface_program

logger = logging.getLogger(__name__)
THEOREM_ID = "THM-R7-004"
CANONICAL_SOURCE = b"""(veyra-proof 1
  (claim (forall item recurrence
    (resonates (var item) (var item))))
  (proof (forall-intro item recurrence
    (resonance-intro (var item) (var item) (pulse (silence))
      (native-law weave-unit-right (var item))))))"""


def canonical_elaboration() -> tuple[ProofElaborationArtifact, ElaboratedProgram]:
    """Reparse and replay the exact source; no theorem-name dispatch is used."""
    logger.debug("canonical_elaboration entry source_bytes=%d", len(CANONICAL_SOURCE))
    elaborated = compile_surface_program(CANONICAL_SOURCE.decode("ascii"))
    artifact = make_surface_elaboration_artifact(
        THEOREM_ID, CANONICAL_SOURCE, elaborated,
    )
    result = artifact, elaborated
    logger.debug("canonical_elaboration exit binding=%s", artifact.binding_digest)
    return result


def canonical_elaboration_lean() -> bytes:
    """Render Lean only from the independently replayed canonical source artifact."""
    logger.debug("canonical_elaboration_lean entry")
    artifact, elaborated = canonical_elaboration()
    result = render_elaboration_lean(
        artifact, CANONICAL_SOURCE, elaborated,
    ).encode("utf-8")
    logger.debug("canonical_elaboration_lean exit bytes=%d", len(result))
    return result
