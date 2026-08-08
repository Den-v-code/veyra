set_option autoImplicit false

abbrev VeyraPrefix (A : Type) (n : Nat) := Fin n -> A
abbrev VeyraStream (A : Type) := Nat -> A

def veyraTruncate {A : Type} {n : Nat} (m : Nat) (h : m <= n)
    (p : VeyraPrefix A n) : VeyraPrefix A m :=
  fun i => p ⟨i.val, Nat.lt_of_lt_of_le i.isLt h⟩

structure VeyraCompatibleFamily (A : Type) where
  value : (n : Nat) -> VeyraPrefix A n
  compatible : forall (m n : Nat) (h : m <= n),
    veyraTruncate m h (value n) = value m

def veyraRho {A : Type} (n : Nat) (s : VeyraStream A) : VeyraPrefix A n :=
  fun i => s i.val

def veyraDiag {A : Type} (f : VeyraCompatibleFamily A) : VeyraStream A :=
  fun k => f.value (k + 1) ⟨k, Nat.lt_succ_self k⟩

theorem THM_POMEGA1_001_truncation_identity {A : Type} (n : Nat)
    (p : VeyraPrefix A n) : veyraTruncate n (Nat.le_refl n) p = p := by
  funext i
  rfl

theorem THM_POMEGA1_002_truncation_composition {A : Type}
    (l m n : Nat) (hlm : l <= m) (hmn : m <= n) (p : VeyraPrefix A n) :
    veyraTruncate l hlm (veyraTruncate m hmn p) =
      veyraTruncate l (Nat.le_trans hlm hmn) p := by
  funext i
  rfl

theorem THM_POMEGA1_003_rho_formation_congruence {A : Type}
    (n : Nat) (s t : VeyraStream A) (h : s = t) : veyraRho n s = veyraRho n t := by
  cases h
  rfl

theorem THM_POMEGA1_004_stream_restriction_compatible {A : Type}
    (m n : Nat) (h : m <= n) (s : VeyraStream A) :
    veyraTruncate m h (veyraRho n s) = veyraRho m s := by
  funext i
  rfl

theorem THM_POMEGA1_005_diagonal_realization_depth {A : Type}
    (f : VeyraCompatibleFamily A) (n : Nat) :
    veyraRho n (veyraDiag f) = f.value n := by
  funext i
  have hle : i.val + 1 <= n := Nat.succ_le_of_lt i.isLt
  have h := f.compatible (i.val + 1) n hle
  have hi := congrFun h ⟨i.val, Nat.lt_succ_self i.val⟩
  exact hi.symm

theorem THM_POMEGA1_006_universal_realization {A : Type}
    (f : VeyraCompatibleFamily A) :
    exists s : VeyraStream A, forall n : Nat, veyraRho n s = f.value n := by
  exact ⟨veyraDiag f, THM_POMEGA1_005_diagonal_realization_depth f⟩

theorem THM_POMEGA1_007_coordinate_agreement {A : Type}
    (s t : VeyraStream A)
    (h : forall n : Nat, veyraRho n s = veyraRho n t) (k : Nat) : s k = t k := by
  have hk := congrFun (h (k + 1)) ⟨k, Nat.lt_succ_self k⟩
  exact hk

theorem THM_POMEGA1_008_joint_separation {A : Type}
    (s t : VeyraStream A)
    (h : forall n : Nat, veyraRho n s = veyraRho n t) : s = t := by
  funext k
  exact THM_POMEGA1_007_coordinate_agreement s t h k

theorem THM_POMEGA1_009_relative_uniqueness {A : Type}
    (f : VeyraCompatibleFamily A) (s t : VeyraStream A)
    (hs : forall n : Nat, veyraRho n s = f.value n)
    (ht : forall n : Nat, veyraRho n t = f.value n) : s = t := by
  apply THM_POMEGA1_008_joint_separation s t
  intro n
  exact (hs n).trans (ht n).symm

theorem THM_POMEGA1_010_nonvacuity_inhabitance {A : Type} (a0 : A) :
    Nonempty (VeyraCompatibleFamily A) ∧ Nonempty (VeyraStream A) := by
  let f : VeyraCompatibleFamily A := {
    value := fun _ _ => a0
    compatible := by intros; funext; rfl
  }
  exact ⟨⟨f⟩, ⟨fun _ => a0⟩⟩

theorem THM_POMEGA1_011_scp_introduction {A : Type} (a0 : A) :
    (forall f : VeyraCompatibleFamily A,
      exists s : VeyraStream A,
        (forall n : Nat, veyraRho n s = f.value n) ∧
        forall t : VeyraStream A,
          (forall n : Nat, veyraRho n t = f.value n) -> t = s) ∧
    Nonempty (VeyraCompatibleFamily A) ∧ Nonempty (VeyraStream A) := by
  constructor
  · intro f
    refine ⟨veyraDiag f, THM_POMEGA1_005_diagonal_realization_depth f, ?_⟩
    intro s hs
    exact THM_POMEGA1_009_relative_uniqueness f s (veyraDiag f) hs
      (THM_POMEGA1_005_diagonal_realization_depth f)
  · exact THM_POMEGA1_010_nonvacuity_inhabitance a0

#print axioms THM_POMEGA1_001_truncation_identity
#print axioms THM_POMEGA1_002_truncation_composition
#print axioms THM_POMEGA1_003_rho_formation_congruence
#print axioms THM_POMEGA1_004_stream_restriction_compatible
#print axioms THM_POMEGA1_005_diagonal_realization_depth
#print axioms THM_POMEGA1_006_universal_realization
#print axioms THM_POMEGA1_007_coordinate_agreement
#print axioms THM_POMEGA1_008_joint_separation
#print axioms THM_POMEGA1_009_relative_uniqueness
#print axioms THM_POMEGA1_010_nonvacuity_inhabitance
#print axioms THM_POMEGA1_011_scp_introduction
