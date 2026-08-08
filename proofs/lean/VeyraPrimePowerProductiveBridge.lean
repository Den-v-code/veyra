import VeyraPadicFamilyIntroduction

set_option autoImplicit false

/-- The one-constructor closed program output, defined independently of N1. -/
def veyraResidueProgramOutput {p : Nat} (hp : VeyraPrimeWitness p)
    (z : Int) (n : Nat) : VeyraZMod hp n := by
  letI : NeZero (veyraModulus p n) :=
    ⟨Nat.ne_of_gt (veyraModulusPos hp n)⟩
  exact Fin.intCast z

/-- Operational evaluation for the closed prime-power residue program. -/
def veyraResidueProgramEval {p : Nat} (hp : VeyraPrimeWitness p)
    (z : Int) (n : Nat) (r : VeyraZMod hp n) : Prop :=
  r = veyraResidueProgramOutput hp z n

theorem THM_P3A1B_001_total {p : Nat} (hp : VeyraPrimeWitness p) (z : Int) :
    forall n, exists r : VeyraZMod hp n,
      veyraResidueProgramEval hp z n r := by
  intro n
  exact ⟨veyraResidueProgramOutput hp z n, rfl⟩

theorem THM_P3A1B_002_deterministic {p : Nat} (hp : VeyraPrimeWitness p)
    (z : Int) (n : Nat) (r s : VeyraZMod hp n) :
    veyraResidueProgramEval hp z n r ->
      veyraResidueProgramEval hp z n s -> r = s := by
  intro hr hs
  exact hr.trans hs.symm

/-- Coherence follows from program semantics, not from the N1 family theorem. -/
theorem THM_P3A1B_003_process_coherent {p : Nat}
    (hp : VeyraPrimeWitness p) (z : Int) (m n : Nat) (h : m <= n)
    (r : VeyraZMod hp n) (s : VeyraZMod hp m) :
    veyraResidueProgramEval hp z n r ->
      veyraResidueProgramEval hp z m s -> veyraReduce hp h r = s := by
  intro hr hs
  rw [hr, hs]
  cases z with
  | ofNat a =>
      apply Fin.ext
      simp [veyraReduce, veyraResidueProgramOutput, Fin.intCast,
        Nat.mod_mod_of_dvd, veyraModulusDvd hp m n h]
  | negSucc a =>
      letI : NeZero (veyraModulus p n) :=
        ⟨Nat.ne_of_gt (veyraModulusPos hp n)⟩
      letI : NeZero (veyraModulus p m) :=
        ⟨Nat.ne_of_gt (veyraModulusPos hp m)⟩
      let ops := veyraCanonicalStageRingLaws hp
      change veyraReduce hp h
        (ops.neg n (Fin.ofNat (veyraModulus p n) (a + 1))) =
          ops.neg m (Fin.ofNat (veyraModulus p m) (a + 1))
      rw [ops.reduce_neg]
      congr 1
      apply Fin.ext
      simp [veyraReduce, Nat.mod_mod_of_dvd,
        veyraModulusDvd hp m n h]

/-- The exact operational process commutes with the direct N1 family. -/
theorem THM_P3A1B_004_commutes {p : Nat} (hp : VeyraPrimeWitness p)
    (z : Int) : forall n,
    veyraResidueProgramEval hp z n ((veyraIntegerFamily hp z).val n) := by
  intro n
  rfl

#print axioms THM_P3A1B_001_total
#print axioms THM_P3A1B_002_deterministic
#print axioms THM_P3A1B_003_process_coherent
#print axioms THM_P3A1B_004_commutes
