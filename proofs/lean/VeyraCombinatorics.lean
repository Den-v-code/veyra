namespace Veyra

/- A finite Pascal recurrence, used only for the fixed card below. -/
def choose : Nat → Nat → Nat
  | _, 0 => 1
  | 0, _ + 1 => 0
  | n + 1, k + 1 => choose n k + choose n (k + 1)

-- theorem-card: fixed-binomial-symmetry-6-2
-- This certifies only the displayed finite computation, not general symmetry.
theorem THM_B001_binomial_symmetry_6_2 :
    choose 6 2 = choose 6 4 ∧ choose 6 2 = 15 ∧ choose 6 4 = 15 := by
  decide

#check THM_B001_binomial_symmetry_6_2

end Veyra
