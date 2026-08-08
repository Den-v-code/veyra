import VeyraProofSoundness
import VeyraRecurrenceModeBridge

/- Generic R10 semantics and structural support for any accepted R7 proof term. -/
namespace VeyraElaboration
open Veyra
open VeyraProof
open VeyraTransport

def ImageSemantics {arity : Nat} (env : Env arity) : Formula arity → Prop
  | .equal left right => intrinsicMode (eval env left) = intrinsicMode (eval env right)
  | .implies premise conclusion =>
      ImageSemantics env premise → ImageSemantics env conclusion
  | .forallE _ body => ∀ value, ImageSemantics (extendEnv env value) body
  | .resonates factor carrier =>
      IntrinsicResonates (intrinsicMode (eval env factor)) (intrinsicMode (eval env carrier))

theorem intrinsicMode_injective {left right : Recurrence}
    (same : intrinsicMode left = intrinsicMode right) : left = right := by
  apply THM_R9_004_encode_injective
  exact congrArg Subtype.val same

theorem intrinsicMode_eq_iff (left right : Recurrence) :
    intrinsicMode left = intrinsicMode right ↔ left = right := by
  constructor
  · exact intrinsicMode_injective
  · intro same
    cases same
    rfl

theorem THM_R10_001_image_semantics_equivalent {arity : Nat}
    (env : Env arity) (formula : Formula arity) :
    Semantics env formula ↔ ImageSemantics env formula := by
  induction formula with
  | equal left right => exact (intrinsicMode_eq_iff (eval env left) (eval env right)).symm
  | implies premise conclusion premiseHypothesis conclusionHypothesis =>
      simp only [Semantics, ImageSemantics]
      rw [← premiseHypothesis, ← conclusionHypothesis]
  | forallE binder body hypothesis =>
      simp only [Semantics, ImageSemantics]
      constructor
      · intro accepted value
        exact (hypothesis (extendEnv env value)).mp (accepted value)
      · intro accepted value
        exact (hypothesis (extendEnv env value)).mpr (accepted value)
  | resonates factor carrier =>
      exact THM_R9_007_resonance_transport (eval env factor) (eval env carrier)

theorem THM_R10_002_checked_elaboration_image_sound {arity : Nat}
    (env : Env arity) {context : Context arity} {proof : Proof arity}
    {goal : Formula arity} (holds : ContextHolds env context)
    (accepted : check context proof goal = true) : ImageSemantics env goal := by
  apply (THM_R10_001_image_semantics_equivalent env goal).mp
  exact THM_R7_001_check_sound env holds accepted

inductive DependencyCategory where
  | formation | definition | logical | domain | observer | obstruction
deriving Repr, DecidableEq, BEq, Hashable

inductive DependencyId where
  | recurrenceFormation | propositionFormation
  | silenceDefinition | pulseDefinition | stitchDefinition | weaveDefinition
  | equalDefinition | impliesDefinition | forallDefinition | resonatesDefinition
  | assumeRule | impIntroRule | impElimRule | forallIntroRule | forallElimRule
  | eqReflRule | eqSymRule | eqTransRule | resonanceIntroRule
  | stitchSilenceLeftLaw | stitchSilenceRightLaw | weaveSilenceRightLaw
  | weavePulseLaw | weaveUnitRightLaw
  | intrinsicModeObserver | foreignModeObstruction
deriving Repr, DecidableEq, BEq, Hashable

def dependencyCategory : DependencyId → DependencyCategory
  | .recurrenceFormation | .propositionFormation => .formation
  | .silenceDefinition | .pulseDefinition | .stitchDefinition | .weaveDefinition
  | .equalDefinition | .impliesDefinition | .forallDefinition | .resonatesDefinition =>
      .definition
  | .assumeRule | .impIntroRule | .impElimRule | .forallIntroRule
  | .forallElimRule | .eqReflRule | .eqSymRule | .eqTransRule
  | .resonanceIntroRule => .logical
  | .stitchSilenceLeftLaw | .stitchSilenceRightLaw | .weaveSilenceRightLaw
  | .weavePulseLaw | .weaveUnitRightLaw => .domain
  | .intrinsicModeObserver => .observer
  | .foreignModeObstruction => .obstruction

/- Mathlib is outside the TCB; an eraseDups list is the finite-set carrier. -/
abbrev DependencySupport := List DependencyId

def dependencies (items : List DependencyId) : DependencySupport :=
  items.eraseDups

def supportUnion (left right : DependencySupport) : DependencySupport :=
  (left ++ right).eraseDups

