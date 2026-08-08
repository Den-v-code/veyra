import VeyraProofKernel

/- Soundness of every inference/checker rule in the supported R7 calculus. -/
namespace VeyraProof
open Veyra

theorem infer_sound {arity : Nat} (env : Env arity) {context : Context arity}
    {proof : Proof arity} {goal : Formula arity} (holds : ContextHolds env context)
    (concluded : infer context proof = some goal) : Semantics env goal := by
  induction proof with
  | hyp index => exact contextHolds_lookup holds concluded
  | impIntro premise body hypothesis =>
      cases childResult : infer (premise :: context) body with
      | none => simp [infer, childResult] at concluded
      | some childGoal =>
          simp [infer, childResult] at concluded
          subst goal
          intro premiseHolds
          exact hypothesis env (context := premise :: context) (goal := childGoal)
            ⟨premiseHolds, holds⟩ childResult
  | impElim function argument functionHypothesis argumentHypothesis =>
      cases functionResult : infer context function with
      | none => simp [infer, functionResult] at concluded
      | some functionGoal =>
          cases functionGoal with
          | equal => simp [infer, functionResult] at concluded
          | forallE => simp [infer, functionResult] at concluded
          | resonates => simp [infer, functionResult] at concluded
          | implies premise conclusion =>
              cases argumentResult : infer context argument with
              | none => simp [infer, functionResult, argumentResult] at concluded
              | some actual =>
                  by_cases same : actual = premise
                  · simp [infer, functionResult, argumentResult, same] at concluded
                    subst goal
                    subst actual
                    exact (functionHypothesis env holds functionResult)
                      (argumentHypothesis env holds argumentResult)
                  · simp [infer, functionResult, argumentResult, same] at concluded
  | forallIntro binder body hypothesis =>
      cases childResult : infer (liftContext context) body with
      | none => simp [infer, childResult] at concluded
      | some childGoal =>
          simp [infer, childResult] at concluded
          subst goal
          intro value
          exact hypothesis (extendEnv env value) (context := liftContext context)
            (goal := childGoal) (contextHolds_lift env value context holds) childResult
  | forallElim universal term hypothesis =>
      cases universalResult : infer context universal with
      | none => simp [infer, universalResult] at concluded
      | some universalGoal =>
          cases universalGoal with
          | equal => simp [infer, universalResult] at concluded
          | implies => simp [infer, universalResult] at concluded
          | resonates => simp [infer, universalResult] at concluded
          | forallE binder body =>
              simp [infer, universalResult] at concluded
              subst goal
              apply (semantics_subst env (Fin.cases term (fun index => Term.var index)) body).2
              have environments : mapEnv env (Fin.cases term (fun index => Term.var index)) =
                  extendEnv env (eval env term) := by
                funext index; refine Fin.cases ?_ (fun _ => ?_) index <;> rfl
              rw [environments]
              exact hypothesis env holds universalResult (eval env term)
  | eqRefl term => simp [infer] at concluded; subst goal; rfl
  | eqSymm evidence hypothesis =>
      cases evidenceResult : infer context evidence with
      | none => simp [infer, evidenceResult] at concluded
      | some evidenceGoal =>
          cases evidenceGoal <;> simp [infer, evidenceResult] at concluded
          case equal left right => subst goal; exact (hypothesis env holds evidenceResult).symm
  | eqTrans first second firstHypothesis secondHypothesis =>
      cases firstResult : infer context first with
      | none => simp [infer, firstResult] at concluded
      | some firstGoal =>
          cases firstGoal <;> simp [infer, firstResult] at concluded
          case equal left middle =>
            cases secondResult : infer context second with
            | none => simp [secondResult] at concluded
            | some secondGoal =>
                cases secondGoal <;> simp [secondResult] at concluded
                case equal actual right =>
                  by_cases same : actual = middle
                  · simp [same] at concluded
                    subst goal; subst actual
                    exact Eq.trans (firstHypothesis env holds firstResult)
                      (secondHypothesis env holds secondResult)
                  · simp [same] at concluded
  | nativeLaw law arguments => exact nativeConclusion_sound env law arguments goal concluded
  | resonanceIntro factor carrier witness equality hypothesis =>
      cases equalityResult : infer context equality with
      | none => simp [infer, equalityResult] at concluded
      | some equalityGoal =>
          by_cases same : equalityGoal = .equal (.weave factor witness) carrier
          · simp [infer, equalityResult, same] at concluded
            subst goal; subst equalityGoal
            exact ⟨eval env witness, hypothesis env holds equalityResult⟩
          · simp [infer, equalityResult, same] at concluded

theorem THM_R7_001_check_sound {arity : Nat} (env : Env arity)
    {context : Context arity} {proof : Proof arity} {goal : Formula arity}
    (holds : ContextHolds env context) (accepted : check context proof goal = true) :
    Semantics env goal := by
  exact infer_sound env holds (of_decide_eq_true accepted)

end VeyraProof
