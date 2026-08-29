import VeyraPrimePowerReductionNetwork
import Lean.Elab.Tactic.Omega

set_option autoImplicit false

/-!
Research-only bounded formal counterpart of the current executable P3-OG candidate.

This file deliberately stops below `EndogenousArithmeticObserverRole`, HAP/N0 token
actualization, doctrine admission, and stable theorem promotion.  It constructs a
small finite model rather than assuming the seven desired observations as opaque
premises:

* arithmetic inputs are the exact P3-N2 integer-family coordinates F_0/F_1;
* a singleton candidate capability is consumed exactly once;
* one native formation tick reaches the first closed state from an unclosed state;
* F_0/F_1 coupling leaves distinct retained residues under one common continuation;
* the retained residue changes the first later phase transition;
* disabling the sole maintenance component is matched except for that component
  and the same continuation removes the boundary and retained residue;
* an explicit finite history rank places every declared parent strictly before
  its child, with criterion/result strictly after selection and first closure.

The semantic state below is intentionally the quotient-level counterpart of the
current Python candidate fixture (period 3, maintenance credit 1, ACTIVE/LOW ->
ADVANCE, DISABLED/LOW -> IDLE/removal).  This is not a proof that Python bytes or
digests implement the Lean definitions, not full DEF-OG-009, and not
THM-P3OG-001/003 promotion.
-/

namespace Veyra

inductive ResearchP3OGInput where
  | f0
  | f1
  deriving DecidableEq, Repr

def researchP3OGInputIndex : ResearchP3OGInput -> Nat
  | .f0 => 0
  | .f1 => 1

def researchP3OGArithmeticInput {p : Nat} (hp : VeyraPrimeWitness p) (n : Nat) :
    ResearchP3OGInput -> VeyraZMod hp n
  | .f0 => veyraRho n (veyraIntegerFamily hp 0)
  | .f1 => veyraRho n (veyraIntegerFamily hp 1)

theorem RESEARCH_OG_T001_f0_f1_arithmetic_distinct {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) :
    researchP3OGArithmeticInput hp n .f0 ≠
      researchP3OGArithmeticInput hp n .f1 := by
  intro equal
  have valuesEqual := congrArg Fin.val equal
  have hpone : 1 < p := Nat.lt_of_lt_of_le Nat.one_lt_two hp.two_le
  have hmod : 1 < veyraModulus p n := by
    simpa [veyraModulus] using Nat.one_lt_pow (Nat.succ_ne_zero n) hpone
  simp [researchP3OGArithmeticInput, veyraRho, veyraIntegerFamily,
    veyraIntegerResidue, Fin.intCast, Nat.mod_eq_of_lt hmod] at valuesEqual

inductive ResearchP3OGCandidate where
  | alpha
  deriving DecidableEq, Repr

inductive ResearchP3OGSelectionCapability where
  | available
  | consumed
  deriving DecidableEq, Repr

def researchP3OGConsumeSelection :
    ResearchP3OGSelectionCapability ->
      Option (ResearchP3OGCandidate × ResearchP3OGSelectionCapability)
  | .available => some (.alpha, .consumed)
  | .consumed => none

theorem RESEARCH_OG_T002_selection_is_consumed_one_shot :
    researchP3OGConsumeSelection .available = some (.alpha, .consumed) /\
      researchP3OGConsumeSelection .consumed = none := by
  constructor <;> rfl

inductive ResearchP3OGFormationState where
  | unformed
  | closed
  deriving DecidableEq, Repr

def researchP3OGFormationTick : ResearchP3OGFormationState -> ResearchP3OGFormationState
  | .unformed => .closed
  | .closed => .closed

def researchP3OGIsClosed : ResearchP3OGFormationState -> Bool
  | .unformed => false
  | .closed => true

theorem RESEARCH_OG_T003_first_closure_is_genuine :
    researchP3OGFormationTick .unformed = .closed /\
      researchP3OGIsClosed .unformed = false /\
      researchP3OGIsClosed (researchP3OGFormationTick .unformed) = true := by
  constructor
  · rfl
  constructor <;> rfl

inductive ResearchP3OGBoundary where
  | alive
  | removed
  deriving DecidableEq, Repr

inductive ResearchP3OGMaintenanceControl where
  | active
  | disabled
  deriving DecidableEq, Repr