def supportInsert (dependency : DependencyId)
    (support : DependencySupport) : DependencySupport :=
  (dependency :: support).eraseDups

def termSupport {arity : Nat} : Term arity → DependencySupport
  | .var _ => dependencies [.recurrenceFormation]
  | .silence => dependencies [.recurrenceFormation, .silenceDefinition]
  | .pulse tail =>
      supportUnion (dependencies [.recurrenceFormation, .pulseDefinition]) (termSupport tail)
  | .stitch left right =>
      supportUnion
        (supportUnion (dependencies [.recurrenceFormation, .stitchDefinition])
          (termSupport left)) (termSupport right)
  | .weave left right =>
      supportUnion
        (supportUnion (dependencies [.recurrenceFormation, .weaveDefinition])
          (termSupport left)) (termSupport right)

def formulaSupport {arity : Nat} : Formula arity → DependencySupport
  | .equal left right =>
      supportUnion
        (supportUnion (dependencies [.propositionFormation, .equalDefinition])
          (termSupport left)) (termSupport right)
  | .implies premise conclusion =>
      supportUnion
        (supportUnion (dependencies [.propositionFormation, .impliesDefinition])
          (formulaSupport premise)) (formulaSupport conclusion)
  | .forallE _ body =>
      supportUnion (dependencies [.propositionFormation, .forallDefinition])
        (formulaSupport body)
  | .resonates factor carrier =>
      supportUnion
        (supportUnion (dependencies [.propositionFormation, .resonatesDefinition])
          (termSupport factor)) (termSupport carrier)

def nativeLawSupport : NativeLawId → DependencySupport
  | .stitchSilenceLeft => dependencies
      [.stitchSilenceLeftLaw, .stitchDefinition, .silenceDefinition]
  | .stitchSilenceRight => dependencies
      [.stitchSilenceRightLaw, .stitchDefinition, .silenceDefinition]
  | .weaveSilenceRight => dependencies
      [.weaveSilenceRightLaw, .weaveDefinition, .silenceDefinition]
  | .weavePulse => dependencies
      [.weavePulseLaw, .weaveDefinition, .pulseDefinition, .stitchDefinition]
  | .weaveUnitRight => dependencies
      [.weaveUnitRightLaw, .weaveDefinition, .pulseDefinition, .silenceDefinition]

def termListSupport {arity : Nat} (terms : List (Term arity)) : DependencySupport :=
  terms.foldl (fun support term => supportUnion support (termSupport term)) []

def proofSupport {arity : Nat} : Proof arity → DependencySupport
  | .hyp _ => dependencies [.assumeRule]
  | .impIntro premise body =>
      supportUnion
        (supportUnion (dependencies [.impIntroRule, .impliesDefinition,
          .propositionFormation]) (formulaSupport premise)) (proofSupport body)
  | .impElim function argument =>
      supportUnion (supportUnion (dependencies [.impElimRule])
        (proofSupport function)) (proofSupport argument)
  | .forallIntro _ body =>
      supportUnion (dependencies [.forallIntroRule, .forallDefinition,
        .propositionFormation, .recurrenceFormation]) (proofSupport body)
  | .forallElim universal argument =>
      supportUnion (supportUnion (dependencies [.forallElimRule])
        (proofSupport universal)) (termSupport argument)
  | .eqRefl term =>
      supportUnion (dependencies [.eqReflRule, .equalDefinition,
        .propositionFormation]) (termSupport term)
  | .eqSymm evidence =>
      supportUnion (dependencies [.eqSymRule]) (proofSupport evidence)
  | .eqTrans left right =>
      supportUnion (supportUnion (dependencies [.eqTransRule])
        (proofSupport left)) (proofSupport right)
  | .nativeLaw law arguments =>
      supportUnion (supportUnion (dependencies [.equalDefinition,
        .propositionFormation]) (nativeLawSupport law)) (termListSupport arguments)
  | .resonanceIntro factor carrier witness equality =>
      supportUnion (supportUnion (supportUnion (supportUnion
        (dependencies [.resonanceIntroRule, .resonatesDefinition,
          .propositionFormation]) (termSupport factor)) (termSupport carrier))
          (termSupport witness)) (proofSupport equality)

def imageCompositionSupport {arity : Nat} (proof : Proof arity) : DependencySupport :=
  supportInsert .intrinsicModeObserver (proofSupport proof)

def elaborationSupport {arity : Nat} (proof : Proof arity)
    (statement : Formula arity) : DependencySupport :=
  supportUnion (imageCompositionSupport proof) (formulaSupport statement)

end VeyraElaboration
