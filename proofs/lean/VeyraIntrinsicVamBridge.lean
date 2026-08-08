import VeyraObserverProof
/- Transport mirror over the bounded R12.2/R12.3 lowering domain.
   Binary framing and receipt authentication remain external. -/
namespace VeyraIntrinsicVam
open Veyra VeyraTransport VeyraObserver VeyraIntrinsicRuntime
inductive IntrinsicAnchorIR where | origin deriving Repr, DecidableEq
inductive IntrinsicTactIR where | successor deriving Repr, DecidableEq
structure IntrinsicRecurrenceIR where
  tacts : List IntrinsicTactIR
  anchor : Option IntrinsicAnchorIR
deriving Repr, DecidableEq
inductive IntrinsicMarkIR where | silent | pulse deriving Repr, DecidableEq
inductive IntrinsicPathStepIR where | applyTail | applyCrest | pairLeft | pairRight deriving Repr, DecidableEq
inductive IntrinsicObstructionCodeIR where | tailOfSilence deriving Repr, DecidableEq
structure IntrinsicObstructionIR where
  code : IntrinsicObstructionCodeIR
  path : List IntrinsicPathStepIR
deriving Repr, DecidableEq
inductive IntrinsicResponseIR : Kind → Type where
  | recurrence : IntrinsicRecurrenceIR → IntrinsicResponseIR .recurrence
  | mark : IntrinsicMarkIR → IntrinsicResponseIR .mark
  | pair : IntrinsicResponseIR left → IntrinsicResponseIR right → IntrinsicResponseIR (.pair left right)
deriving Repr, DecidableEq
inductive IntrinsicObservationIR (kind : Kind) where
  | ready : IntrinsicResponseIR kind → IntrinsicObservationIR kind
  | blocked : List IntrinsicObstructionIR → IntrinsicObservationIR kind
deriving Repr, DecidableEq
inductive IntrinsicEchoOutcomeIR (kind : Kind) where
  | echo : IntrinsicResponseIR kind → IntrinsicEchoOutcomeIR kind
  | mismatch : IntrinsicResponseIR kind → IntrinsicResponseIR kind → IntrinsicEchoOutcomeIR kind
  | domainBlocked : List IntrinsicObstructionIR → List IntrinsicObstructionIR → IntrinsicEchoOutcomeIR kind
deriving Repr, DecidableEq
def recurrenceFromTacts : List IntrinsicTactIR → IntrinsicRecurrenceIR
  | [] => { tacts := [], anchor := some .origin }
  | run@(_ :: _) => { tacts := run, anchor := none }
def validRecurrenceIR (value : IntrinsicRecurrenceIR) : Bool :=
  match value.tacts, value.anchor with
  | [], some .origin => true | _ :: _, none => true | _, _ => false
def recurrenceTacts : Recurrence → List IntrinsicTactIR
  | .silence => [] | .pulse tail => .successor :: recurrenceTacts tail
def recurrenceBounded (value : Recurrence) : Prop := (recurrenceTacts value).length ≤ 2047
def r11RecurrenceBounded (value : Recurrence) : Prop := (recurrenceTacts value).length ≤ 128
def observerNodes {source target : Kind} : Observer source target → Nat
  | .input => 1 | .apply _ inner => observerNodes inner + 1
  | .pair left right => observerNodes left + observerNodes right + 1
def observerDepth {source target : Kind} : Observer source target → Nat
  | .input => 0 | .apply _ inner => observerDepth inner + 1
  | .pair left right => max (observerDepth left) (observerDepth right) + 1
def observerBounded {source target : Kind} (value : Observer source target) : Prop :=
  observerNodes value ≤ 2048 ∧ observerDepth value ≤ 128
def responseNodes {kind : Kind} : Response kind → Nat
  | .recurrence _ | .mark _ => 1 | .pair left right => responseNodes left + responseNodes right + 1
def responseDepth {kind : Kind} : Response kind → Nat
  | .recurrence _ | .mark _ => 0 | .pair left right => max (responseDepth left) (responseDepth right) + 1
def intrinsicResponseNodes {kind : Kind} : Response kind → Nat
  | .recurrence value => let n := (recurrenceTacts value).length; if n = 0 then 3 else n + 2
  | .mark _ => 1
  | .pair left right => intrinsicResponseNodes left + intrinsicResponseNodes right + 1
