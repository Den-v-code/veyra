import VeyraProofKernel
import VeyraProofSoundness
import VeyraRecurrenceModeBridge
import VeyraObserverProof
import VeyraIntrinsicVamBridge

/- R13 standalone semantic nucleus. THM-R13-001 represents exact R7 checker
   acceptance of the elaborated source proof; surface-parser acceptance remains
   outside this Lean module. No reflection or observer-totality is claimed. -/
namespace VeyraIntrinsicObserverEcho
open Veyra
open VeyraProof
open VeyraTransport
open VeyraObserver
open VeyraIntrinsicRuntime
open VeyraIntrinsicVam

def unitRecurrence : Recurrence := .pulse .silence

def capturedUnitWeaveGoal : Formula 0 :=
  .forallE .recurrence
    (.equal (.weave (.var 0) (.pulse .silence)) (.var 0))

def capturedUnitWeaveProof : Proof 0 :=
  .forallIntro .recurrence
    (.nativeLaw .weaveUnitRight [(.var 0)])

def emptyEnv : Env 0 := fun index => Fin.elim0 index

theorem THM_R13_001_captured_unit_weave_accepted :
    check [] capturedUnitWeaveProof capturedUnitWeaveGoal = true := by
  rfl

private theorem capturedUnitWeaveSemantics (value : Recurrence) :
    weave value unitRecurrence = value := by
  have sound :=
    THM_R7_001_check_sound emptyEnv (context := [])
      (proof := capturedUnitWeaveProof) (goal := capturedUnitWeaveGoal)
      trivial THM_R13_001_captured_unit_weave_accepted
  simpa [capturedUnitWeaveGoal, Semantics, eval, extendEnv, unitRecurrence] using
    sound value

theorem THM_R13_002_unit_weave_semantics_and_image (value : Recurrence) :
    weave value unitRecurrence = value ∧
      VeyraIntrinsicRuntime.weave
        (encodeMode value) (encodeMode unitRecurrence) =
          .ready (encodeMode value) := by
  constructor
  · exact capturedUnitWeaveSemantics value
  · simpa [unitRecurrence, weave_single_pulse_right] using
      (THM_R9_006_weave_preserved value unitRecurrence)

theorem THM_R13_003_ready_intrinsic_unit_weave_echo {target : Kind}
    (observer : Observer .recurrence target) (value : Recurrence)
    (response : Response target)
    (observerBound : observerBounded observer)
    (valueBound : r11RecurrenceBounded value)
    (outcomeBound : echoOutcomeBounded (echo observer value value))
    (ready :
      observeIntrinsic observer (intrinsicMode value) = .ready response) :
    echoIR observer
      (lowerRecurrenceIR (weave value unitRecurrence))
      (lowerRecurrenceIR value) =
        some (.echo (lowerResponseIR response)) := by
  have sourceReady : observe observer value = .ready response := by
    simpa [observeIntrinsic_image] using ready
  rw [THM_R13_002_unit_weave_semantics_and_image value |>.1]
  calc
    echoIR observer (lowerRecurrenceIR value) (lowerRecurrenceIR value) =
        some (lowerEchoOutcomeIR (echo observer value value)) :=
      THM_R12_008_echo_transport observer value value observerBound
        valueBound valueBound outcomeBound
    _ = some (.echo (lowerResponseIR response)) := by
      rw [THM_R11_002_ready_domain_reflexivity observer value response sourceReady]
      rfl

theorem THM_R13_004_tail_silence_two_sided_domain_blocked :
    echoIR tailObserver
      (lowerRecurrenceIR (weave .silence unitRecurrence))
      (lowerRecurrenceIR .silence) =
        some (.domainBlocked
          [{ code := .tailOfSilence, path := [.applyTail] }]
          [{ code := .tailOfSilence, path := [.applyTail] }]) := by
  have observerBound : observerBounded tailObserver := by
    simp [observerBounded, observerNodes, observerDepth, tailObserver]
  have valueBound : r11RecurrenceBounded (.silence : Recurrence) := by
    simp [r11RecurrenceBounded, recurrenceTacts]
  have outcomeBound :
      echoOutcomeBounded (echo tailObserver .silence .silence) := by
    rw [THM_R11_005_both_side_echo_domain_obstruction]
    simp [echoOutcomeBounded, obstructionListBounded]
  rw [THM_R13_002_unit_weave_semantics_and_image .silence |>.1]
  simpa [THM_R11_005_both_side_echo_domain_obstruction, lowerEchoOutcomeIR,
    lowerObstructionIR, lowerPathStepIR] using
      (THM_R12_008_echo_transport tailObserver .silence .silence
        observerBound valueBound valueBound outcomeBound)

theorem THM_R13_005_crest_nonreflection :
    echoIR crestObserver
        (lowerRecurrenceIR (.pulse .silence))
        (lowerRecurrenceIR (.pulse (.pulse .silence))) =
          some (.echo (.mark .pulse)) ∧
      lowerRecurrenceIR (.pulse .silence) ≠
        lowerRecurrenceIR (.pulse (.pulse .silence)) := by
  have observerBound : observerBounded crestObserver := by
    simp [observerBounded, observerNodes, observerDepth, crestObserver]
  have leftR11Bound :
      r11RecurrenceBounded (.pulse .silence) := by
    simp [r11RecurrenceBounded, recurrenceTacts]
  have rightR11Bound :
      r11RecurrenceBounded (.pulse (.pulse .silence)) := by
    simp [r11RecurrenceBounded, recurrenceTacts]
  have leftR12Bound : recurrenceBounded (.pulse .silence) := by
    simp [recurrenceBounded, recurrenceTacts]
  have rightR12Bound : recurrenceBounded (.pulse (.pulse .silence)) := by
    simp [recurrenceBounded, recurrenceTacts]
  constructor
  · have sourceEcho := THM_R11_006_crest_noncollapse_witness
    have outcomeBound :
        echoOutcomeBounded
          (echo crestObserver (.pulse .silence) (.pulse (.pulse .silence))) := by
      rw [sourceEcho.1]
      simp [echoOutcomeBounded, responseBounded, responseNodes, responseDepth,
        intrinsicResponseNodes, intrinsicResponseDepth, responseTactsBounded]
    rw [THM_R12_008_echo_transport crestObserver
      (.pulse .silence) (.pulse (.pulse .silence))
      observerBound leftR11Bound rightR11Bound outcomeBound]
    simp [sourceEcho.1, lowerEchoOutcomeIR, lowerResponseIR, lowerMarkIR]
  · intro loweredSame
    exact THM_R11_006_crest_noncollapse_witness.2
      (THM_R12_003_lower_recurrence_injective
        (.pulse .silence) (.pulse (.pulse .silence))
        leftR12Bound rightR12Bound loweredSame)

end VeyraIntrinsicObserverEcho
