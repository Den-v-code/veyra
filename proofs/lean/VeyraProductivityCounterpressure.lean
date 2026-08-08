import Lean.Elab.Tactic.Omega

/-!
# D2 productivity counterpressure

Foundation-relative countermodels to three precise finite-to-universal
implications.  The file constructs no all-depth family or completed carrier.
-/

set_option autoImplicit false

namespace VeyraProductivityCounterpressure

def descendingRow (d : Nat) : Fin d → Nat :=
  fun i ↦ d - (i.val + 1)

theorem descendingRow_strict
    (d : Nat) :
    ∀ i j : Fin d, i.val < j.val → descendingRow d j < descendingRow d i := by
  intro i j hij
  simp only [descendingRow]
  omega

/-- Every finite demand has the exact canonical descending row. -/
theorem THM_D2_LEAN_001_finite_strict_descent (d : Nat) :
    ∃ row : Fin d → Nat,
      row = descendingRow d ∧
      ∀ i j : Fin d, i.val < j.val → row j < row i := by
  exact ⟨descendingRow d, rfl, descendingRow_strict d⟩

/-- No infinite `Nat`-valued sequence descends at every successor. -/
theorem THM_D2_LEAN_002_no_infinite_nat_descent :
    ¬ ∃ f : Nat → Nat, ∀ n : Nat, f (n + 1) < f n := by
  rintro ⟨f, hstep⟩
  have bound : ∀ n : Nat, f n + n ≤ f 0 := by
    intro n
    induction n with
    | zero => simp
    | succ n ih =>
        have hs := hstep n
        omega
  have impossible := bound (f 0 + 1)
  omega

def X (n : Nat) : Nat → Prop :=
  fun k ↦ n ≤ k

theorem THM_D2_LEAN_003a_self_mem (n : Nat) : X n n := by
  exact Nat.le_refl n

theorem THM_D2_LEAN_003b_succ_subset (n : Nat) :
    ∀ k : Nat, X (n + 1) k → X n k := by
  intro k hk
  exact Nat.le_trans (Nat.le_succ n) hk

theorem THM_D2_LEAN_003c_diagonal_absence (k : Nat) : ¬ X (k + 1) k := by
  exact Nat.not_succ_le_self k

#print axioms THM_D2_LEAN_001_finite_strict_descent
#print axioms THM_D2_LEAN_002_no_infinite_nat_descent
#print axioms THM_D2_LEAN_003a_self_mem
#print axioms THM_D2_LEAN_003b_succ_subset
#print axioms THM_D2_LEAN_003c_diagonal_absence

end VeyraProductivityCounterpressure
