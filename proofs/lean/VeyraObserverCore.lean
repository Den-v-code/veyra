import VeyraRecurrenceModeBridge

/- A typed, conservative observer calculus over native recurrences. -/
namespace VeyraObserver
open Veyra
open VeyraTransport

inductive Kind where
  | recurrence
  | mark
  | pair : Kind → Kind → Kind
deriving Repr, DecidableEq

inductive Mark where
  | silent
  | pulse
deriving Repr, DecidableEq

inductive Primitive : Kind → Kind → Type where
  | tail : Primitive .recurrence .recurrence
  | crest : Primitive .recurrence .mark
deriving Repr, DecidableEq

inductive Observer : Kind → Kind → Type where
  | input {kind : Kind} : Observer kind kind
  | apply {middle target source : Kind} :
      Primitive middle target → Observer source middle → Observer source target
  | pair {source left right : Kind} : Observer source left → Observer source right →
      Observer source (.pair left right)
deriving Repr, DecidableEq

inductive Response : Kind → Type where
  | recurrence : Recurrence → Response .recurrence
  | mark : Mark → Response .mark
  | pair : Response left → Response right → Response (.pair left right)
deriving Repr, DecidableEq

inductive PathStep where
  | applyTail
  | applyCrest
  | pairLeft
  | pairRight
deriving Repr, DecidableEq

inductive ObstructionCode where
  | tailOfSilence
deriving Repr, DecidableEq

/-- The path is stored outer-to-inner; evaluator-produced paths are always nonempty. -/
structure ObserverObstruction where
  code : ObstructionCode
  path : List PathStep
deriving Repr, DecidableEq

inductive Observation (kind : Kind) where
  | ready : Response kind → Observation kind
  | blocked : List ObserverObstruction → Observation kind
deriving Repr, DecidableEq

inductive EchoOutcome (kind : Kind) where
  | echo : Response kind → EchoOutcome kind
  | mismatch : Response kind → Response kind → EchoOutcome kind
  | domainBlocked : List ObserverObstruction → List ObserverObstruction → EchoOutcome kind
deriving Repr, DecidableEq

def primitiveStep {source target : Kind} (primitive : Primitive source target) : PathStep :=
  match primitive with
  | .tail => .applyTail
  | .crest => .applyCrest

def prefixObstruction (step : PathStep)
    (obstruction : ObserverObstruction) : ObserverObstruction :=
  { obstruction with path := step :: obstruction.path }

def prefixObstructions (step : PathStep)
    (obstructions : List ObserverObstruction) : List ObserverObstruction :=
  obstructions.map (prefixObstruction step)

def tailOfSilenceObstruction : ObserverObstruction :=
  { code := .tailOfSilence, path := [.applyTail] }

def runPrimitive {source target : Kind} (primitive : Primitive source target) :
    Response source → Observation target
  | .recurrence value =>
      match primitive, value with
      | .tail, .silence => .blocked [tailOfSilenceObstruction]
      | .tail, .pulse tail => .ready (.recurrence tail)
      | .crest, .silence => .ready (.mark .silent)
      | .crest, .pulse _ => .ready (.mark .pulse)

def runObserver {source target : Kind} (observer : Observer source target)
    (input : Response source) : Observation target :=
  match observer with
  | .input => .ready input
  | .apply primitive inner =>
      match runObserver inner input with
      | .ready response => runPrimitive primitive response
      | .blocked obstructions =>
          .blocked (prefixObstructions (primitiveStep primitive) obstructions)
  | .pair left right =>
      match runObserver left input, runObserver right input with
      | .ready leftResponse, .ready rightResponse =>
          .ready (.pair leftResponse rightResponse)
      | .blocked leftObstructions, .ready _ =>
          .blocked (prefixObstructions .pairLeft leftObstructions)
      | .ready _, .blocked rightObstructions =>
          .blocked (prefixObstructions .pairRight rightObstructions)
      | .blocked leftObstructions, .blocked rightObstructions =>
          .blocked (prefixObstructions .pairLeft leftObstructions ++
            prefixObstructions .pairRight rightObstructions)
termination_by sizeOf observer

def observe {target : Kind} (observer : Observer .recurrence target)
    (value : Recurrence) : Observation target :=
  runObserver observer (.recurrence value)

def echo {target : Kind} (observer : Observer .recurrence target)
    (left right : Recurrence) : EchoOutcome target :=
  match observe observer left, observe observer right with
  | .ready leftResponse, .ready rightResponse =>
      if leftResponse = rightResponse then .echo leftResponse
      else .mismatch leftResponse rightResponse
  | .blocked leftObstructions, .ready _ => .domainBlocked leftObstructions []
  | .ready _, .blocked rightObstructions => .domainBlocked [] rightObstructions
  | .blocked leftObstructions, .blocked rightObstructions =>
      .domainBlocked leftObstructions rightObstructions

/-- The executable decoder is total on the `IntrinsicMode` image subtype. -/
def decodeIntrinsic (value : IntrinsicMode) : Recurrence :=
  (decodeMode value.1).getD .silence

def observeDecodedMode {target : Kind} (observer : Observer .recurrence target)
    (value : VeyraMode) : Option (Observation target) :=
  (decodeMode value).map (observe observer)

def observeIntrinsic {target : Kind} (observer : Observer .recurrence target)
    (value : IntrinsicMode) : Observation target :=
  observe observer (decodeIntrinsic value)

theorem decodeIntrinsic_image (value : Recurrence) :
    decodeIntrinsic (intrinsicMode value) = value := by
  simp [decodeIntrinsic, intrinsicMode, THM_R9_002_decode_encode]

theorem observeDecodedMode_image {target : Kind}
    (observer : Observer .recurrence target) (value : Recurrence) :
    observeDecodedMode observer (encodeMode value) = some (observe observer value) := by
  simp [observeDecodedMode, THM_R9_002_decode_encode]

theorem observeIntrinsic_image {target : Kind}
    (observer : Observer .recurrence target) (value : Recurrence) :
    observeIntrinsic observer (intrinsicMode value) = observe observer value := by
  simp [observeIntrinsic, decodeIntrinsic_image]

def tailObserver : Observer .recurrence .recurrence :=
  .apply .tail .input

def crestObserver : Observer .recurrence .mark :=
  .apply .crest .input

def tailCrestObserver : Observer .recurrence .mark :=
  .apply .crest tailObserver

end VeyraObserver
