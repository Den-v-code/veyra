/- Native observer-class closure laws for the R5/R6 bridge. -/

theorem THM_R6_001_factor_blind
    {α β γ : Type}
    (baseline : α → β) (post : β → γ)
    (x y : α)
    (h : baseline x = baseline y) :
    post (baseline x) = post (baseline y) :=
  congrArg post h

theorem THM_R6_002_extension_separates
    {α β γ : Type}
    (baseline : α → β) (extra : α → γ)
    (x y : α)
    (_hbase : baseline x = baseline y)
    (hextra : extra x ≠ extra y) :
    (baseline x, extra x) ≠ (baseline y, extra y) := by
  intro h
  exact hextra (congrArg Prod.snd h)
