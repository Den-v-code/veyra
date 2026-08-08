import VeyraObserverCore
import VeyraProofSoundness

/- Proof-grade observer laws. R7 remains unchanged and is consumed only through soundness. -/
namespace VeyraObserver
open Veyra
open VeyraProof

theorem THM_R11_001_ready_echo_characterization {target : Kind}
    (observer : Observer .recurrence target) (left right : Recurrence)
    (response : Response target) :
    echo observer left right = .echo response ↔
      observe observer left = .ready response ∧
      observe observer right = .ready response := by
  cases leftObservation : observe observer left with
  | blocked leftPaths =>
      cases rightObservation : observe observer right <;>
        simp [echo, leftObservation, rightObservation]
  | ready leftResponse =>
      cases rightObservation : observe observer right with
      | blocked rightPaths => simp [echo, leftObservation, rightObservation]
      | ready rightResponse =>
          by_cases same : leftResponse = rightResponse
          · subst rightResponse
            simp [echo, leftObservation, rightObservation]
          · constructor
            · intro echoed
              simp [echo, leftObservation, rightObservation, same] at echoed
            · intro observations
              have leftSame : leftResponse = response := by
                simpa [leftObservation] using observations.1
              have rightSame : rightResponse = response := by
                simpa [rightObservation] using observations.2
              exact (same (leftSame.trans rightSame.symm)).elim

theorem THM_R11_002_ready_domain_reflexivity {target : Kind}
    (observer : Observer .recurrence target) (value : Recurrence)
    (response : Response target)
    (ready : observe observer value = .ready response) :
    echo observer value value = .echo response := by
  simp [echo, ready]

theorem THM_R11_003_r7_equality_implies_ready_echo {arity : Nat}
    (env : Env arity) {context : Context arity} {proof : Proof arity}
    {left right : Term arity} {target : Kind}
    (observer : Observer .recurrence target) (response : Response target)
    (holds : ContextHolds env context)
    (accepted : check context proof (.equal left right) = true)
    (ready : observe observer (eval env left) = .ready response) :
    echo observer (eval env left) (eval env right) = .echo response := by
  have equalSemantics : eval env left = eval env right :=
    THM_R7_001_check_sound env holds accepted
  rw [equalSemantics] at ready ⊢
  exact THM_R11_002_ready_domain_reflexivity observer _ response ready

theorem THM_R11_004_tail_silence_obstruction :
    observe tailObserver .silence =
      .blocked [{ code := .tailOfSilence, path := [.applyTail] }] := by
  simp [observe, tailObserver, runObserver, runPrimitive,
    tailOfSilenceObstruction]

theorem THM_R11_005_both_side_echo_domain_obstruction :
    echo tailObserver .silence .silence =
      .domainBlocked
        [{ code := .tailOfSilence, path := [.applyTail] }]
        [{ code := .tailOfSilence, path := [.applyTail] }] := by
  simp [echo, observe, tailObserver, runObserver, runPrimitive,
    tailOfSilenceObstruction]

theorem THM_R11_006_crest_noncollapse_witness :
    echo crestObserver (.pulse .silence) (.pulse (.pulse .silence)) =
        .echo (.mark .pulse) ∧
      (.pulse .silence : Recurrence) ≠ .pulse (.pulse .silence) := by
  simp [echo, observe, crestObserver, runObserver, runPrimitive]

end VeyraObserver
