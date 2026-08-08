import Std.Tactic
import Init.GrindInstances.Ring.Fin
set_option autoImplicit false
structure VeyraPrimeWitness (p : Nat) where
  two_le : 2 <= p
  no_proper_divisor : forall d : Fin p, 2 <= d.val -> p % d.val != 0
def veyraModulus (p n : Nat) : Nat := p ^ (n + 1)
theorem veyraModulusPos {p : Nat} (hp : VeyraPrimeWitness p) (n : Nat) :
    0 < veyraModulus p n :=
  Nat.pow_pos (Nat.zero_lt_of_lt hp.two_le)

theorem veyraModulusDvd {p : Nat} (_hp : VeyraPrimeWitness p)
    (m n : Nat) (h : m <= n) : veyraModulus p m ∣ veyraModulus p n :=
  Nat.pow_dvd_pow p (Nat.add_le_add_right h 1)

abbrev ZMod (modulus : Nat) := Fin modulus

abbrev VeyraZMod {p : Nat} (_hp : VeyraPrimeWitness p) (n : Nat) :=
  ZMod (veyraModulus p n)

def veyraReduce {p : Nat} (hp : VeyraPrimeWitness p) {m n : Nat}
    (_h : m <= n) (x : VeyraZMod hp n) : VeyraZMod hp m :=
  ⟨x.val % veyraModulus p m, Nat.mod_lt _ (veyraModulusPos hp m)⟩

structure VeyraStageRingLaws {p : Nat} (hp : VeyraPrimeWitness p) where
  zero : (n : Nat) -> VeyraZMod hp n
  one : (n : Nat) -> VeyraZMod hp n
  neg : (n : Nat) -> VeyraZMod hp n -> VeyraZMod hp n
  add : (n : Nat) -> VeyraZMod hp n -> VeyraZMod hp n -> VeyraZMod hp n
  mul : (n : Nat) -> VeyraZMod hp n -> VeyraZMod hp n -> VeyraZMod hp n
  reduce_zero : forall m n (h : m <= n), veyraReduce hp h (zero n) = zero m
  reduce_one : forall m n (h : m <= n), veyraReduce hp h (one n) = one m
  reduce_neg : forall m n (h : m <= n) x,
    veyraReduce hp h (neg n x) = neg m (veyraReduce hp h x)
  reduce_add : forall m n (h : m <= n) x y,
    veyraReduce hp h (add n x y) = add m (veyraReduce hp h x) (veyraReduce hp h y)
  reduce_mul : forall m n (h : m <= n) x y,
    veyraReduce hp h (mul n x y) = mul m (veyraReduce hp h x) (veyraReduce hp h y)
  add_assoc : forall n a b c, add n (add n a b) c = add n a (add n b c)
  add_comm : forall n a b, add n a b = add n b a
  zero_add : forall n a, add n (zero n) a = a
  add_neg : forall n a, add n a (neg n a) = zero n
  mul_assoc : forall n a b c, mul n (mul n a b) c = mul n a (mul n b c)
  mul_comm : forall n a b, mul n a b = mul n b a
  one_mul : forall n a, mul n (one n) a = a
  left_distrib : forall n a b c, mul n a (add n b c) = add n (mul n a b) (mul n a c)