def intrinsicResponseDepth {kind : Kind} : Response kind → Nat
  | .recurrence _ => 2 | .mark _ => 0
  | .pair left right => max (intrinsicResponseDepth left) (intrinsicResponseDepth right) + 1
def responseTactsBounded {kind : Kind} : Response kind → Prop
  | .recurrence value => r11RecurrenceBounded value | .mark _ => True
  | .pair left right => responseTactsBounded left ∧ responseTactsBounded right
def responseBounded {kind : Kind} (value : Response kind) : Prop :=
  responseNodes value ≤ 2048 ∧ responseDepth value ≤ 128 ∧ intrinsicResponseNodes value ≤ 4096 ∧
    intrinsicResponseDepth value ≤ 128 ∧ responseTactsBounded value
def obstructionListBounded (values : List ObserverObstruction) : Prop :=
  values.length ≤ 2048 ∧ ∀ value ∈ values, 0 < value.path.length ∧ value.path.length ≤ 128
def observationBounded {kind : Kind} : Observation kind → Prop
  | .ready value => responseBounded value ∧ intrinsicResponseNodes value + 1 ≤ 4096 ∧
      intrinsicResponseDepth value + 1 ≤ 128
  | .blocked values => values ≠ [] ∧ obstructionListBounded values
def echoOutcomeBounded {kind : Kind} : EchoOutcome kind → Prop
  | .echo value => responseBounded value ∧ intrinsicResponseNodes value + 1 ≤ 4096 ∧
      intrinsicResponseDepth value + 1 ≤ 128
  | .mismatch left right => responseBounded left ∧ responseBounded right ∧
      intrinsicResponseNodes left + intrinsicResponseNodes right + 1 ≤ 4096 ∧
      max (intrinsicResponseDepth left) (intrinsicResponseDepth right) + 1 ≤ 128
  | .domainBlocked left right => left ++ right ≠ [] ∧ (left ++ right).length ≤ 2048 ∧
      obstructionListBounded left ∧ obstructionListBounded right
def lowerRecurrenceIR (value : Recurrence) : IntrinsicRecurrenceIR := recurrenceFromTacts (recurrenceTacts value)
def decodeTacts : List IntrinsicTactIR → Recurrence
  | [] => .silence | .successor :: tail => .pulse (decodeTacts tail)
def decodeRecurrenceIR (value : IntrinsicRecurrenceIR) : Option Recurrence :=
  if validRecurrenceIR value then some (decodeTacts value.tacts) else none
def realizeRecurrenceIR (value : IntrinsicRecurrenceIR) : Option VeyraBreath :=
  if validRecurrenceIR value then some {
    tacts := value.tacts.map (fun _ => successorTact)
    anchor := if value.tacts.isEmpty then some originNode else none } else none
def lowerMarkIR : Mark → IntrinsicMarkIR
  | .silent => .silent | .pulse => .pulse
def lowerPathStepIR : PathStep → IntrinsicPathStepIR
  | .applyTail => .applyTail | .applyCrest => .applyCrest
  | .pairLeft => .pairLeft | .pairRight => .pairRight
def lowerObstructionIR (value : ObserverObstruction) : IntrinsicObstructionIR :=
  { code := .tailOfSilence, path := value.path.map lowerPathStepIR }
def prefixObstructionIR (step : IntrinsicPathStepIR)
    (value : IntrinsicObstructionIR) : IntrinsicObstructionIR := { value with path := step :: value.path }
def lowerResponseIR {kind : Kind} : Response kind → IntrinsicResponseIR kind
  | .recurrence value => .recurrence (lowerRecurrenceIR value)
  | .mark value => .mark (lowerMarkIR value)
  | .pair left right => .pair (lowerResponseIR left) (lowerResponseIR right)
def lowerObservationIR {kind : Kind} : Observation kind → IntrinsicObservationIR kind
  | .ready value => .ready (lowerResponseIR value)
  | .blocked values => .blocked (values.map lowerObstructionIR)
def lowerEchoOutcomeIR {kind : Kind} : EchoOutcome kind → IntrinsicEchoOutcomeIR kind
  | .echo value => .echo (lowerResponseIR value)
  | .mismatch left right => .mismatch (lowerResponseIR left) (lowerResponseIR right)
  | .domainBlocked left right => .domainBlocked (left.map lowerObstructionIR) (right.map lowerObstructionIR)
