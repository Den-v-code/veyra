import VeyraPrimePowerReductionNetwork

set_option autoImplicit false

/-!
Private arithmetic kernel for P3-N0.  These theorems establish only the two
finite residue facts consumed by the model doctrine.  They do not assert that
A-HAP is necessary, that any physical observer is born, or that generic E4 is
available.
-/

/-- `rho_n` distinguishes the freshly introduced integer families `F_0,F_1`. -/
theorem THM_P3N0_001_zero_one_discrimination {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) :
    veyraRho n (veyraIntegerFamily hp 0) ≠
      veyraRho n (veyraIntegerFamily hp 1) := by
  intro equal
  have valuesEqual := congrArg Fin.val equal
  have hpone : 1 < p := Nat.lt_of_lt_of_le Nat.one_lt_two hp.two_le
  have hmod : 1 < veyraModulus p n := by
    simpa [veyraModulus] using Nat.one_lt_pow (Nat.succ_ne_zero n) hpone
  simp [veyraRho, veyraIntegerFamily, veyraIntegerResidue, Fin.intCast,
    Nat.mod_eq_of_lt hmod] at valuesEqual

/-- The strict package's canonical pair agrees at the selected coarse depth. -/
theorem THM_P3N0_002_strict_pair_coarse {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) :
    veyraRho n (veyraIntegerFamily hp 0) =
      veyraRho n (veyraIntegerFamily hp (Int.ofNat (veyraModulus p n))) :=
  THM_P3N2_006_separator_coarse hp n

/-- The same canonical pair separates exactly one level later. -/
theorem THM_P3N0_003_strict_pair_next {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) :
    veyraRho (n + 1) (veyraIntegerFamily hp 0) ≠
      veyraRho (n + 1)
        (veyraIntegerFamily hp (Int.ofNat (veyraModulus p n))) :=
  THM_P3N2_007_separator_fine hp n (n + 1) (Nat.lt_succ_self n)

#print axioms THM_P3N0_001_zero_one_discrimination
#print axioms THM_P3N0_002_strict_pair_coarse
#print axioms THM_P3N0_003_strict_pair_next