structure ResearchP3OGState where
  boundary : ResearchP3OGBoundary
  maintenanceControl : ResearchP3OGMaintenanceControl
  phase : Nat
  retainedResidue : Option Nat
  maintenanceCredit : Nat
  deriving DecidableEq, Repr

def researchP3OGClosedState : ResearchP3OGState where
  boundary := .alive
  maintenanceControl := .active
  phase := 0
  retainedResidue := none
  maintenanceCredit := 1

def researchP3OGCouple
    (input : ResearchP3OGInput) (state : ResearchP3OGState) : ResearchP3OGState :=
  match state.boundary with
  | .removed => state
  | .alive =>
      { state with retainedResidue := some (researchP3OGInputIndex input) }

def researchP3OGCouplingResponse (_input : ResearchP3OGInput) : Nat := 0

def researchP3OGTick (state : ResearchP3OGState) : ResearchP3OGState :=
  match state.boundary with
  | .removed => state
  | .alive =>
      match state.maintenanceControl with
      | .active =>
          let step :=
            match state.retainedResidue with
            | none => 1
            | some residue => 1 + residue
          { state with phase := (state.phase + step) % 3 }
      | .disabled =>
          {
            boundary := .removed
            maintenanceControl := .disabled
            phase := 0
            retainedResidue := none
            maintenanceCredit := 0
          }

def researchP3OGAblateMaintenance (state : ResearchP3OGState) : ResearchP3OGState :=
  { state with maintenanceControl := .disabled }

def researchP3OGLeftCoupled : ResearchP3OGState :=
  researchP3OGCouple .f0 researchP3OGClosedState

def researchP3OGRightCoupled : ResearchP3OGState :=
  researchP3OGCouple .f1 researchP3OGClosedState

def researchP3OGRetentionClaim {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) : Prop :=
  researchP3OGLeftCoupled.retainedResidue =
      some (researchP3OGArithmeticInput hp n .f0).val /\
  researchP3OGRightCoupled.retainedResidue =
      some (researchP3OGArithmeticInput hp n .f1).val /\
  researchP3OGCouplingResponse .f0 = researchP3OGCouplingResponse .f1 /\
  researchP3OGLeftCoupled.retainedResidue ≠
    researchP3OGRightCoupled.retainedResidue /\
  (researchP3OGTick researchP3OGLeftCoupled).boundary = .alive /\
  (researchP3OGTick researchP3OGRightCoupled).boundary = .alive /\
  (researchP3OGTick researchP3OGLeftCoupled).retainedResidue ≠
    (researchP3OGTick researchP3OGRightCoupled).retainedResidue /\
  (researchP3OGTick researchP3OGLeftCoupled).phase ≠
    (researchP3OGTick researchP3OGRightCoupled).phase

theorem RESEARCH_OG_T004_retained_difference_changes_later_phase {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) :
    researchP3OGRetentionClaim hp n := by
  have hpone : 1 < p := Nat.lt_of_lt_of_le Nat.one_lt_two hp.two_le
  have hmod : 1 < veyraModulus p n := by
    simpa [veyraModulus] using Nat.one_lt_pow (Nat.succ_ne_zero n) hpone
  simp [researchP3OGRetentionClaim, researchP3OGCouplingResponse,
    researchP3OGLeftCoupled, researchP3OGRightCoupled, researchP3OGCouple,
    researchP3OGClosedState, researchP3OGInputIndex, researchP3OGTick,
    researchP3OGArithmeticInput, veyraRho, veyraIntegerFamily,
    veyraIntegerResidue, Fin.intCast, Nat.mod_eq_of_lt hmod]

def researchP3OGMatchedExceptMaintenance
    (before after : ResearchP3OGState) : Prop :=
  before.boundary = after.boundary /\
  before.phase = after.phase /\
  before.retainedResidue = after.retainedResidue /\
  before.maintenanceCredit = after.maintenanceCredit /\
  before.maintenanceControl = .active /\
  after.maintenanceControl = .disabled