def prefixObstructionsIR (step : IntrinsicPathStepIR)
    (values : List IntrinsicObstructionIR) : List IntrinsicObstructionIR := values.map (prefixObstructionIR step)
def runPrimitiveIR {source target : Kind} (primitive : Primitive source target) :
    IntrinsicResponseIR source → Option (IntrinsicObservationIR target)
  | .recurrence value =>
      if validRecurrenceIR value then
        match primitive, value.tacts with
        | .tail, [] => some (.blocked [{ code := .tailOfSilence, path := [.applyTail] }])
        | .tail, _ :: tail => some (.ready (.recurrence (recurrenceFromTacts tail)))
        | .crest, [] => some (.ready (.mark .silent))
        | .crest, _ :: _ => some (.ready (.mark .pulse))
      else none
def runObserverIR {source target : Kind} (observer : Observer source target)
    (input : IntrinsicResponseIR source) : Option (IntrinsicObservationIR target) :=
  match observer with
  | .input => some (.ready input)
  | .apply primitive inner =>
      match runObserverIR inner input with
      | none => none
      | some (.ready response) => runPrimitiveIR primitive response
      | some (.blocked obstructions) =>
          some (.blocked (prefixObstructionsIR
            (lowerPathStepIR (primitiveStep primitive)) obstructions))
  | .pair left right =>
      match runObserverIR left input, runObserverIR right input with
      | some (.ready leftResponse), some (.ready rightResponse) =>
          some (.ready (.pair leftResponse rightResponse))
      | some (.blocked leftObstructions), some (.ready _) =>
          some (.blocked (prefixObstructionsIR .pairLeft leftObstructions))
      | some (.ready _), some (.blocked rightObstructions) =>
          some (.blocked (prefixObstructionsIR .pairRight rightObstructions))
      | some (.blocked leftObstructions), some (.blocked rightObstructions) =>
          some (.blocked (prefixObstructionsIR .pairLeft leftObstructions ++
            prefixObstructionsIR .pairRight rightObstructions))
      | _, _ => none
termination_by sizeOf observer
def observeIR {target : Kind} (observer : Observer .recurrence target)
    (value : IntrinsicRecurrenceIR) : Option (IntrinsicObservationIR target) :=
  runObserverIR observer (.recurrence value)
def echoIR {target : Kind} (observer : Observer .recurrence target)
    (left right : IntrinsicRecurrenceIR) : Option (IntrinsicEchoOutcomeIR target) :=
  match observeIR observer left, observeIR observer right with
  | some (.ready leftResponse), some (.ready rightResponse) =>
      if leftResponse = rightResponse then some (.echo leftResponse)
      else some (.mismatch leftResponse rightResponse)
  | some (.blocked leftObstructions), some (.ready _) =>
      some (.domainBlocked leftObstructions [])
  | some (.ready _), some (.blocked rightObstructions) =>
      some (.domainBlocked [] rightObstructions)
  | some (.blocked leftObstructions), some (.blocked rightObstructions) =>
      some (.domainBlocked leftObstructions rightObstructions)
  | _, _ => none
theorem decodeTacts_lower (value : Recurrence) : decodeTacts (recurrenceTacts value) = value := by
  induction value with
  | silence => rfl
  | pulse tail hypothesis => simp [recurrenceTacts, decodeTacts, hypothesis]
theorem realizeTacts_lower (value : Recurrence) :
    (recurrenceTacts value).map (fun _ => successorTact) = (encodeBreath value).tacts := by
  induction value with
  | silence => rfl
  | pulse tail hypothesis => simp [recurrenceTacts, encodeBreath, hypothesis]
theorem lower_recurrence_preserves_image_universal (value : Recurrence) :
    realizeRecurrenceIR (lowerRecurrenceIR value) = some (encodeBreath value) := by
  cases value with
  | silence => rfl
  | pulse tail => simp [lowerRecurrenceIR, recurrenceTacts, recurrenceFromTacts,
      realizeRecurrenceIR, validRecurrenceIR, encodeBreath, realizeTacts_lower]
theorem decode_lower_recurrence_universal (value : Recurrence) :
    decodeRecurrenceIR (lowerRecurrenceIR value) = some value := by
  cases value <;> simp [decodeRecurrenceIR, lowerRecurrenceIR, recurrenceTacts,
    recurrenceFromTacts, validRecurrenceIR, decodeTacts, decodeTacts_lower]
