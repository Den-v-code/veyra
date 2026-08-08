/-!
# P1-D3 all-depth family

Constructive periodic coordinates plus pointwise prefix/family equivalence and
restriction laws.  This file introduces no completed carrier.
-/

set_option autoImplicit false

namespace VeyraAllDepthFamily

def Prefix (A : Type) (n : Nat) := Fin n → A

def prefixEq {A : Type} {n : Nat} (x y : Prefix A n) : Prop :=
  ∀ i, x i = y i

def restrict {A : Type} {m n : Nat} (h : m ≤ n) (x : Prefix A n) : Prefix A m :=
  fun i ↦ x ⟨i.val, Nat.lt_of_lt_of_le i.isLt h⟩

def Family (A : Type) := (n : Nat) → Prefix A n

def familyEq {A : Type} (F G : Family A) : Prop :=
  ∀ n, prefixEq (F n) (G n)

def periodicAt {A : Type} (p : List A) (h : p ≠ []) (i : Nat) : A :=
  p.get ⟨i % p.length, Nat.mod_lt _ (List.length_pos_iff.mpr h)⟩

def periodicFamily {A : Type} (p : List A) (h : p ≠ []) : Family A :=
  fun _ i ↦ periodicAt p h i.val

theorem THM_D3_LEAN_001_coordinate_total
    {A : Type} (p : List A) (h : p ≠ []) (n : Nat) (i : Fin n) :
    periodicFamily p h n i = periodicAt p h i.val := by
  rfl

theorem THM_D3_LEAN_002_coordinate_member
    {A : Type} (p : List A) (h : p ≠ []) (n : Nat) (i : Fin n) :
    periodicFamily p h n i ∈ p := by
  exact List.get_mem p _

theorem THM_D3_LEAN_003_restriction_compatible
    {A : Type} (p : List A) (h : p ≠ [])
    (m n : Nat) (hmn : m ≤ n) (i : Fin m) :
    periodicFamily p h n ⟨i.val, Nat.lt_of_lt_of_le i.isLt hmn⟩ =
      periodicFamily p h m i := by
  rfl

theorem THM_D3_LEAN_004_relation_reflexive
    {A : Type} {n : Nat} (x : Prefix A n) : prefixEq x x := by
  intro i
  rfl

theorem THM_D3_LEAN_005_relation_symmetric
    {A : Type} {n : Nat} {x y : Prefix A n} (h : prefixEq x y) : prefixEq y x := by
  intro i
  exact Eq.symm (h i)

theorem THM_D3_LEAN_006_relation_transitive
    {A : Type} {n : Nat} {x y z : Prefix A n}
    (hxy : prefixEq x y) (hyz : prefixEq y z) : prefixEq x z := by
  intro i
  exact Eq.trans (hxy i) (hyz i)

theorem THM_D3_LEAN_007_restriction_identity
    {A : Type} {n : Nat} (x : Prefix A n) :
    prefixEq (restrict (Nat.le_refl n) x) x := by
  intro i
  rfl

theorem THM_D3_LEAN_008_restriction_composition
    {A : Type} {l m n : Nat} (hlm : l ≤ m) (hmn : m ≤ n) (x : Prefix A n) :
    prefixEq (restrict hlm (restrict hmn x)) (restrict (Nat.le_trans hlm hmn) x) := by
  intro i
  rfl

theorem THM_D3_LEAN_009_restriction_congruence
    {A : Type} {m n : Nat} (hmn : m ≤ n) {x y : Prefix A n} (h : prefixEq x y) :
    prefixEq (restrict hmn x) (restrict hmn y) := by
  intro i
  exact h _

theorem THM_D3_LEAN_010_family_equivalence
    {A : Type} :
    (∀ F : Family A, familyEq F F) ∧
    (∀ F G : Family A, familyEq F G → familyEq G F) ∧
    (∀ F G H : Family A, familyEq F G → familyEq G H → familyEq F H) := by
  constructor
  · intro F n i
    rfl
  constructor
  · intro F G h n i
    exact Eq.symm (h n i)
  · intro F G H hFG hGH n i
    exact Eq.trans (hFG n i) (hGH n i)

theorem THM_D3_LEAN_011_constructor_deterministic
    {A : Type} (p : List A) (h₁ h₂ : p ≠ []) :
    ∀ n i, periodicFamily p h₁ n i = periodicFamily p h₂ n i := by
  intro n i
  rfl


#print axioms THM_D3_LEAN_001_coordinate_total
#print axioms THM_D3_LEAN_002_coordinate_member
#print axioms THM_D3_LEAN_003_restriction_compatible
#print axioms THM_D3_LEAN_004_relation_reflexive
#print axioms THM_D3_LEAN_005_relation_symmetric
#print axioms THM_D3_LEAN_006_relation_transitive
#print axioms THM_D3_LEAN_007_restriction_identity
#print axioms THM_D3_LEAN_008_restriction_composition
#print axioms THM_D3_LEAN_009_restriction_congruence
#print axioms THM_D3_LEAN_010_family_equivalence
#print axioms THM_D3_LEAN_011_constructor_deterministic

end VeyraAllDepthFamily
