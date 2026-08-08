import VeyraNativeArithmetic
import VeyraIntrinsicRuntime

/- Exact fixed-anchor image bridge between proof recurrences and strict native modes. -/
namespace VeyraTransport
open Veyra
open VeyraIntrinsicRuntime

def encodeBreath : Recurrence → VeyraBreath
  | .silence => { tacts := [], anchor := some originNode }
  | .pulse tail => { tacts := successorTact :: (encodeBreath tail).tacts, anchor := none }

def encodeMode (value : Recurrence) : VeyraMode :=
  { breath := encodeBreath value, observer := "native-cycle" }

def decodeTacts : List VeyraTact → Option Recurrence
  | [] => some .silence
  | head :: tail =>
      if head = successorTact then Option.map .pulse (decodeTacts tail) else none

def decodeMode (value : VeyraMode) : Option Recurrence :=
  if value.observer = "native-cycle" then
    match value.breath.tacts, value.breath.anchor with
    | [], some anchor => if anchor = originNode then some .silence else none
    | [], none => none
    | _ :: _, some _ => none
    | run, none => decodeTacts run
  else none

def IsIntrinsicMode (native : VeyraMode) : Prop :=
  ∃ recurrence : Recurrence, encodeMode recurrence = native

def IntrinsicMode := { native : VeyraMode // IsIntrinsicMode native }

def intrinsicMode (recurrence : Recurrence) : IntrinsicMode :=
  ⟨encodeMode recurrence, ⟨recurrence, rfl⟩⟩

def IntrinsicResonates (factor carrier : IntrinsicMode) : Prop :=
  ∃ witness : IntrinsicMode,
    VeyraIntrinsicRuntime.weave factor.1 witness.1 = .ready carrier.1

theorem decodeTacts_encode (value : Recurrence) :
    decodeTacts (encodeBreath value).tacts = some value := by
  induction value with
  | silence => rfl
  | pulse tail hypothesis => simp [encodeBreath, decodeTacts, successorTact, hypothesis]

theorem THM_R9_002_decode_encode (value : Recurrence) :
    decodeMode (encodeMode value) = some value := by
  cases value with
  | silence => simp [decodeMode, encodeMode, encodeBreath, originNode]
  | pulse tail =>
      change decodeTacts (successorTact :: (encodeBreath tail).tacts) = some (.pulse tail)
      exact decodeTacts_encode (.pulse tail)

theorem decodeTacts_complete {run : List VeyraTact} {value : Recurrence}
    (decoded : decodeTacts run = some value) : run = (encodeBreath value).tacts := by
  induction run generalizing value with
  | nil =>
      simp [decodeTacts] at decoded
      subst value
      rfl
  | cons head tail hypothesis =>
      by_cases canonical : head = successorTact
      · subst head
        cases value with
        | silence => simp [decodeTacts] at decoded
        | pulse valueTail =>
            simp [decodeTacts] at decoded
            exact congrArg (successorTact :: ·) (hypothesis decoded)
      · simp [decodeTacts, canonical] at decoded

theorem THM_R9_003_encode_decode (native : VeyraMode) (value : Recurrence)
    (decoded : decodeMode native = some value) : encodeMode value = native := by
  cases native with
  | mk breath observer =>
      cases breath with
      | mk run anchor =>
          by_cases nativeObserver : observer = "native-cycle"
          · subst observer
            cases run with
            | nil =>
                cases anchor with
                | none => simp [decodeMode] at decoded
                | some point =>
                    by_cases canonical : point = originNode
                    · subst point
                      simp [decodeMode] at decoded
                      subst value
                      rfl
                    · simp [decodeMode, canonical] at decoded
            | cons head tail =>
                cases anchor with
                | some _ => simp [decodeMode] at decoded
                | none =>
                    have complete := decodeTacts_complete decoded
                    cases value with
                    | silence => simp [encodeBreath] at complete
                    | pulse valueTail =>
                        simp [encodeMode, encodeBreath]
                        injection complete with headSame tailSame
                        exact ⟨headSame.symm, tailSame.symm⟩
          · simp [decodeMode, nativeObserver] at decoded

theorem THM_R9_004_encode_injective (left right : Recurrence)
    (same : encodeMode left = encodeMode right) : left = right := by
  have decoded := congrArg decodeMode same
  simpa [THM_R9_002_decode_encode] using decoded

theorem canonicalTacts_encode (value : Recurrence) :
    canonicalTacts (encodeBreath value).tacts = true := by
  induction value with
  | silence => rfl
  | pulse tail hypothesis =>
      simpa only [encodeBreath, canonicalTacts, decide_true, Bool.true_and] using hypothesis

theorem canonicalMode_encode (value : Recurrence) :
    canonicalMode (encodeMode value) = true := by
  cases value with
  | silence => simp [canonicalMode, encodeMode, encodeBreath, originNode]
  | pulse tail => exact canonicalTacts_encode (.pulse tail)

theorem encode_silence_preserved : VeyraIntrinsicRuntime.zero = encodeMode .silence := by
  rfl

theorem encode_pulse_preserved (value : Recurrence) :
    VeyraIntrinsicRuntime.successor (encodeMode value) = .ready (encodeMode (.pulse value)) := by
  unfold VeyraIntrinsicRuntime.successor
  rw [if_pos (canonicalMode_encode value)]
  rfl

theorem contiguous_encoded (value : Recurrence) :
    contiguous (successorTact :: (encodeBreath value).tacts) = true := by
  induction value with
  | silence => rfl
  | pulse tail hypothesis =>
      simpa only [encodeBreath, contiguous, successorTact, originNode,
        decide_true, Bool.true_and] using hypothesis

theorem last_encoded (value : Recurrence) :
    (successorTact :: (encodeBreath value).tacts).getLastD successorTact = successorTact := by
  induction value with
  | silence => rfl
  | pulse tail hypothesis => simpa [encodeBreath] using hypothesis

theorem lastTail_encoded (value : Recurrence) :
    (encodeBreath value).tacts.getLastD successorTact = successorTact := by
  cases value with
  | silence => rfl
  | pulse tail => exact last_encoded tail

theorem valid_encodeBreath (value : Recurrence) :
    validBreath (encodeBreath value) = true := by
  cases value with
  | silence => rfl
  | pulse tail => exact contiguous_encoded tail

theorem boundary_encodeBreath (value : Recurrence) :
    breathBoundary (encodeBreath value) = some (originNode, originNode) := by
  cases value with
  | silence => rfl
  | pulse tail =>
      change some (successorTact.start,
        ((encodeBreath tail).tacts.getLastD successorTact).stop) =
        some (originNode, originNode)
      rw [lastTail_encoded]
      rfl

theorem encoded_ready (value : Recurrence) :
    evalModeBreath (encodeMode value).breath = .ready (encodeMode value) := by
  simp [encodeMode, evalModeBreath, valid_encodeBreath, boundary_encodeBreath]

theorem THM_R9_001_encode_mode_ready (value : Recurrence) :
    evalModeBreath (encodeMode value).breath = .ready (encodeMode value) :=
  encoded_ready value

theorem encodeTacts_stitch (left right : Recurrence) :
    (encodeBreath (Veyra.stitch left right)).tacts =
      (encodeBreath left).tacts ++ (encodeBreath right).tacts := by
  induction left with
  | silence => rfl
  | pulse tail hypothesis => simp [Veyra.stitch, encodeBreath, hypothesis]

theorem canonicalBreath_encode (value : Recurrence) :
    canonicalBreath (encodeBreath value).tacts = encodeBreath value := by
  cases value <;> rfl

theorem THM_R9_005_stitch_preserved (left right : Recurrence) :
    VeyraIntrinsicRuntime.stitch (encodeMode left) (encodeMode right) =
      .ready (encodeMode (Veyra.stitch left right)) := by
  have breathSame :
      canonicalBreath ((encodeBreath left).tacts ++ (encodeBreath right).tacts) =
        encodeBreath (Veyra.stitch left right) := by
    rw [← encodeTacts_stitch]
    exact canonicalBreath_encode _
  unfold VeyraIntrinsicRuntime.stitch
  rw [if_pos (by simp [canonicalMode_encode])]
  simp only [encodeMode]
  rw [breathSame]

theorem repeatTacts_encode (left right : Recurrence) :
    repeatTacts (encodeBreath left).tacts (encodeBreath right).tacts =
      (encodeBreath (Veyra.weave left right)).tacts := by
  induction right with
  | silence => rfl
  | pulse tail hypothesis =>
      simp [repeatTacts, encodeBreath, Veyra.weave, encodeTacts_stitch, hypothesis]

theorem THM_R9_006_weave_preserved (left right : Recurrence) :
    VeyraIntrinsicRuntime.weave (encodeMode left) (encodeMode right) =
      .ready (encodeMode (Veyra.weave left right)) := by
  have breathSame :
      canonicalBreath (repeatTacts (encodeBreath left).tacts (encodeBreath right).tacts) =
        encodeBreath (Veyra.weave left right) := by
    rw [repeatTacts_encode]
    exact canonicalBreath_encode _
  unfold VeyraIntrinsicRuntime.weave
  rw [if_pos (by simp [canonicalMode_encode])]
  simp only [encodeMode]
  rw [breathSame]

theorem THM_R9_007_resonance_transport (factor carrier : Recurrence) :
    resonates factor carrier ↔
      IntrinsicResonates (intrinsicMode factor) (intrinsicMode carrier) := by
  constructor
  · rintro ⟨witness, reconstruction⟩
    refine ⟨intrinsicMode witness, ?_⟩
    change VeyraIntrinsicRuntime.weave (encodeMode factor) (encodeMode witness) =
      .ready (encodeMode carrier)
    rw [THM_R9_006_weave_preserved, reconstruction]
  · rintro ⟨witness, reconstruction⟩
    rcases witness.property with ⟨witnessRecurrence, witnessEncoded⟩
    refine ⟨witnessRecurrence, ?_⟩
    change VeyraIntrinsicRuntime.weave (encodeMode factor) witness.1 =
      .ready (encodeMode carrier) at reconstruction
    rw [← witnessEncoded, THM_R9_006_weave_preserved] at reconstruction
    injection reconstruction with same
    exact THM_R9_004_encode_injective _ _ same

end VeyraTransport