theorem lower_recurrence_injective_universal : Function.Injective lowerRecurrenceIR := by
  intro left right same
  have decoded := congrArg decodeRecurrenceIR same
  simpa [decode_lower_recurrence_universal] using decoded
theorem prefix_obstruction_transport_universal
    (step : PathStep) (value : ObserverObstruction) :
    lowerObstructionIR (prefixObstruction step value) =
      prefixObstructionIR (lowerPathStepIR step) (lowerObstructionIR value) := by
  cases step <;> cases value <;> rfl
theorem runPrimitive_transport_universal {source target : Kind}
    (primitive : Primitive source target) (input : Response source) :
    runPrimitiveIR primitive (lowerResponseIR input) =
      some (lowerObservationIR (runPrimitive primitive input)) := by
  cases primitive <;> cases input with
  | recurrence value => cases value <;> simp [
      runPrimitiveIR, lowerResponseIR, lowerRecurrenceIR, recurrenceTacts,
      recurrenceFromTacts, validRecurrenceIR, runPrimitive, lowerObservationIR,
      tailOfSilenceObstruction, lowerObstructionIR, lowerPathStepIR, lowerMarkIR]
theorem runObserver_transport_universal {source target : Kind}
    (observer : Observer source target) (input : Response source) :
    runObserverIR observer (lowerResponseIR input) =
      some (lowerObservationIR (runObserver observer input)) := by
  induction observer with
  | input => simp [runObserverIR, runObserver, lowerObservationIR]
  | apply primitive inner hypothesis =>
      rw [runObserverIR, runObserver, hypothesis]
      cases result : runObserver inner input with
      | ready response => simpa [lowerObservationIR] using runPrimitive_transport_universal primitive response
      | blocked obstructions =>
          simp [lowerObservationIR, prefixObstructionsIR, prefixObstructions,
            List.map_map, Function.comp_def, prefix_obstruction_transport_universal]
  | pair left right leftHypothesis rightHypothesis =>
      rw [runObserverIR, runObserver, leftHypothesis, rightHypothesis]
      cases runObserver left input <;> cases runObserver right input <;>
        simp [lowerObservationIR, lowerResponseIR, prefixObstructionsIR,
          prefixObstructions, List.map_map, Function.comp_def, lowerPathStepIR,
          prefix_obstruction_transport_universal]
theorem observe_transport_universal {target : Kind}
    (observer : Observer .recurrence target) (value : Recurrence) :
    observeIR observer (lowerRecurrenceIR value) =
      some (lowerObservationIR (observe observer value)) := runObserver_transport_universal observer (.recurrence value)
def raiseResponseIR {kind : Kind} : IntrinsicResponseIR kind → Option (Response kind)
  | .recurrence value => (decodeRecurrenceIR value).map .recurrence
  | .mark .silent => some (.mark .silent)
  | .mark .pulse => some (.mark .pulse)
  | .pair left right => do
      let leftValue ← raiseResponseIR left
      let rightValue ← raiseResponseIR right
      some (.pair leftValue rightValue)
theorem raise_lower_response {kind : Kind} (value : Response kind) :
    raiseResponseIR (lowerResponseIR value) = some value := by
  induction value with
  | recurrence value => simp [raiseResponseIR, lowerResponseIR,
      decode_lower_recurrence_universal]
  | mark value => cases value <;> rfl
  | pair left right leftHypothesis rightHypothesis =>
      simp [raiseResponseIR, lowerResponseIR, leftHypothesis, rightHypothesis]
theorem lowerResponseIR_injective {kind : Kind} : Function.Injective (@lowerResponseIR kind) := by
  intro left right same
  have raised := congrArg raiseResponseIR same
  simpa [raise_lower_response] using raised
