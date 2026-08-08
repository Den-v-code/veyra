import VeyraPadicCompletion

set_option autoImplicit false

/-- The total prime-power residue coordinate of one exact integer. -/
def veyraIntegerResidue {p : Nat} (hp : VeyraPrimeWitness p)
    (z : Int) (n : Nat) : VeyraZMod hp n := by
  letI : NeZero (veyraModulus p n) :=
    ⟨Nat.ne_of_gt (veyraModulusPos hp n)⟩
  exact Fin.intCast z

/-- Every natural depth has the exact integer residue coordinate. -/
theorem THM_P3N1_001_integer_residue_total {p : Nat}
    (hp : VeyraPrimeWitness p) (z : Int) :
    forall n : Nat, exists r : VeyraZMod hp n,
      r = veyraIntegerResidue hp z n := by
  intro n
  exact ⟨veyraIntegerResidue hp z n, rfl⟩

/-- Integer residues commute with every canonical coarse reduction. -/
theorem THM_P3N1_002_integer_residue_reduction {p : Nat}
    (hp : VeyraPrimeWitness p) (z : Int) (m n : Nat) (h : m <= n) :
    veyraReduce hp h (veyraIntegerResidue hp z n) =
      veyraIntegerResidue hp z m := by
  cases z with
  | ofNat a =>
      apply Fin.ext
      simp [veyraReduce, veyraIntegerResidue, Fin.intCast,
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

/-- The extensional compatible all-depth family induced by an integer. -/
def veyraIntegerFamily {p : Nat} (hp : VeyraPrimeWitness p)
    (z : Int) : VeyraCompatibleFamily hp :=
  ⟨veyraIntegerResidue hp z,
    fun m n h => THM_P3N1_002_integer_residue_reduction hp z m n h⟩

/-- Introduce that exact family and expose every coordinate equation. -/
theorem THM_P3N1_003_integer_family_introduction {p : Nat}
    (hp : VeyraPrimeWitness p) (z : Int) :
    exists f : VeyraCompatibleFamily hp,
      f = veyraIntegerFamily hp z /\
        forall n, f.val n = veyraIntegerResidue hp z n := by
  exact ⟨veyraIntegerFamily hp z, rfl, fun _ => rfl⟩

#print axioms THM_P3N1_001_integer_residue_total
#print axioms THM_P3N1_002_integer_residue_reduction
#print axioms THM_P3N1_003_integer_family_introduction
