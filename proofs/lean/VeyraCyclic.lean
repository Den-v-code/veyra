namespace Veyra

-- theorem-card: cyclic-period
-- Advancing a finite phase by its modulus returns the same phase shadow.
theorem THM_C001_cyclic_period (phase modulus : Nat) :
    (phase + modulus) % modulus = phase % modulus := by
  rw [Nat.add_mod]
  simp

-- theorem-card: chord-symmetry
-- Fixed phase shell only: anchor 0 mod 12, phases 3 and 9 have shortest
-- distance 3, numerator 108, and equal chord shadows 108/144 = 3/4.
theorem THM_C002_chord_symmetry_12_0_3_9 :
    Nat.min 3 (12 - 3) = 3 ∧ Nat.min 9 (12 - 9) = 3 ∧
    4 * 3 * (12 - 3) = 108 ∧ 4 * (12 - 9) * (12 - (12 - 9)) = 108 ∧
    4 * 3 * (12 - 3) = 4 * (12 - 9) * (12 - (12 - 9)) ∧
    108 * 4 = 3 * (12 * 12) := by
  decide

#check THM_C002_chord_symmetry_12_0_3_9

end Veyra