def veyraCanonicalStageRingLaws {p : Nat} (hp : VeyraPrimeWitness p) :
    VeyraStageRingLaws hp where
  zero := fun n => ⟨0, veyraModulusPos hp n⟩
  one := fun n => ⟨1 % veyraModulus p n, Nat.mod_lt _ (veyraModulusPos hp n)⟩
  neg := fun _ x => -x
  add := fun _ x y => x + y
  mul := fun _ x y => x * y
  reduce_zero := by intros; apply Fin.ext; simp [veyraReduce]
  reduce_one := by
    intros m n h; apply Fin.ext
    simp [veyraReduce, Nat.mod_mod_of_dvd, veyraModulusDvd hp m n h]
  reduce_neg := by
    intros m n h x
    letI : NeZero (veyraModulus p n) := ⟨Nat.ne_of_gt (veyraModulusPos hp n)⟩
    letI : NeZero (veyraModulus p m) := ⟨Nat.ne_of_gt (veyraModulusPos hp m)⟩
    have hzero : veyraReduce hp h (-x) + veyraReduce hp h x = 0 := by
      apply Fin.ext
      simp [veyraReduce, Fin.neg_def, Fin.add_def, Nat.mod_mod_of_dvd,
        veyraModulusDvd hp m n h, Nat.mod_eq_zero_of_dvd]
    have hcancel : veyraReduce hp h x + -(veyraReduce hp h x) = 0 := by
      rw [Lean.Grind.Fin.add_comm]
      exact Lean.Grind.Fin.neg_add_cancel _
    calc
      veyraReduce hp h (-x) = veyraReduce hp h (-x) + 0 := (Fin.add_zero _).symm
      _ = veyraReduce hp h (-x) + (veyraReduce hp h x + -(veyraReduce hp h x)) := by
        rw [hcancel]
      _ = (veyraReduce hp h (-x) + veyraReduce hp h x) + -(veyraReduce hp h x) :=
        (Lean.Grind.Fin.add_assoc _ _ _).symm
      _ = -(veyraReduce hp h x) := by rw [hzero, Fin.zero_add]
  reduce_add := by
    intros m n h x y; apply Fin.ext
    simp [veyraReduce, Fin.add_def, Nat.mod_mod_of_dvd, veyraModulusDvd hp m n h]
  reduce_mul := by
    intros m n h x y; apply Fin.ext
    simp [veyraReduce, Fin.mul_def, Nat.mod_mod_of_dvd, veyraModulusDvd hp m n h]
  add_assoc := fun _ => Lean.Grind.Fin.add_assoc
  add_comm := fun _ => Lean.Grind.Fin.add_comm
  zero_add := by
    intro n; letI : NeZero (veyraModulus p n) := ⟨Nat.ne_of_gt (veyraModulusPos hp n)⟩
    exact Fin.zero_add
  add_neg := by
    intro n; letI : NeZero (veyraModulus p n) := ⟨Nat.ne_of_gt (veyraModulusPos hp n)⟩
    intro a; rw [Lean.Grind.Fin.add_comm]; exact Lean.Grind.Fin.neg_add_cancel a
  mul_assoc := fun _ => Lean.Grind.Fin.mul_assoc
  mul_comm := fun _ => Lean.Grind.Fin.mul_comm
  one_mul := by
    intro n; letI : NeZero (veyraModulus p n) := ⟨Nat.ne_of_gt (veyraModulusPos hp n)⟩
    exact Fin.one_mul
  left_distrib := fun _ => Lean.Grind.Fin.left_distrib

def VeyraCompatibleFamily {p : Nat} (hp : VeyraPrimeWitness p) :=
  {a : (n : Nat) -> VeyraZMod hp n //
    forall m n (h : m <= n), veyraReduce hp h (a n) = a m}

abbrev ZpVeyra {p : Nat} (hp : VeyraPrimeWitness p) := VeyraCompatibleFamily hp

def veyraRho {p : Nat} {hp : VeyraPrimeWitness p} (n : Nat) (x : ZpVeyra hp) := x.val n

def veyraZeroFamily {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) : ZpVeyra hp :=
  ⟨ops.zero, ops.reduce_zero⟩

def veyraOneFamily {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) : ZpVeyra hp :=
  ⟨ops.one, ops.reduce_one⟩

def veyraNegFamily {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) (x : ZpVeyra hp) : ZpVeyra hp :=
  ⟨fun n => ops.neg n (x.val n), by
    intros m n h
    rw [ops.reduce_neg, x.property m n h]⟩

def veyraAddFamily {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) (x y : ZpVeyra hp) : ZpVeyra hp :=
  ⟨fun n => ops.add n (x.val n) (y.val n), by
    intros m n h
    rw [ops.reduce_add, x.property m n h, y.property m n h]⟩

def veyraMulFamily {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) (x y : ZpVeyra hp) : ZpVeyra hp :=
  ⟨fun n => ops.mul n (x.val n) (y.val n), by
    intros m n h
    rw [ops.reduce_mul, x.property m n h, y.property m n h]⟩

structure VeyraCarrierCommRingLaws {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) where
  add_assoc : forall a b c, veyraAddFamily ops (veyraAddFamily ops a b) c =
    veyraAddFamily ops a (veyraAddFamily ops b c)
  add_comm : forall a b, veyraAddFamily ops a b = veyraAddFamily ops b a
  zero_add : forall a, veyraAddFamily ops (veyraZeroFamily ops) a = a
  add_neg : forall a, veyraAddFamily ops a (veyraNegFamily ops a) = veyraZeroFamily ops
  mul_assoc : forall a b c, veyraMulFamily ops (veyraMulFamily ops a b) c =
    veyraMulFamily ops a (veyraMulFamily ops b c)
  mul_comm : forall a b, veyraMulFamily ops a b = veyraMulFamily ops b a
  one_mul : forall a, veyraMulFamily ops (veyraOneFamily ops) a = a
  left_distrib : forall a b c, veyraMulFamily ops a (veyraAddFamily ops b c) =
    veyraAddFamily ops (veyraMulFamily ops a b) (veyraMulFamily ops a c)