theorem echo_transport_universal {target : Kind}
    (observer : Observer .recurrence target) (left right : Recurrence) :
    echoIR observer (lowerRecurrenceIR left) (lowerRecurrenceIR right) =
      some (lowerEchoOutcomeIR (echo observer left right)) := by
  rw [echoIR, observe_transport_universal, observe_transport_universal]
  cases leftResult : observe observer left with
  | blocked leftBlocked =>
      cases rightResult : observe observer right <;>
        simp [echo, leftResult, rightResult, lowerObservationIR, lowerEchoOutcomeIR]
  | ready leftReady =>
      cases rightResult : observe observer right with
      | blocked rightBlocked =>
          simp [echo, leftResult, rightResult, lowerObservationIR, lowerEchoOutcomeIR]
      | ready rightReady =>
          by_cases same : leftReady = rightReady
          · subst rightReady
            simp [echo, leftResult, rightResult, lowerObservationIR, lowerEchoOutcomeIR]
          · have lowerDifferent : lowerResponseIR leftReady ≠ lowerResponseIR rightReady :=
              fun lowered => same (lowerResponseIR_injective lowered)
            simp [echo, leftResult, rightResult, lowerObservationIR,
              lowerEchoOutcomeIR, same, lowerDifferent]
theorem tail_silence_obstruction_transport_universal :
    observeIR tailObserver (lowerRecurrenceIR .silence) =
      some (.blocked [{
        code := .tailOfSilence,
        path := [.applyTail]
      }]) := by
  simpa [observe, tailObserver, runObserver, runPrimitive, lowerObservationIR,
    lowerObstructionIR, lowerPathStepIR, tailOfSilenceObstruction] using
    (observe_transport_universal tailObserver (.silence))
theorem THM_R12_001_lower_recurrence_preserves_image (value : Recurrence) (_ : recurrenceBounded value) :
    realizeRecurrenceIR (lowerRecurrenceIR value) = some (encodeBreath value) := lower_recurrence_preserves_image_universal value
theorem THM_R12_002_decode_lower_recurrence (value : Recurrence) (_ : recurrenceBounded value) :
    decodeRecurrenceIR (lowerRecurrenceIR value) = some value := decode_lower_recurrence_universal value
theorem THM_R12_003_lower_recurrence_injective (left right : Recurrence) (_ : recurrenceBounded left)
    (_ : recurrenceBounded right) : lowerRecurrenceIR left = lowerRecurrenceIR right → left = right := fun same => lower_recurrence_injective_universal same
theorem THM_R12_004_prefix_obstruction_transport (step : PathStep) (value : ObserverObstruction)
    (_ : value.path.length + 1 ≤ 128) : lowerObstructionIR (prefixObstruction step value) =
      prefixObstructionIR (lowerPathStepIR step) (lowerObstructionIR value) := prefix_obstruction_transport_universal step value
theorem THM_R12_005_runPrimitive_transport {source target : Kind} (primitive : Primitive source target)
    (input : Response source) (_ : responseBounded input) (_ : observationBounded (runPrimitive primitive input)) :
    runPrimitiveIR primitive (lowerResponseIR input) = some (lowerObservationIR (runPrimitive primitive input)) :=
  runPrimitive_transport_universal primitive input
theorem THM_R12_006_runObserver_transport {source target : Kind} (observer : Observer source target)
    (input : Response source) (_ : observerBounded observer) (_ : responseBounded input)
    (_ : observationBounded (runObserver observer input)) : runObserverIR observer (lowerResponseIR input) =
      some (lowerObservationIR (runObserver observer input)) := runObserver_transport_universal observer input
theorem THM_R12_007_observe_transport {target : Kind} (observer : Observer .recurrence target) (value : Recurrence)
    (_ : observerBounded observer) (_ : r11RecurrenceBounded value) (_ : observationBounded (observe observer value)) :
    observeIR observer (lowerRecurrenceIR value) = some (lowerObservationIR (observe observer value)) :=
  observe_transport_universal observer value
theorem THM_R12_008_echo_transport {target : Kind} (observer : Observer .recurrence target) (left right : Recurrence)
    (_ : observerBounded observer) (_ : r11RecurrenceBounded left) (_ : r11RecurrenceBounded right)
    (_ : echoOutcomeBounded (echo observer left right)) : echoIR observer (lowerRecurrenceIR left) (lowerRecurrenceIR right) =
      some (lowerEchoOutcomeIR (echo observer left right)) := echo_transport_universal observer left right
theorem THM_R12_009_tail_silence_obstruction_transport : observeIR tailObserver (lowerRecurrenceIR .silence) =
    some (.blocked [{ code := .tailOfSilence, path := [.applyTail] }]) := tail_silence_obstruction_transport_universal
end VeyraIntrinsicVam
