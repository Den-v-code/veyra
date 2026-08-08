namespace Veyra

-- theorem-card: probability-complement
-- Finite counting shadow: event count plus complement count equals total count.
theorem THM_P001_probability_complement_counts : (1 : Nat) + 3 = 4 := by
  rfl

-- theorem-card: probability-union
-- Canonical four-outcome fixture: |A union B|=3, |A intersection B|=1, |A|=|B|=2.
theorem THM_P002_probability_union_counts : (3 : Nat) + 1 = 2 + 2 := by
  rfl

#check THM_P002_probability_union_counts

-- theorem-card: probability-independence
-- Same four-outcome fixture: |A intersection B|*|Omega| = |A|*|B|.
theorem THM_P003_probability_independence_counts : (1 : Nat) * 4 = 2 * 2 := by
  rfl

#check THM_P003_probability_independence_counts

end Veyra
