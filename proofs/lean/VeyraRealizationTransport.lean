/-!
Abstract laws for the restricted realization-context transport boundary.

The executable contract uses total finite state reindexings and acts on
extensional response partitions by inverse image.  This file proves only the
corresponding relation-level identity, composition, indiscrete-bottom,
common-refinement, and conditional cost laws.  It does not formalize Python,
R11 replay, R16 admission, canonical bytes, digests, finite resource bounds,
receipt reconstruction, P1-A, or cross-doctrine transport.
-/

namespace VeyraRealizationTransport

universe u v w

/-- A response partition is represented extensionally by its binary relation. -/
abbrev PartitionRel (State : Type u) := State → State → Prop

/-- Reindex a target relation along a total source-to-target state map. -/
def pullback {Source : Type u} {Target : Type v}
    (stateMap : Source → Target) (relation : PartitionRel Target) :
    PartitionRel Source :=
  fun left right => relation (stateMap left) (stateMap right)

/-- The R16 realization bottom is the indiscrete partition. -/
def indiscrete (State : Type u) : PartitionRel State :=
  fun _ _ => True

/-- Common refinement is pointwise intersection of partition relations. -/
def commonRefinement {State : Type u}
    (left right : PartitionRel State) : PartitionRel State :=
  fun first second => left first second ∧ right first second

theorem pullback_identity {State : Type u} (relation : PartitionRel State) :
    pullback (fun state : State => state) relation = relation := by
  rfl

theorem pullback_composition
    {Source : Type u} {Middle : Type v} {Target : Type w}
    (sourceToMiddle : Source → Middle)
    (middleToTarget : Middle → Target)
    (relation : PartitionRel Target) :
    pullback (middleToTarget ∘ sourceToMiddle) relation =
      pullback sourceToMiddle (pullback middleToTarget relation) := by
  rfl

theorem pullback_indiscrete
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target) :
    pullback stateMap (indiscrete Target) = indiscrete Source := by
  rfl

theorem pullback_commonRefinement
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target)
    (left right : PartitionRel Target) :
    pullback stateMap (commonRefinement left right) =
      commonRefinement (pullback stateMap left) (pullback stateMap right) := by
  rfl

/-- A concrete finite partition representation by class labels. -/
abbrev LabelPartition (State : Type u) := State → Nat

/-- The extensional equivalence relation induced by concrete class labels. -/
def relationOfLabels {State : Type u}
    (labels : LabelPartition State) : PartitionRel State :=
  fun left right => labels left = labels right

/-- Pull concrete target labels back along the same total state map. -/
def pullbackLabels {Source : Type u} {Target : Type v}
    (stateMap : Source → Target)
    (target : LabelPartition Target) : LabelPartition Source :=
  fun source => target (stateMap source)

/-- Two concrete labelings encode the same extensional partition. -/
def SamePartitionLabels {State : Type u}
    (left right : LabelPartition State) : Prop :=
  ∀ first second, left first = left second ↔ right first = right second

/-- Raw label pullback induces exactly the abstract relation pullback. -/
theorem relationOfLabels_pullback
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target)
    (target : LabelPartition Target)
    (first second : Source) :
    relationOfLabels (pullbackLabels stateMap target) first second ↔
      pullback stateMap (relationOfLabels target) first second := by
  rfl

/--
A normalized source labeling realizes the same relation pullback whenever the
normalization preserves equality classes.  The equality-class premise is
deliberately explicit: Python first-occurrence normalization is executable
evidence, not proved here.
-/
theorem normalizedLabels_realize_pullback
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target)
    (target : LabelPartition Target)
    (source : LabelPartition Source)
    (same : SamePartitionLabels source (pullbackLabels stateMap target))
    (first second : Source) :
    relationOfLabels source first second ↔
      pullback stateMap (relationOfLabels target) first second := by
  exact (same first second).trans (relationOfLabels_pullback stateMap target first second)

