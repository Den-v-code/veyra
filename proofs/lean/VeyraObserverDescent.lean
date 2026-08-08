namespace Veyra

/-
Abstract distinction predicates for one composed observer pullback:
`raw` is the exact composite pullback, `direct` its greatest admitted
descent, and `staged` the descent obtained through the middle doctrine.

This artifact proves only the conditional set-theoretic partition spine when
the named direct and staged descents already exist. Python doctrine validation,
descent existence, and the bridge from concrete response tables to these
predicates remain outside this Lean file.
-/

/-- Any nested admitted predicate splits raw debt into two disjoint regions. -/
theorem residual_partition
    {α : Type}
    (raw admitted staged : α → Prop)
    (hStagedAdmitted : ∀ x, staged x → admitted x)
    (hAdmittedRaw : ∀ x, admitted x → raw x) :
    ∀ x,
      ((raw x ∧ ¬ admitted x) ∨ (admitted x ∧ ¬ staged x)) ↔
      (raw x ∧ ¬ staged x) := by
  intro x
  constructor
  · intro h
    cases h with
    | inl hResidual =>
        exact ⟨hResidual.1, fun hStaged => hResidual.2 (hStagedAdmitted x hStaged)⟩
    | inr hSynergy =>
        exact ⟨hAdmittedRaw x hSynergy.1, hSynergy.2⟩
  · intro hDebt
    by_cases hAdmitted : admitted x
    · exact Or.inr ⟨hAdmitted, hDebt.2⟩
    · exact Or.inl ⟨hDebt.1, hAdmitted⟩

/-- THM-R16-001: staged and direct descent partition the same raw debt. -/
theorem THM_R16_001_residual_chain_partition
    {α : Type}
    (raw middle direct staged : α → Prop)
    (hStagedMiddle : ∀ x, staged x → middle x)
    (hMiddleRaw : ∀ x, middle x → raw x)
    (hStagedDirect : ∀ x, staged x → direct x)
    (hDirectRaw : ∀ x, direct x → raw x) :
    ∀ x,
      ((raw x ∧ ¬ middle x) ∨ (middle x ∧ ¬ staged x)) ↔
      ((raw x ∧ ¬ direct x) ∨ (direct x ∧ ¬ staged x)) := by
  intro x
  exact
    (residual_partition raw middle staged hStagedMiddle hMiddleRaw x).trans
      (residual_partition raw direct staged hStagedDirect hDirectRaw x).symm

/-- THM-R16-002: composite residual and synergy are disjoint. -/
theorem THM_R16_002_residual_synergy_disjoint
    {α : Type}
    (raw direct staged : α → Prop) :
    ∀ x,
      ¬ ((raw x ∧ ¬ direct x) ∧ (direct x ∧ ¬ staged x)) := by
  intro x h
  exact h.1.2 h.2.1

/--
THM-R16-003: when direct and staged admitted distinctions coincide,
the synergy correction vanishes and the exact chain rule remains.
-/
theorem THM_R16_003_zero_synergy_chain_rule
    {α : Type}
    (raw direct staged : α → Prop)
    (hSame : ∀ x, direct x ↔ staged x) :
    ∀ x, (raw x ∧ ¬ direct x) ↔ (raw x ∧ ¬ staged x) := by
  intro x
  constructor
  · intro h
    exact ⟨h.1, fun hStaged => h.2 ((hSame x).mpr hStaged)⟩
  · intro h
    exact ⟨h.1, fun hDirect => h.2 ((hSame x).mp hDirect)⟩

end Veyra
