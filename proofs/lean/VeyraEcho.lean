namespace Veyra

universe u v

def echo {Obj : Type u} {Observer : Type v}
    (observe : Observer → Obj → Nat) (o : Observer) (x y : Obj) : Prop :=
  observe o x = observe o y

theorem THM_F001_echo_reflexive {Obj : Type u} {Observer : Type v}
    (observe : Observer → Obj → Nat) (o : Observer) (x : Obj) :
    echo observe o x x := by
  unfold echo
  rfl

-- Euclid-style escape: product-plus-one is congruent to one modulo each listed factor shadow.
theorem THM_F002_euclid_escape_mod (n k : Nat) : (n * k + 1) % n = 1 % n := by
  simp [Nat.add_mod]

end Veyra