/-- The same bridge transports pairwise distinction, the predicate used by R16-style debt rows. -/
theorem normalizedLabels_distinction_pullback
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target)
    (target : LabelPartition Target)
    (source : LabelPartition Source)
    (same : SamePartitionLabels source (pullbackLabels stateMap target))
    (first second : Source) :
    (¬ relationOfLabels source first second) ↔
      ¬ pullback stateMap (relationOfLabels target) first second := by
  exact not_congr (normalizedLabels_realize_pullback stateMap target source same first second)

/-- Ordered off-diagonal pairs distinguished by one concrete labeling. -/
def DistinguishedByLabels {State : Type u}
    (labels : LabelPartition State) (first second : State) : Prop :=
  first ≠ second ∧ ¬ relationOfLabels labels first second

/--
The normalized label bridge induces exactly the raw R16-style distinction
predicate: off-diagonal source pairs are distinguished precisely when their
images are distinguished by the target labeling.
-/
theorem normalizedLabels_rawDistinction_pullback
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target)
    (target : LabelPartition Target)
    (source : LabelPartition Source)
    (same : SamePartitionLabels source (pullbackLabels stateMap target))
    (first second : Source) :
    DistinguishedByLabels source first second ↔
      (first ≠ second ∧
        ¬ pullback stateMap (relationOfLabels target) first second) := by
  constructor
  · intro h
    exact ⟨h.1, (normalizedLabels_distinction_pullback
      stateMap target source same first second).mp h.2⟩
  · intro h
    exact ⟨h.1, (normalizedLabels_distinction_pullback
      stateMap target source same first second).mpr h.2⟩

/--
When the normalized source labeling is itself the admitted realization of the
raw pullback distinction, the R16 residual predicate is empty pointwise.
This is the exact mathematical consequence exercised by accepted transport
closure rows; it does not prove general descent existence.
-/
theorem normalizedLabels_admittedRaw_zeroResidual
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target)
    (target : LabelPartition Target)
    (source : LabelPartition Source)
    (same : SamePartitionLabels source (pullbackLabels stateMap target))
    (first second : Source) :
    ¬ ((first ≠ second ∧
          ¬ pullback stateMap (relationOfLabels target) first second) ∧
        ¬ DistinguishedByLabels source first second) := by
  intro residual
  exact residual.2 ((normalizedLabels_rawDistinction_pullback
    stateMap target source same first second).mpr residual.1)

/-- Cost nonincrease is an explicit hypothesis on an admitted closure action;
it is not inferred from relation pullback alone. -/
def CostNonincreasing {SourceClosure : Type u} {TargetClosure : Type v}
    (action : TargetClosure → SourceClosure)
    (sourceCost : SourceClosure → Nat)
    (targetCost : TargetClosure → Nat) : Prop :=
  ∀ target, sourceCost (action target) ≤ targetCost target

theorem cost_nonincrease_identity
    {Closure : Type u} (cost : Closure → Nat) :
    CostNonincreasing (fun value : Closure => value) cost cost := by
  intro value
  exact Nat.le_refl (cost value)

theorem cost_nonincrease_composition
    {SourceClosure : Type u} {MiddleClosure : Type v}
    {TargetClosure : Type w}
    (targetToMiddle : TargetClosure → MiddleClosure)
    (middleToSource : MiddleClosure → SourceClosure)
    (sourceCost : SourceClosure → Nat)
    (middleCost : MiddleClosure → Nat)
    (targetCost : TargetClosure → Nat)
    (firstLaw : CostNonincreasing middleToSource sourceCost middleCost)
    (secondLaw : CostNonincreasing targetToMiddle middleCost targetCost) :
    CostNonincreasing (middleToSource ∘ targetToMiddle) sourceCost targetCost := by
  intro target
  exact Nat.le_trans (firstLaw (targetToMiddle target)) (secondLaw target)

#print axioms pullback_identity
#print axioms pullback_composition
#print axioms pullback_indiscrete
#print axioms pullback_commonRefinement
#print axioms relationOfLabels_pullback
#print axioms normalizedLabels_realize_pullback
#print axioms normalizedLabels_distinction_pullback
#print axioms normalizedLabels_rawDistinction_pullback
#print axioms normalizedLabels_admittedRaw_zeroResidual
#print axioms cost_nonincrease_identity
#print axioms cost_nonincrease_composition

end VeyraRealizationTransport
