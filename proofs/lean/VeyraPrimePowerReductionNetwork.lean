import VeyraPadicFamilyIntroduction

set_option autoImplicit false

/-!
P3-N2's symbolic lane.  This file deliberately imports only the raw prime-power
definitions and the direct integer-family introduction.  In particular it does
not consume the final completion bundle, a completed-carrier judgment, or P3-C2.
-/

/-- The canonical thin arrow from depth `n` to depth `m` remembers only `m <= n`. -/
structure VeyraReductionArrow (m n : Nat) where
  comparable : m <= n

/-- Evaluation of a thin reduction arrow is the arithmetic residue map. -/
def veyraReductionArrowMap {p : Nat} (hp : VeyraPrimeWitness p)
    {m n : Nat} (arrow : VeyraReductionArrow m n) :
    VeyraZMod hp n -> VeyraZMod hp m :=
  veyraReduce hp arrow.comparable

/-- A finite composable path, oriented from one fine depth to one coarse depth. -/
inductive VeyraReductionPath : (fine coarse : Nat) -> Type where
  | nil (n : Nat) : VeyraReductionPath n n
  | step {fine middle coarse : Nat} (path : VeyraReductionPath fine middle)
      (comparable : coarse <= middle) : VeyraReductionPath fine coarse

/-- Endpoint comparability derived from every finite path. -/
def veyraReductionPathComparable {fine coarse : Nat}
    (path : VeyraReductionPath fine coarse) : coarse <= fine :=
  match path with
  | .nil _ => Nat.le_refl fine
  | .step prior h => Nat.le_trans h (veyraReductionPathComparable prior)

/-- Elaborate a finite thin path to its canonical endpoint reduction map. -/
def veyraReductionPathMap {p : Nat} (hp : VeyraPrimeWitness p)
    {fine coarse : Nat} (path : VeyraReductionPath fine coarse) :
    VeyraZMod hp fine -> VeyraZMod hp coarse :=
  match path with
  | .nil _ => id
  | .step prior h =>
      veyraReductionArrowMap hp (VeyraReductionArrow.mk h) ∘
        veyraReductionPathMap hp prior

/-- Every identity arrow evaluates extensionally to the identity map. -/
theorem THM_P3N2_001_reduction_identity {p : Nat} (hp : VeyraPrimeWitness p)
    (n : Nat) :
    veyraReductionArrowMap hp (VeyraReductionArrow.mk (Nat.le_refl n)) = id := by
  funext x
  exact THM_POMEGA2_004_reduction_identity hp n x

/-- Evaluation respects composition for every `k <= m <= n`. -/
theorem THM_P3N2_002_reduction_composition {p : Nat}
    (hp : VeyraPrimeWitness p) (k m n : Nat) (hkm : k <= m) (hmn : m <= n) :
    veyraReductionArrowMap hp (VeyraReductionArrow.mk hkm) ∘
        veyraReductionArrowMap hp (VeyraReductionArrow.mk hmn) =
      veyraReductionArrowMap hp (VeyraReductionArrow.mk (Nat.le_trans hkm hmn)) := by
  funext x
  exact THM_POMEGA2_005_reduction_composition hp k m n hkm hmn x

/-- Comparison-proof witnesses cannot change the canonical reduction map. -/
theorem THM_P3N2_003_reduction_witness_independent {p : Nat}
    (hp : VeyraPrimeWitness p) (m n : Nat) (h₁ h₂ : m <= n) :
    veyraReductionArrowMap hp (VeyraReductionArrow.mk h₁) =
      veyraReductionArrowMap hp (VeyraReductionArrow.mk h₂) := by
  funext x
  apply Fin.ext
  rfl

