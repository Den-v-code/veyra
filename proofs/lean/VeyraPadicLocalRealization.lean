import VeyraPadicFamilyIntroduction

set_option autoImplicit false

/-- Realize the exact N1 integer family using only PΩ2 universal realization. -/
theorem THM_P3N3_001_realize_integer_family {p : Nat}
    (hp : VeyraPrimeWitness p) (z : Int) :
    exists x : ZpVeyra hp,
      forall n, veyraRho n x = (veyraIntegerFamily hp z).val n :=
  THM_POMEGA2_007_universal_realization (veyraIntegerFamily hp z)

/-- Expose the all-depth equation carried by the THM007 witness. -/
theorem THM_P3N3_002_realized_integer_family_coordinate {p : Nat}
    (hp : VeyraPrimeWitness p) (z : Int) :
    exists x : ZpVeyra hp,
      forall n, veyraRho n x = (veyraIntegerFamily hp z).val n := by
  obtain ⟨x, hx⟩ := THM_P3N3_001_realize_integer_family hp z
  exact ⟨x, hx⟩

/-- Joint separation yields equality only inside this exact carrier. -/
theorem THM_P3N4_001_scoped_joint_separation {p : Nat}
    {hp : VeyraPrimeWitness p} (x y : ZpVeyra hp)
    (h : forall n, veyraRho n x = veyraRho n y) : x = y :=
  THM_POMEGA2_009_joint_separation x y h

#print axioms THM_P3N3_001_realize_integer_family
#print axioms THM_P3N3_002_realized_integer_family_coordinate
#print axioms THM_P3N4_001_scoped_joint_separation
