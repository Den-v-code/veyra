"""Deterministic Lean renderer binding R7 resonance to the R9 native image."""
from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Mapping

logger = logging.getLogger(__name__)
REQUIRED_DIGESTS = (
    "python_transport", "python_laws", "native_runtime", "intrinsic_arithmetic",
    "proof_core_types", "lean_intrinsic_runtime", "lean_transport",
)
THEOREM_IDS = tuple(f"THM-R9-{index:03d}" for index in range(1, 9))


def render_mode_transport_lean(
    r7_artifact_digest: str, source_digests: Mapping[str, str],
) -> str:
    """Render the composite theorem only from exact pre-hashed reviewed inputs."""
    logger.debug("render_mode_transport_lean entry digests=%d", len(source_digests))
    frozen = MappingProxyType(dict(source_digests))
    if tuple(frozen) != REQUIRED_DIGESTS:
        logger.error("render_mode_transport_lean invalid source keys=%r", tuple(frozen))
        raise ValueError("invalid-r9-render-source-digests")
    if len(r7_artifact_digest) != 64 or any(len(frozen[key]) != 64 for key in REQUIRED_DIGESTS):
        logger.error("render_mode_transport_lean invalid digest shape")
        raise ValueError("invalid-r9-render-digest")
    result = f'''import VeyraProofResonance
import VeyraRecurrenceModeBridge

/- Generated composite export: the checked R7 theorem transported to the exact R9 image. -/
namespace VeyraTransport
open Veyra

def r7ArtifactDigest : String := "{r7_artifact_digest}"
def pythonTransportDigest : String := "{frozen['python_transport']}"
def pythonLawsDigest : String := "{frozen['python_laws']}"
def nativeRuntimeDigest : String := "{frozen['native_runtime']}"
def intrinsicArithmeticDigest : String := "{frozen['intrinsic_arithmetic']}"
def proofCoreTypesDigest : String := "{frozen['proof_core_types']}"
def intrinsicRuntimeLeanDigest : String := "{frozen['lean_intrinsic_runtime']}"
def recurrenceModeBridgeDigest : String := "{frozen['lean_transport']}"

#check THM_R9_001_encode_mode_ready
#check THM_R9_002_decode_encode
#check THM_R9_003_encode_decode
#check THM_R9_004_encode_injective
#check THM_R9_005_stitch_preserved
#check THM_R9_006_weave_preserved
#check THM_R9_007_resonance_transport

theorem THM_R9_008_R7_reflexive_resonance_transport :
    ∀ recurrence : Recurrence,
      IntrinsicResonates (intrinsicMode recurrence) (intrinsicMode recurrence) := by
  intro recurrence
  exact (THM_R9_007_resonance_transport recurrence recurrence).mp
    (VeyraProof.THM_R7_004_every_recurrence_resonates_with_itself recurrence)

#check THM_R9_008_R7_reflexive_resonance_transport
def transportTheoremIds : List String :=
  ["THM-R9-001", "THM-R9-002", "THM-R9-003", "THM-R9-004",
   "THM-R9-005", "THM-R9-006", "THM-R9-007", "THM-R9-008"]

end VeyraTransport
'''
    logger.debug("render_mode_transport_lean exit bytes=%d", len(result.encode()))
    return result