/-- Every finite path evaluates to the canonical endpoint reduction. -/
theorem veyraReductionPathMap_canonical {p : Nat} (hp : VeyraPrimeWitness p)
    {fine coarse : Nat} (path : VeyraReductionPath fine coarse) :
    veyraReductionPathMap hp path =
      veyraReductionArrowMap hp
        (VeyraReductionArrow.mk (veyraReductionPathComparable path)) := by
  induction path with
  | nil =>
      simpa [veyraReductionPathMap, veyraReductionPathComparable] using
        (THM_P3N2_001_reduction_identity hp _).symm
  | step prior h ih =>
      calc
        veyraReductionPathMap hp (.step prior h) =
            veyraReductionArrowMap hp (VeyraReductionArrow.mk h) ∘
              veyraReductionPathMap hp prior := rfl
        _ = veyraReductionArrowMap hp (VeyraReductionArrow.mk h) ∘
              veyraReductionArrowMap hp
                (VeyraReductionArrow.mk (veyraReductionPathComparable prior)) := by rw [ih]
        _ = veyraReductionArrowMap hp
              (VeyraReductionArrow.mk
                (Nat.le_trans h (veyraReductionPathComparable prior))) :=
              THM_P3N2_002_reduction_composition hp _ _ _ h
                (veyraReductionPathComparable prior)
        _ = veyraReductionArrowMap hp
              (VeyraReductionArrow.mk
                (veyraReductionPathComparable (.step prior h))) := rfl

/-- Any two arbitrary finite thin-tower paths with the same endpoints have equal maps. -/
theorem THM_P3N2_004_path_equality {p : Nat} (hp : VeyraPrimeWitness p)
    (fine coarse : Nat) (left right : VeyraReductionPath fine coarse) :
    veyraReductionPathMap hp left = veyraReductionPathMap hp right := by
  calc
    veyraReductionPathMap hp left = veyraReductionArrowMap hp
        (VeyraReductionArrow.mk (veyraReductionPathComparable left)) :=
      veyraReductionPathMap_canonical hp left
    _ = veyraReductionArrowMap hp
        (VeyraReductionArrow.mk (veyraReductionPathComparable right)) :=
      THM_P3N2_003_reduction_witness_independent hp coarse fine
        (veyraReductionPathComparable left) (veyraReductionPathComparable right)
    _ = veyraReductionPathMap hp right :=
      (veyraReductionPathMap_canonical hp right).symm

/-- Every compatible-family observation square commutes at all depths. -/
theorem THM_P3N2_005_rho_square {p : Nat} {hp : VeyraPrimeWitness p}
    (x : VeyraCompatibleFamily hp) (m n : Nat) (h : m <= n) :
    veyraReductionArrowMap hp (VeyraReductionArrow.mk h) (veyraRho n x) =
      veyraRho m x :=
  x.property m n h

/-- The direct integer separator `0,p^(m+1)` collapses at the coarse depth. -/
theorem THM_P3N2_006_separator_coarse {p : Nat} (hp : VeyraPrimeWitness p)
    (m : Nat) :
    veyraRho m (veyraIntegerFamily hp 0) =
      veyraRho m (veyraIntegerFamily hp (Int.ofNat (veyraModulus p m))) := by
  apply Fin.ext
  simp [veyraRho, veyraIntegerFamily, veyraIntegerResidue, Fin.intCast]

/-- The same direct integer separator remains distinct at every finer depth. -/
theorem THM_P3N2_007_separator_fine {p : Nat} (hp : VeyraPrimeWitness p)
    (m n : Nat) (h : m < n) :
    veyraRho n (veyraIntegerFamily hp 0) ≠
      veyraRho n (veyraIntegerFamily hp (Int.ofNat (veyraModulus p m))) := by
  have hpone : 1 < p := Nat.lt_of_lt_of_le Nat.one_lt_two hp.two_le
  have hmod : veyraModulus p m < veyraModulus p n :=
    Nat.pow_lt_pow_right hpone (Nat.add_lt_add_right h 1)
  intro equal
  have valuesEqual : 0 = veyraModulus p m := by
    have := congrArg Fin.val equal
    simp [veyraRho, veyraIntegerFamily, veyraIntegerResidue, Fin.intCast] at this
    rw [Nat.mod_eq_of_lt hmod] at this
    exact this
  exact (Nat.ne_of_gt (veyraModulusPos hp m)) valuesEqual.symm

#print axioms THM_P3N2_001_reduction_identity
#print axioms THM_P3N2_002_reduction_composition
#print axioms THM_P3N2_003_reduction_witness_independent
#print axioms THM_P3N2_004_path_equality
#print axioms THM_P3N2_005_rho_square
#print axioms THM_P3N2_006_separator_coarse
#print axioms THM_P3N2_007_separator_fine