def researchP3OGAblationClaim {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) : Prop :=
  researchP3OGLeftCoupled.retainedResidue =
      some (researchP3OGArithmeticInput hp n .f0).val /\
  researchP3OGRightCoupled.retainedResidue =
      some (researchP3OGArithmeticInput hp n .f1).val /\
  researchP3OGMatchedExceptMaintenance
      researchP3OGLeftCoupled
      (researchP3OGAblateMaintenance researchP3OGLeftCoupled) /\
  researchP3OGMatchedExceptMaintenance
      researchP3OGRightCoupled
      (researchP3OGAblateMaintenance researchP3OGRightCoupled) /\
  (researchP3OGTick
      (researchP3OGAblateMaintenance researchP3OGLeftCoupled)).boundary = .removed /\
  (researchP3OGTick
      (researchP3OGAblateMaintenance researchP3OGRightCoupled)).boundary = .removed /\
  (researchP3OGTick
      (researchP3OGAblateMaintenance researchP3OGLeftCoupled)).retainedResidue = none /\
  (researchP3OGTick
      (researchP3OGAblateMaintenance researchP3OGRightCoupled)).retainedResidue = none

theorem RESEARCH_OG_T005_matched_ablation_removes_declared_ability {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) :
    researchP3OGAblationClaim hp n := by
  have hpone : 1 < p := Nat.lt_of_lt_of_le Nat.one_lt_two hp.two_le
  have hmod : 1 < veyraModulus p n := by
    simpa [veyraModulus] using Nat.one_lt_pow (Nat.succ_ne_zero n) hpone
  simp [researchP3OGAblationClaim, researchP3OGMatchedExceptMaintenance,
    researchP3OGAblateMaintenance, researchP3OGLeftCoupled,
    researchP3OGRightCoupled, researchP3OGCouple, researchP3OGClosedState,
    researchP3OGInputIndex, researchP3OGTick, researchP3OGArithmeticInput,
    veyraRho, veyraIntegerFamily, veyraIntegerResidue, Fin.intCast,
    Nat.mod_eq_of_lt hmod]

inductive ResearchP3OGHistoryEvent where
  | source
  | pool
  | selector
  | selection
  | firstClosure
  | arithmeticInput
  | coupling
  | typedAblation
  | retainedDifference
  | phaseEffect
  | removalDependence
  | decisiveCriterion
  | laterResult
  deriving DecidableEq, Repr

def researchP3OGEventRank : ResearchP3OGHistoryEvent -> Nat
  | .source => 0
  | .pool => 1
  | .selector => 2
  | .selection => 3
  | .firstClosure => 4
  | .arithmeticInput => 5
  | .coupling => 6
  | .typedAblation => 7
  | .retainedDifference => 8
  | .phaseEffect => 9
  | .removalDependence => 10
  | .decisiveCriterion => 11
  | .laterResult => 12

def researchP3OGParentRanks : ResearchP3OGHistoryEvent -> List Nat
  | .source => []
  | .pool => [0]
  | .selector => [0]
  | .selection => [1, 2]
  | .firstClosure => [3]
  | .arithmeticInput => [0, 4]
  | .coupling => [4, 5]
  | .typedAblation => [6]
  | .retainedDifference => [6]
  | .phaseEffect => [8]
  | .removalDependence => [7, 9]
  | .decisiveCriterion => [10]
  | .laterResult => [10, 11]

def researchP3OGHistoryClaim : Prop :=
  (forall event parentRank,
      parentRank ∈ researchP3OGParentRanks event ->
        parentRank < researchP3OGEventRank event) /\
  researchP3OGEventRank .selection < researchP3OGEventRank .firstClosure /\
  researchP3OGEventRank .firstClosure < researchP3OGEventRank .decisiveCriterion /\
  researchP3OGEventRank .firstClosure < researchP3OGEventRank .laterResult

theorem RESEARCH_OG_T006_history_edges_are_forward :
    researchP3OGHistoryClaim := by
  unfold researchP3OGHistoryClaim
  constructor
  · intro event parentRank member
    cases event <;>
      simp [researchP3OGParentRanks, researchP3OGEventRank] at member ⊢ <;>
      omega
  constructor
  · decide
  constructor <;> decide

structure ResearchP3OGBoundedWitness {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) : Prop where
  arithmeticDistinct :
    researchP3OGArithmeticInput hp n .f0 ≠
      researchP3OGArithmeticInput hp n .f1
  selectionOneShot :
    researchP3OGConsumeSelection .available = some (.alpha, .consumed) /\
      researchP3OGConsumeSelection .consumed = none
  genuineFirstClosure :
    researchP3OGFormationTick .unformed = .closed /\
      researchP3OGIsClosed .unformed = false /\
      researchP3OGIsClosed (researchP3OGFormationTick .unformed) = true
  retainedLaterEffect : researchP3OGRetentionClaim hp n
  matchedRemoval : researchP3OGAblationClaim hp n
  forwardHistory : researchP3OGHistoryClaim

