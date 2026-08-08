namespace Veyra

/-- A recurrence is either silent or one native pulse followed by another recurrence. -/
inductive Recurrence where
  | silence : Recurrence
  | pulse : Recurrence → Recurrence
  deriving Repr, DecidableEq

/-- Stitch places the pulses of the first recurrence before the second recurrence. -/
def stitch : Recurrence → Recurrence → Recurrence
  | Recurrence.silence, right => right
  | Recurrence.pulse tail, right => Recurrence.pulse (stitch tail right)

/-- Weave repeats the first recurrence along the complete structure of the second. -/
def weave (left : Recurrence) : Recurrence → Recurrence
  | Recurrence.silence => Recurrence.silence
  | Recurrence.pulse tail => stitch left (weave left tail)

/-- Resonance is witnessed by a recurrence whose weave reconstructs the carrier. -/
def resonates (factor carrier : Recurrence) : Prop :=
  ∃ witness : Recurrence, weave factor witness = carrier

theorem stitch_silence_left (value : Recurrence) :
    stitch Recurrence.silence value = value := by
  rfl

theorem stitch_silence_right (value : Recurrence) :
    stitch value Recurrence.silence = value := by
  induction value with
  | silence => rfl
  | pulse tail hypothesis =>
      simp [stitch, hypothesis]

theorem stitch_pulse_recursion (left right : Recurrence) :
    stitch (Recurrence.pulse left) right = Recurrence.pulse (stitch left right) := by
  rfl

theorem stitch_associative (first second third : Recurrence) :
    stitch (stitch first second) third = stitch first (stitch second third) := by
  induction first with
  | silence => rfl
  | pulse tail hypothesis =>
      simp [stitch, hypothesis]

theorem weave_silence_right (value : Recurrence) :
    weave value Recurrence.silence = Recurrence.silence := by
  rfl

theorem weave_pulse_recursion (left right : Recurrence) :
    weave left (Recurrence.pulse right) = stitch left (weave left right) := by
  rfl

theorem weave_single_pulse_right (value : Recurrence) :
    weave value (Recurrence.pulse Recurrence.silence) = value := by
  simp [weave, stitch_silence_right]

theorem every_recurrence_resonates_with_single_pulse (value : Recurrence) :
    resonates (Recurrence.pulse Recurrence.silence) value := by
  refine ⟨value, ?_⟩
  induction value with
  | silence => rfl
  | pulse tail hypothesis =>
      simp [weave, stitch, hypothesis]

theorem THM_R3_001_stitch_associative (first second third : Recurrence) :
    stitch (stitch first second) third = stitch first (stitch second third) :=
  stitch_associative first second third

theorem THM_R3_002_single_pulse_resonance (value : Recurrence) :
    resonates (Recurrence.pulse Recurrence.silence) value :=
  every_recurrence_resonates_with_single_pulse value

end Veyra