structure VeyraPPCPBundle {p : Nat} (hp : VeyraPrimeWitness p)
    (ops : VeyraStageRingLaws hp) where
  prime_lower_bound : 2 <= p
  stage_modulus_divisibility : forall m n, m <= n -> veyraModulus p m ∣ veyraModulus p n
  reduction_well_formed_congruence : forall m n (h : m <= n)
    (x y : VeyraZMod hp n), x = y -> veyraReduce hp h x = veyraReduce hp h y
  reduction_identity : forall n (x : VeyraZMod hp n),
    veyraReduce hp (Nat.le_refl n) x = x
  reduction_composition : forall l m n (hlm : l <= m) (hmn : m <= n)
    (x : VeyraZMod hp n), veyraReduce hp hlm (veyraReduce hp hmn x) =
      veyraReduce hp (Nat.le_trans hlm hmn) x
  carrier_presentation_compatible : forall x : ZpVeyra hp, forall m n (h : m <= n),
    veyraReduce hp h (veyraRho n x) = veyraRho m x
  universal_realization : forall f : VeyraCompatibleFamily hp,
    exists x : ZpVeyra hp, forall n, veyraRho n x = f.val n
  coordinate_agreement : forall x y : ZpVeyra hp,
    (forall n, veyraRho n x = veyraRho n y) -> forall n, x.val n = y.val n
  joint_separation : forall x y : ZpVeyra hp,
    (forall n, veyraRho n x = veyraRho n y) -> x = y
  relative_uniqueness : forall f : VeyraCompatibleFamily hp, forall x y : ZpVeyra hp,
    (forall n, veyraRho n x = f.val n) ->
    (forall n, veyraRho n y = f.val n) -> x = y
  zero_family_nonvacuity : Nonempty (ZpVeyra hp)
  one_family_formation : exists x : ZpVeyra hp, x = veyraOneFamily ops
  addition_closure : forall x y : ZpVeyra hp,
    exists z : ZpVeyra hp, z = veyraAddFamily ops x y
  negation_additive_inverse : forall x : ZpVeyra hp,
    veyraAddFamily ops x (veyraNegFamily ops x) = veyraZeroFamily ops
  multiplication_closure : forall x y : ZpVeyra hp,
    exists z : ZpVeyra hp, z = veyraMulFamily ops x y
  full_commutative_ring : VeyraCarrierCommRingLaws ops

theorem THM_POMEGA2_001_prime_lower_bound {p : Nat} (hp : VeyraPrimeWitness p) : 2 <= p := hp.two_le

theorem THM_POMEGA2_002_stage_modulus_divisibility {p : Nat}
    (_hp : VeyraPrimeWitness p) (m n : Nat) (h : m <= n) :
    veyraModulus p m ∣ veyraModulus p n :=
  veyraModulusDvd _hp m n h

theorem THM_POMEGA2_003_reduction_well_formed_congruence {p : Nat}
    (hp : VeyraPrimeWitness p) {m n : Nat} (h : m <= n)
    (x y : VeyraZMod hp n) (e : x = y) : veyraReduce hp h x = veyraReduce hp h y := by
  cases e
  rfl

theorem THM_POMEGA2_004_reduction_identity {p : Nat} (hp : VeyraPrimeWitness p)
    (n : Nat) (x : VeyraZMod hp n) : veyraReduce hp (Nat.le_refl n) x = x := by
  apply Fin.ext
  exact Nat.mod_eq_of_lt x.isLt

theorem THM_POMEGA2_005_reduction_composition {p : Nat} (hp : VeyraPrimeWitness p)
    (l m n : Nat) (hlm : l <= m) (hmn : m <= n) (x : VeyraZMod hp n) :
    veyraReduce hp hlm (veyraReduce hp hmn x) =
      veyraReduce hp (Nat.le_trans hlm hmn) x := by
  apply Fin.ext
  exact Nat.mod_mod_of_dvd x.val (THM_POMEGA2_002_stage_modulus_divisibility hp l m hlm)

theorem THM_POMEGA2_006_carrier_presentation_compatible {p : Nat}
    {hp : VeyraPrimeWitness p} (x : ZpVeyra hp) :
    forall m n (h : m <= n), veyraReduce hp h (veyraRho n x) = veyraRho m x := x.property

theorem THM_POMEGA2_007_universal_realization {p : Nat} {hp : VeyraPrimeWitness p}
    (f : VeyraCompatibleFamily hp) : exists x : ZpVeyra hp, forall n, veyraRho n x = f.val n :=
  ⟨f, fun _ => rfl⟩

theorem THM_POMEGA2_008_coordinate_agreement {p : Nat} {hp : VeyraPrimeWitness p}
    (x y : ZpVeyra hp) (h : forall n, veyraRho n x = veyraRho n y) (n : Nat) :
    x.val n = y.val n := h n

theorem THM_POMEGA2_009_joint_separation {p : Nat} {hp : VeyraPrimeWitness p}
    (x y : ZpVeyra hp) (h : forall n, veyraRho n x = veyraRho n y) : x = y := by
  apply Subtype.ext
  exact funext h

