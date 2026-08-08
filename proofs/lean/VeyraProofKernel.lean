import VeyraNativeArithmetic
/- R7 de-Bruijn proof calculus over the canonical native recurrence semantics. -/
namespace VeyraProof
open Veyra
inductive CoreType where | recurrence
deriving Repr, DecidableEq
inductive Term (arity : Nat) where
  | var : Fin arity → Term arity
  | silence : Term arity
  | pulse : Term arity → Term arity
  | stitch : Term arity → Term arity → Term arity
  | weave : Term arity → Term arity → Term arity
deriving Repr, DecidableEq
abbrev Env (arity : Nat) := Fin arity → Recurrence
def eval {arity : Nat} (env : Env arity) : Term arity → Recurrence
  | .var index => env index
  | .silence => .silence
  | .pulse tail => .pulse (eval env tail)
  | .stitch left right => stitch (eval env left) (eval env right)
  | .weave left right => weave (eval env left) (eval env right)
inductive Formula : Nat → Type where
  | equal {arity : Nat} : Term arity → Term arity → Formula arity
  | implies {arity : Nat} : Formula arity → Formula arity → Formula arity
  | forallE {arity : Nat} : CoreType → Formula (arity + 1) → Formula arity
  | resonates {arity : Nat} : Term arity → Term arity → Formula arity
deriving Repr, DecidableEq
def extendEnv {arity : Nat} (env : Env arity) (value : Recurrence) : Env (arity + 1) :=
  Fin.cases value env
def Semantics {arity : Nat} (env : Env arity) : Formula arity → Prop
  | .equal left right => eval env left = eval env right
  | .implies premise conclusion => Semantics env premise → Semantics env conclusion
  | .forallE _ body => ∀ value, Semantics (extendEnv env value) body
  | .resonates factor carrier => Veyra.resonates (eval env factor) (eval env carrier)
abbrev Subst (source target : Nat) := Fin source → Term target
def substTerm {source target : Nat} (substitution : Subst source target) :
    Term source → Term target
  | .var index => substitution index
  | .silence => .silence
  | .pulse tail => .pulse (substTerm substitution tail)
  | .stitch left right => .stitch (substTerm substitution left) (substTerm substitution right)
  | .weave left right => .weave (substTerm substitution left) (substTerm substitution right)
def weakenTerm {arity : Nat} (term : Term arity) : Term (arity + 1) :=
  substTerm (fun index => .var index.succ) term
def liftSubst {source target : Nat} (substitution : Subst source target) :
    Subst (source + 1) (target + 1) :=
  Fin.cases (.var 0) (fun index => weakenTerm (substitution index))
def substFormula {source target : Nat} (substitution : Subst source target) :
    Formula source → Formula target
  | .equal left right => .equal (substTerm substitution left) (substTerm substitution right)
  | .implies premise conclusion =>
      .implies (substFormula substitution premise) (substFormula substitution conclusion)
  | .forallE binder body => .forallE binder (substFormula (liftSubst substitution) body)
  | .resonates factor carrier =>
      .resonates (substTerm substitution factor) (substTerm substitution carrier)
def weakenFormula {arity : Nat} (formula : Formula arity) : Formula (arity + 1) :=
  substFormula (fun index => .var index.succ) formula
def instantiate {arity : Nat} (replacement : Term arity)
    (body : Formula (arity + 1)) : Formula arity :=
  substFormula (Fin.cases replacement (fun index => .var index)) body
def mapEnv {source target : Nat} (env : Env target)
    (substitution : Subst source target) : Env source :=
  fun index => eval env (substitution index)
theorem eval_subst {source target : Nat} (env : Env target)
    (substitution : Subst source target) (term : Term source) :
    eval env (substTerm substitution term) = eval (mapEnv env substitution) term := by
  induction term with
  | var => rfl
  | silence => rfl
  | pulse tail hypothesis => simp [substTerm, eval, hypothesis]
  | stitch left right leftHypothesis rightHypothesis =>
      simp [substTerm, eval, leftHypothesis, rightHypothesis]
  | weave left right leftHypothesis rightHypothesis =>
      simp [substTerm, eval, leftHypothesis, rightHypothesis]
theorem eval_weaken {arity : Nat} (env : Env arity) (value : Recurrence)
    (term : Term arity) : eval (extendEnv env value) (weakenTerm term) = eval env term := by
  rw [weakenTerm, eval_subst]
  congr 1
theorem mapEnv_liftSubst {source target : Nat} (env : Env target)
    (value : Recurrence) (substitution : Subst source target) :
    mapEnv (extendEnv env value) (liftSubst substitution) =
      extendEnv (mapEnv env substitution) value := by
  funext index
  refine Fin.cases ?_ (fun tail => ?_) index
  · rfl
  · simp [mapEnv, liftSubst, extendEnv, eval_weaken]
theorem semantics_subst {source target : Nat} (env : Env target)
    (substitution : Subst source target) (formula : Formula source) :
    Semantics env (substFormula substitution formula) ↔
      Semantics (mapEnv env substitution) formula := by
  induction formula generalizing target with
  | equal left right => simp [Semantics, substFormula, eval_subst]
  | implies premise conclusion premiseHypothesis conclusionHypothesis =>
      simp [Semantics, substFormula, premiseHypothesis, conclusionHypothesis]
  | resonates factor carrier => simp [Semantics, substFormula, eval_subst]
  | forallE binder body hypothesis =>
      simp only [Semantics, substFormula]
      constructor <;> intro accepted value
      · have row := accepted value
        rw [hypothesis, mapEnv_liftSubst] at row
        exact row
      · rw [hypothesis, mapEnv_liftSubst]
        exact accepted value
