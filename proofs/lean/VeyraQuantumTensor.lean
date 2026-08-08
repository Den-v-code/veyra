namespace VeyraQuantumTensor

/-!
Exact finite theorem scope only.

`FiniteBornState` represents rational probabilities by natural numerators and a
common positive scale. `TensorBorn` is a finite, arbitrarily long factor chain.
`ExactUnitary` is a reversible norm-preserving map, and `tensorUnitary` proves
closure under binary tensor products. This file does not formalize analytic
Hilbert spaces, physical apparatus, simulation fidelity, or quantum advantage.
-/

/-- A finite Born distribution represented by exact natural weights. -/
structure FiniteBornState where
  weights : List Nat
  scale : Nat
  scalePositive : 0 < scale
  normalized : weights.sum = scale
deriving Repr

/-- Exact total numerator in the finite Born rule. -/
def bornTotal (state : FiniteBornState) : Nat :=
  state.weights.sum

/-- Exact numerator of one outcome, or zero outside the finite support. -/
def bornNumerator (state : FiniteBornState) (outcome : Nat) : Nat :=
  state.weights.getD outcome 0

/-- The checked finite Born weights sum to their common scale. -/
theorem THM_Q11_001_born_rule_normalized (state : FiniteBornState) :
    bornTotal state = state.scale := by
  exact state.normalized

/-- A finite tensor chain; `scalar` is the empty tensor product. -/
inductive TensorBorn where
  | scalar
  | factor (head : FiniteBornState) (tail : TensorBorn)
deriving Repr

/-- Total Born numerator of a tensor chain. -/
def tensorBornTotal : TensorBorn → Nat
  | .scalar => 1
  | .factor head tail => bornTotal head * tensorBornTotal tail

/-- Common probability scale of a tensor chain. -/
def tensorBornScale : TensorBorn → Nat
  | .scalar => 1
  | .factor head tail => head.scale * tensorBornScale tail

/-- Any finite tensor chain of normalized factors remains normalized exactly. -/
theorem THM_Q11_002_tensor_born_normalized (state : TensorBorn) :
    tensorBornTotal state = tensorBornScale state := by
  induction state with
  | scalar => rfl
  | factor head tail hypothesis =>
      simp only [tensorBornTotal, tensorBornScale]
      rw [THM_Q11_001_born_rule_normalized, hypothesis]

/-- Product norm used by the finite tensor carrier. -/
def tensorNorm {Left Right : Type}
    (leftNorm : Left → Nat) (rightNorm : Right → Nat) (state : Left × Right) : Nat :=
  leftNorm state.1 * rightNorm state.2

/-- Exact finite unitarity: a two-sided inverse plus norm preservation. -/
structure ExactUnitary (State : Type) (normSq : State → Nat) where
  forward : State → State
  inverse : State → State
  leftInverse : ∀ state, inverse (forward state) = state
  rightInverse : ∀ state, forward (inverse state) = state
  preservesNorm : ∀ state, normSq (forward state) = normSq state

/-- Identity is exactly unitary for every finite norm carrier. -/
def identityUnitary {State : Type} (normSq : State → Nat) : ExactUnitary State normSq where
  forward := id
  inverse := id
  leftInverse := by intro state; rfl
  rightInverse := by intro state; rfl
  preservesNorm := by intro state; rfl

/-- Tensor action of two finite maps. -/
def tensorMap {Left Right : Type}
    (left : Left → Left) (right : Right → Right) (state : Left × Right) : Left × Right :=
  (left state.1, right state.2)

/-- Tensor products of exact finite unitaries are exact finite unitaries. -/
def THM_Q11_003_tensor_unitary {Left Right : Type}
    {leftNorm : Left → Nat} {rightNorm : Right → Nat}
    (left : ExactUnitary Left leftNorm) (right : ExactUnitary Right rightNorm) :
    ExactUnitary (Left × Right) (tensorNorm leftNorm rightNorm) where
  forward := tensorMap left.forward right.forward
  inverse := tensorMap left.inverse right.inverse
  leftInverse := by
    intro state
    cases state with
    | mk leftState rightState =>
        simp only [tensorMap]
        rw [left.leftInverse, right.leftInverse]
  rightInverse := by
    intro state
    cases state with
    | mk leftState rightState =>
        simp only [tensorMap]
        rw [left.rightInverse, right.rightInverse]
  preservesNorm := by
    intro state
    cases state with
    | mk leftState rightState =>
        simp only [tensorMap, tensorNorm]
        rw [left.preservesNorm, right.preservesNorm]

/-- Composition of exact finite unitaries is exact finite unitary. -/
def THM_Q11_004_compose_unitary {State : Type} {normSq : State → Nat}
    (outer inner : ExactUnitary State normSq) : ExactUnitary State normSq where
  forward := fun state => outer.forward (inner.forward state)
  inverse := fun state => inner.inverse (outer.inverse state)
  leftInverse := by
    intro state
    rw [outer.leftInverse, inner.leftInverse]
  rightInverse := by
    intro state
    rw [inner.rightInverse, outer.rightInverse]
  preservesNorm := by
    intro state
    rw [outer.preservesNorm, inner.preservesNorm]

#check THM_Q11_001_born_rule_normalized
#check THM_Q11_002_tensor_born_normalized
#check THM_Q11_003_tensor_unitary
#check THM_Q11_004_compose_unitary

end VeyraQuantumTensor