theorem THM_POMEGA2_010_relative_uniqueness {p : Nat} {hp : VeyraPrimeWitness p}
    (f : VeyraCompatibleFamily hp) (x y : ZpVeyra hp)
    (hx : forall n, veyraRho n x = f.val n)
    (hy : forall n, veyraRho n y = f.val n) : x = y :=
  THM_POMEGA2_009_joint_separation x y (fun n => (hx n).trans (hy n).symm)

theorem THM_POMEGA2_011_zero_family_nonvacuity {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) : Nonempty (ZpVeyra hp) := ⟨veyraZeroFamily ops⟩

theorem THM_POMEGA2_012_one_family_formation {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) : exists x : ZpVeyra hp, x = veyraOneFamily ops :=
  ⟨veyraOneFamily ops, rfl⟩

theorem THM_POMEGA2_013_addition_closure {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) (x y : ZpVeyra hp) :
    exists z : ZpVeyra hp, z = veyraAddFamily ops x y :=
  ⟨veyraAddFamily ops x y, rfl⟩

theorem THM_POMEGA2_014_negation_additive_inverse {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) (x : ZpVeyra hp) :
    veyraAddFamily ops x (veyraNegFamily ops x) = veyraZeroFamily ops := by
  apply THM_POMEGA2_009_joint_separation
  intro n
  exact ops.add_neg n (x.val n)

theorem THM_POMEGA2_015_multiplication_closure {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) (x y : ZpVeyra hp) :
    exists z : ZpVeyra hp, z = veyraMulFamily ops x y :=
  ⟨veyraMulFamily ops x y, rfl⟩

theorem THM_POMEGA2_016_full_commutative_ring {p : Nat} {hp : VeyraPrimeWitness p}
    (ops : VeyraStageRingLaws hp) : VeyraCarrierCommRingLaws ops := by
  constructor <;> intros <;> apply THM_POMEGA2_009_joint_separation <;> intro n
  · exact ops.add_assoc n _ _ _
  · exact ops.add_comm n _ _
  · exact ops.zero_add n _
  · exact ops.add_neg n _
  · exact ops.mul_assoc n _ _ _
  · exact ops.mul_comm n _ _
  · exact ops.one_mul n _
  · exact ops.left_distrib n _ _ _

theorem THM_POMEGA2_017_ppcp_introduction {p : Nat} (hp : VeyraPrimeWitness p) :
    VeyraPPCPBundle hp (veyraCanonicalStageRingLaws hp) := by
  let ops := veyraCanonicalStageRingLaws hp
  constructor
  · exact THM_POMEGA2_001_prime_lower_bound hp
  · exact fun m n h => THM_POMEGA2_002_stage_modulus_divisibility hp m n h
  · exact fun _ _ h x y e => THM_POMEGA2_003_reduction_well_formed_congruence hp h x y e
  · exact THM_POMEGA2_004_reduction_identity hp
  · exact THM_POMEGA2_005_reduction_composition hp
  · exact THM_POMEGA2_006_carrier_presentation_compatible
  · exact THM_POMEGA2_007_universal_realization
  · exact fun x y h n => THM_POMEGA2_008_coordinate_agreement x y h n
  · exact THM_POMEGA2_009_joint_separation
  · exact THM_POMEGA2_010_relative_uniqueness
  · exact THM_POMEGA2_011_zero_family_nonvacuity ops
  · exact THM_POMEGA2_012_one_family_formation ops
  · exact THM_POMEGA2_013_addition_closure ops
  · exact THM_POMEGA2_014_negation_additive_inverse ops
  · exact THM_POMEGA2_015_multiplication_closure ops
  · exact THM_POMEGA2_016_full_commutative_ring ops

#print axioms THM_POMEGA2_001_prime_lower_bound
#print axioms THM_POMEGA2_002_stage_modulus_divisibility
#print axioms THM_POMEGA2_003_reduction_well_formed_congruence
#print axioms THM_POMEGA2_004_reduction_identity
#print axioms THM_POMEGA2_005_reduction_composition
#print axioms THM_POMEGA2_006_carrier_presentation_compatible
#print axioms THM_POMEGA2_007_universal_realization
#print axioms THM_POMEGA2_008_coordinate_agreement
#print axioms THM_POMEGA2_009_joint_separation
#print axioms THM_POMEGA2_010_relative_uniqueness
#print axioms THM_POMEGA2_011_zero_family_nonvacuity
#print axioms THM_POMEGA2_012_one_family_formation
#print axioms THM_POMEGA2_013_addition_closure
#print axioms THM_POMEGA2_014_negation_additive_inverse
#print axioms THM_POMEGA2_015_multiplication_closure
#print axioms THM_POMEGA2_016_full_commutative_ring
#print axioms THM_POMEGA2_017_ppcp_introduction
#print axioms veyraCanonicalStageRingLaws
