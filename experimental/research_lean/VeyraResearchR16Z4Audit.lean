set_option autoImplicit false

namespace Veyra

/-
Bounded formal counterpart of the executable R16 Z/4 reduction audit.

This file intentionally proves only:
* the exact four-state/four-shift/four-observer best-lower table;
* one five-state no-greatest-lower counterexample matching the executable
  partiality boundary.

It is a standalone finite decision model bound to the executable fixture by
hostile Python tests; it does not formally depend on the stable
`THM-R16-001..003` predicate spine. It does not prove descent totality, the
64-row composition audit, Python/Lean implementation equivalence, a new
calculus, novelty, or R8 promotion.
-/

inductive Z4State where
  | s0 | s1 | s2 | s3
deriving DecidableEq, Repr

inductive Z4Shift where
  | k0 | k1 | k2 | k3
deriving DecidableEq, Repr

inductive Z4Observer where
  | silence | parity | threshold | phasePair
deriving DecidableEq, Repr

def z4States : List Z4State := [.s0, .s1, .s2, .s3]
def z4Shifts : List Z4Shift := [.k0, .k1, .k2, .k3]
def z4Observers : List Z4Observer :=
  [.silence, .parity, .threshold, .phasePair]

def z4ShiftApply : Z4Shift → Z4State → Z4State
  | .k0, state => state
  | .k1, .s0 => .s1
  | .k1, .s1 => .s2
  | .k1, .s2 => .s3
  | .k1, .s3 => .s0
  | .k2, .s0 => .s2
  | .k2, .s1 => .s3
  | .k2, .s2 => .s0
  | .k2, .s3 => .s1
  | .k3, .s0 => .s3
  | .k3, .s1 => .s0
  | .k3, .s2 => .s1
  | .k3, .s3 => .s2

def z4Labels : Z4Observer → Z4State → Nat
  | .silence, _ => 0
  | .parity, .s0 => 0
  | .parity, .s1 => 1
  | .parity, .s2 => 0
  | .parity, .s3 => 1
  | .threshold, .s0 => 0
  | .threshold, .s1 => 0
  | .threshold, .s2 => 1
  | .threshold, .s3 => 1
  | .phasePair, .s0 => 0
  | .phasePair, .s1 => 1
  | .phasePair, .s2 => 2
  | .phasePair, .s3 => 3

def distinguishedB {State : Type}
    [DecidableEq State]
    (labels : State → Nat) (left right : State) : Bool :=
  decide (left ≠ right) && decide (labels left ≠ labels right)

def relationLeB {State : Type}
    [DecidableEq State] (states : List State)
    (left right : State → Nat) : Bool :=
  states.all fun first =>
    states.all fun second =>
      (! distinguishedB left first second) ||
        distinguishedB right first second

def z4RawLabels (shift : Z4Shift) (target : Z4Observer) : Z4State → Nat :=
  fun state => z4Labels target (z4ShiftApply shift state)

def z4AdmittedBelowB
    (candidate : Z4Observer) (shift : Z4Shift) (target : Z4Observer) : Bool :=
  relationLeB z4States (z4Labels candidate) (z4RawLabels shift target)

def z4IsGreatestB
    (candidate : Z4Observer) (shift : Z4Shift) (target : Z4Observer) : Bool :=
  z4AdmittedBelowB candidate shift target &&
    z4Observers.all fun other =>
      (! z4AdmittedBelowB other shift target) ||
        relationLeB z4States (z4Labels other) (z4Labels candidate)

def z4ExpectedBest : Z4Shift → Z4Observer → Z4Observer
  | _, .silence => .silence
  | _, .parity => .parity
  | .k0, .threshold => .threshold
  | .k1, .threshold => .silence
  | .k2, .threshold => .threshold
  | .k3, .threshold => .silence
  | _, .phasePair => .phasePair

def z4AuditB : Bool :=
  z4Shifts.all fun shift =>
    z4Observers.all fun target =>
      z4IsGreatestB (z4ExpectedBest shift target) shift target

inductive Z5State where
  | s0 | s1 | s2 | s3 | s4
deriving DecidableEq, Repr

def z5States : List Z5State := [.s0, .s1, .s2, .s3, .s4]

def z5Bottom : Z5State → Nat
  | _ => 0

def z5A : Z5State → Nat
  | .s0 | .s1 => 0
  | .s2 | .s3 | .s4 => 1

def z5B : Z5State → Nat
  | .s0 | .s2 => 0
  | .s1 | .s3 | .s4 => 1

def z5Top : Z5State → Nat
  | .s0 => 0
  | .s1 => 1
  | .s2 => 2
  | .s3 => 3
  | .s4 => 4

def z5Raw : Z5State → Nat
  | .s0 => 0
  | .s1 => 1
  | .s2 => 2
  | .s3 | .s4 => 3

def z5Doctrine : List (Z5State → Nat) := [z5Bottom, z5A, z5B, z5Top]

def z5BelowRawB (candidate : Z5State → Nat) : Bool :=
  relationLeB z5States candidate z5Raw

def z5IsGreatestB (candidate : Z5State → Nat) : Bool :=
  z5BelowRawB candidate &&
    z5Doctrine.all fun other =>
      (! z5BelowRawB other) || relationLeB z5States other candidate

def z5NoGreatestB : Bool :=
  z5Doctrine.all fun candidate => ! z5IsGreatestB candidate

theorem RESEARCH_RZ_T001_bounded_best_lower_and_partiality :
    z4Shifts.length * z4Observers.length = 16 ∧
      z4AuditB = true ∧
      z5NoGreatestB = true := by
  decide

#print axioms RESEARCH_RZ_T001_bounded_best_lower_and_partiality

end Veyra