theorem RESEARCH_OG_T007_bounded_candidate_witness {p : Nat}
    (hp : VeyraPrimeWitness p) (n : Nat) :
    ResearchP3OGBoundedWitness hp n := by
  exact {
    arithmeticDistinct := RESEARCH_OG_T001_f0_f1_arithmetic_distinct hp n
    selectionOneShot := RESEARCH_OG_T002_selection_is_consumed_one_shot
    genuineFirstClosure := RESEARCH_OG_T003_first_closure_is_genuine
    retainedLaterEffect := RESEARCH_OG_T004_retained_difference_changes_later_phase hp n
    matchedRemoval := RESEARCH_OG_T005_matched_ablation_removes_declared_ability hp n
    forwardHistory := RESEARCH_OG_T006_history_edges_are_forward
  }

def researchP3OGCurrentExecutableFixtureId : String :=
  "semantic-complete-history-current"

def researchP3OGCurrentExecutablePrime : Nat := 3
def researchP3OGCurrentExecutableDepth : Nat := 1
def researchP3OGCurrentExecutableMaintenanceCredit : Nat := 1
def researchP3OGCurrentExecutableLeftResidue : Nat := 0
def researchP3OGCurrentExecutableRightResidue : Nat := 1
def researchP3OGCurrentExecutableLeftAfterPhase : Nat := 1
def researchP3OGCurrentExecutableRightAfterPhase : Nat := 2

def researchP3OGCurrentPrimeWitness :
    VeyraPrimeWitness researchP3OGCurrentExecutablePrime := by
  constructor <;> decide

def researchP3OGCurrentExecutableClaim : Prop :=
  researchP3OGClosedState.maintenanceCredit =
      researchP3OGCurrentExecutableMaintenanceCredit /\
  researchP3OGLeftCoupled.retainedResidue =
      some researchP3OGCurrentExecutableLeftResidue /\
  researchP3OGRightCoupled.retainedResidue =
      some researchP3OGCurrentExecutableRightResidue /\
  (researchP3OGTick researchP3OGLeftCoupled).phase =
      researchP3OGCurrentExecutableLeftAfterPhase /\
  (researchP3OGTick researchP3OGRightCoupled).phase =
      researchP3OGCurrentExecutableRightAfterPhase /\
  researchP3OGRetentionClaim
      researchP3OGCurrentPrimeWitness researchP3OGCurrentExecutableDepth /\
  researchP3OGAblationClaim
      researchP3OGCurrentPrimeWitness researchP3OGCurrentExecutableDepth

theorem RESEARCH_OG_T008_current_executable_candidate :
    researchP3OGCurrentExecutableClaim /\
      ResearchP3OGBoundedWitness
        researchP3OGCurrentPrimeWitness researchP3OGCurrentExecutableDepth := by
  constructor
  · refine ⟨rfl, rfl, rfl, rfl, rfl, ?_, ?_⟩
    · exact RESEARCH_OG_T004_retained_difference_changes_later_phase
        researchP3OGCurrentPrimeWitness researchP3OGCurrentExecutableDepth
    · exact RESEARCH_OG_T005_matched_ablation_removes_declared_ability
        researchP3OGCurrentPrimeWitness researchP3OGCurrentExecutableDepth
  · exact RESEARCH_OG_T007_bounded_candidate_witness
      researchP3OGCurrentPrimeWitness researchP3OGCurrentExecutableDepth


#print axioms RESEARCH_OG_T001_f0_f1_arithmetic_distinct
#print axioms RESEARCH_OG_T002_selection_is_consumed_one_shot
#print axioms RESEARCH_OG_T003_first_closure_is_genuine
#print axioms RESEARCH_OG_T004_retained_difference_changes_later_phase
#print axioms RESEARCH_OG_T005_matched_ablation_removes_declared_ability
#print axioms RESEARCH_OG_T006_history_edges_are_forward
#print axioms RESEARCH_OG_T007_bounded_candidate_witness
#print axioms RESEARCH_OG_T008_current_executable_candidate

end Veyra
