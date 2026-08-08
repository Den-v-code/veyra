import VeyraPrimePowerUnbounded

set_option autoImplicit false

/-- One canonical request-bound late distinction in the prime-power carrier. -/
structure VeyraPrimePowerLateWitness {p : Nat}
    (hp : VeyraPrimeWitness p) (k : Nat) where
  later : Nat
  later_eq : later = k + 1
  left : ZpVeyra hp
  right : ZpVeyra hp
  left_eq : left = veyraIntegerFamily hp 0
  right_eq :
    right = veyraIntegerFamily hp (Int.ofNat (p ^ (k + 1)))
  «prefix» : ∀ n, n ≤ k → veyraRho n left = veyraRho n right
  later_gt : k < later
  separates : veyraRho later left ≠ veyraRho later right

/-- Construct the exact zero/`p^(k+1)` witness using N6 THM001/THM002. -/
def veyraPrimePowerLateWitness {p : Nat}
    (hp : VeyraPrimeWitness p) (k : Nat) :
    VeyraPrimePowerLateWitness hp k where
  later := k + 1
  later_eq := rfl
  left := veyraIntegerFamily hp 0
  right := veyraIntegerFamily hp (Int.ofNat (p ^ (k + 1)))
  left_eq := rfl
  right_eq := rfl
  «prefix» := by
    intro n hn
    exact THM_P3N6_001_prefix_indistinguishable hp k n hn
  later_gt := Nat.lt_succ_self k
  separates := THM_P3N6_002_next_depth_distinguishes hp k

/-- The constructor retains the exact requested depth and exact two carriers. -/
theorem THM_P3N6W_001_exact_shape {p : Nat}
    (hp : VeyraPrimeWitness p) (k : Nat) :
    (veyraPrimePowerLateWitness hp k).later = k + 1 ∧
      (veyraPrimePowerLateWitness hp k).left =
        veyraIntegerFamily hp 0 ∧
      (veyraPrimePowerLateWitness hp k).right =
        veyraIntegerFamily hp (Int.ofNat (p ^ (k + 1))) := by
  exact ⟨rfl, rfl, rfl⟩

/-- Every coordinate through the requested finite prefix agrees. -/
theorem THM_P3N6W_002_prefix {p : Nat}
    (hp : VeyraPrimeWitness p) (k : Nat) :
    ∀ n, n ≤ k →
      veyraRho n (veyraPrimePowerLateWitness hp k).left =
        veyraRho n (veyraPrimePowerLateWitness hp k).right := by
  exact (veyraPrimePowerLateWitness hp k).«prefix»

/-- The canonical immediately later coordinate strictly separates the pair. -/
theorem THM_P3N6W_003_later {p : Nat}
    (hp : VeyraPrimeWitness p) (k : Nat) :
    k < (veyraPrimePowerLateWitness hp k).later ∧
      veyraRho (veyraPrimePowerLateWitness hp k).later
          (veyraPrimePowerLateWitness hp k).left ≠
        veyraRho (veyraPrimePowerLateWitness hp k).later
          (veyraPrimePowerLateWitness hp k).right := by
  exact ⟨(veyraPrimePowerLateWitness hp k).later_gt,
    (veyraPrimePowerLateWitness hp k).separates⟩

/-- A constructive metalanguage constructor for every requested finite depth. -/
theorem THM_P3N6W_004_uniform {p : Nat}
    (hp : VeyraPrimeWitness p) :
    ∀ k, Nonempty (VeyraPrimePowerLateWitness hp k) := by
  intro k
  exact ⟨veyraPrimePowerLateWitness hp k⟩

#print axioms THM_P3N6W_001_exact_shape
#print axioms THM_P3N6W_002_prefix
#print axioms THM_P3N6W_003_later
#print axioms THM_P3N6W_004_uniform
