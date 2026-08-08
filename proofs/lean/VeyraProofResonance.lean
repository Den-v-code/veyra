import VeyraProofSoundness

/- Generated from the canonically replayed Python proof artifact. -/
namespace VeyraProof
open Veyra

def resonanceArtifactDigest : String := "aca33a6a76af8b0f9958e722a11133dc851876ba718dce59c2486fba8232e362"
def emptyEnv : Env 0 := fun index => Fin.elim0 index
def resonanceStatement : Formula 0 := (.forallE .recurrence (.resonates (.var ⟨0, by decide⟩) (.var ⟨0, by decide⟩)))
def resonanceProof : Proof 0 := (.forallIntro .recurrence (.resonanceIntro (.var ⟨0, by decide⟩) (.var ⟨0, by decide⟩) (.pulse .silence) (.nativeLaw .weaveUnitRight [(.var ⟨0, by decide⟩)])))

theorem THM_R7_002_resonance_proof_accepted : check [] resonanceProof resonanceStatement = true := by rfl
theorem THM_R7_003_checked_reflexive_resonance : Semantics emptyEnv resonanceStatement := by
  exact THM_R7_001_check_sound emptyEnv (context := []) (proof := resonanceProof)
    (goal := resonanceStatement) trivial THM_R7_002_resonance_proof_accepted
theorem THM_R7_004_every_recurrence_resonates_with_itself :
    ∀ recurrence : Recurrence, resonates recurrence recurrence :=
  THM_R7_003_checked_reflexive_resonance

end VeyraProof