abbrev Context (arity : Nat) := List (Formula arity)
def ContextHolds {arity : Nat} (env : Env arity) : Context arity → Prop
  | [] => True
  | formula :: rest => Semantics env formula ∧ ContextHolds env rest
def liftContext {arity : Nat} (context : Context arity) : Context (arity + 1) :=
  context.map weakenFormula
theorem contextHolds_lift {arity : Nat} (env : Env arity) (value : Recurrence)
    (context : Context arity) (holds : ContextHolds env context) :
    ContextHolds (extendEnv env value) (liftContext context) := by
  induction context with
  | nil => trivial
  | cons formula rest hypothesis =>
      change Semantics env formula ∧ ContextHolds env rest at holds
      exact ⟨(semantics_subst (extendEnv env value)
        (fun index => Term.var index.succ) formula).2 holds.1, hypothesis holds.2⟩
def lookupFormula {arity : Nat} : Context arity → Nat → Option (Formula arity)
  | [], _ => none
  | formula :: _, 0 => some formula
  | _ :: rest, index + 1 => lookupFormula rest index
theorem contextHolds_lookup {arity : Nat} {env : Env arity} {context : Context arity}
    {index : Nat} {formula : Formula arity} (holds : ContextHolds env context)
    (found : lookupFormula context index = some formula) : Semantics env formula := by
  induction context generalizing index with
  | nil => simp [lookupFormula] at found
  | cons head tail hypothesis =>
      change Semantics env head ∧ ContextHolds env tail at holds
      cases index with
      | zero => simp [lookupFormula] at found; subst formula; exact holds.1
      | succ index => exact hypothesis holds.2 found
inductive NativeLawId where
  | stitchSilenceLeft | stitchSilenceRight | weaveSilenceRight | weavePulse | weaveUnitRight
deriving Repr, DecidableEq
inductive Proof : Nat → Type where
  | hyp {arity : Nat} : Nat → Proof arity
  | impIntro {arity : Nat} : Formula arity → Proof arity → Proof arity
  | impElim {arity : Nat} : Proof arity → Proof arity → Proof arity
  | forallIntro {arity : Nat} : CoreType → Proof (arity + 1) → Proof arity
  | forallElim {arity : Nat} : Proof arity → Term arity → Proof arity
  | eqRefl {arity : Nat} : Term arity → Proof arity
  | eqSymm {arity : Nat} : Proof arity → Proof arity
  | eqTrans {arity : Nat} : Proof arity → Proof arity → Proof arity
  | nativeLaw {arity : Nat} : NativeLawId → List (Term arity) → Proof arity
  | resonanceIntro {arity : Nat} : Term arity → Term arity → Term arity → Proof arity → Proof arity
deriving Repr, DecidableEq
def nativeConclusion {arity : Nat} : NativeLawId → List (Term arity) → Option (Formula arity)
  | .stitchSilenceLeft, [term] => some (.equal (.stitch .silence term) term)
  | .stitchSilenceRight, [term] => some (.equal (.stitch term .silence) term)
  | .weaveSilenceRight, [term] => some (.equal (.weave term .silence) .silence)
  | .weavePulse, [left, tail] => some (.equal (.weave left (.pulse tail)) (.stitch left (.weave left tail)))
  | .weaveUnitRight, [term] => some (.equal (.weave term (.pulse .silence)) term)
  | _, _ => none
def infer {arity : Nat} (context : Context arity) : Proof arity → Option (Formula arity)
  | .hyp index => lookupFormula context index
  | .impIntro premise body => (infer (premise :: context) body).map (.implies premise)
  | .impElim function argument => do
      let .implies premise conclusion ← infer context function | none
      let actual ← infer context argument
      if actual = premise then some conclusion else none
  | .forallIntro binder body => (infer (liftContext context) body).map (.forallE binder)
  | .forallElim universal term => do
      let .forallE _ body ← infer context universal | none
      some (instantiate term body)
  | .eqRefl term => some (.equal term term)
  | .eqSymm evidence => do
      let .equal left right ← infer context evidence | none
      some (.equal right left)
  | .eqTrans first second => do
      let .equal left middle ← infer context first | none
      let .equal actual right ← infer context second | none
      if actual = middle then some (.equal left right) else none
  | .nativeLaw law arguments => nativeConclusion law arguments
  | .resonanceIntro factor carrier witness equality => do
      let actual ← infer context equality
      if actual = .equal (.weave factor witness) carrier then some (.resonates factor carrier) else none
def check {arity : Nat} (context : Context arity) (proof : Proof arity)
    (goal : Formula arity) : Bool := decide (infer context proof = some goal)
theorem nativeConclusion_sound {arity : Nat} (env : Env arity)
    (law : NativeLawId) (arguments : List (Term arity)) (goal : Formula arity)
    (concluded : nativeConclusion law arguments = some goal) : Semantics env goal := by
  cases law <;> cases arguments with
  | nil => simp [nativeConclusion] at concluded
  | cons first rest =>
      cases rest with
      | nil =>
          simp [nativeConclusion] at concluded
          all_goals subst goal
          all_goals simp [Semantics, eval, stitch_silence_left, stitch_silence_right,
              weave_silence_right, weave_single_pulse_right]
      | cons second rest =>
          cases rest with
          | nil =>
              simp [nativeConclusion] at concluded
              all_goals subst goal
              all_goals simp [Semantics, eval, weave_pulse_recursion]
          | cons => simp [nativeConclusion] at concluded
end VeyraProof
