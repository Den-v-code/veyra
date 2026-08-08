# 007 — Core Theorem Lowering Plan

## Scope

Lower Core theorem objects, quantifiers, and proof obligations into VAM without claiming proof strength that VAM has not checked. The lowering layer is a transport and obligation generator, not a theorem prover.

## Goals

- Preserve Core theorem identity, assumptions, conclusions, binders, and source locations.
- Emit VAM objects that are explicit about what is asserted, assumed, deferred, or merely annotated.
- Convert implicit proof requirements into named VAM obligations.
- Keep no-overclaim boundaries machine-visible in the lowered representation.
- Support round-trip diagnostics from VAM obligations back to Core spans.

## Non-Goals

- Do not certify the theorem during lowering.
- Do not simplify away assumptions unless Core has already justified the rewrite.
- Do not infer stronger quantifier domains than Core encodes.
- Do not treat missing proof terms as accepted proofs.
- Do not collapse warnings into success states.

## Inputs

Expected Core theorem shape:

- Stable theorem id and optional human name.
- Context: universe parameters, type variables, term variables, hypotheses.
- Quantifier tree: universal, existential, bounded, implicit, and instance binders.
- Claim body: proposition or predicate expression.
- Proof payload: complete proof, partial proof, external reference, sketch, or absent proof.
- Metadata: source span, trust level, imports, tags, and no-overclaim notes.

## VAM Output Shape

Each lowered theorem should produce:

```text
vam.theorem {
  id,
  source,
  binders,
  assumptions,
  claim,
  proof_status,
  obligations,
  trust_boundary,
  diagnostics
}
```

Where `proof_status` is one of:

- `verified`: Core supplied a proof accepted by the configured checker.
- `imported`: accepted only under an explicit named external trust boundary.
- `partial`: some proof steps or obligations remain open.
- `conjectural`: claim recorded, no proof accepted.
- `invalid`: lowering found a contradiction, malformed object, or forbidden overclaim.

## Lowering Steps

1. **Normalize identity**
   - Assign deterministic VAM theorem id from Core id plus module path.
   - Preserve original Core id as metadata.
   - Reject duplicate ids unless explicitly versioned.

2. **Lower context**
   - Convert Core universe/type parameters into VAM binder declarations.
   - Preserve binder order and dependency edges.
   - Mark implicit binders as implicit; do not materialize them as user claims.

3. **Lower quantifiers**
   - Map universal quantifiers to VAM `forall` binders.
   - Map existential quantifiers to VAM `exists` binders plus witness obligations when proofs require witnesses.
   - Map bounded quantifiers to domain binder plus membership/range assumption.
   - Preserve vacuity warnings when a domain may be empty.

4. **Lower assumptions**
   - Emit each hypothesis as a named VAM assumption.
   - Preserve whether it is local, imported, axiomatic, or generated.
   - Attach source spans and dependency links.

5. **Lower claim body**
   - Translate Core expressions structurally.
   - If a symbol has no VAM equivalent, emit an opaque symbol with an obligation to resolve semantics.
   - Never replace opaque symbols with approximate semantics without a warning.

6. **Lower proof payload**
   - Complete Core proof: emit proof reference and checker provenance.
   - Partial proof: emit known steps and open obligations.
   - External reference: emit `imported` status with trust boundary id.
   - Sketch or absent proof: emit `conjectural` or `partial`, not `verified`.

7. **Generate obligations**
   - Type/well-formedness obligations for binders, assumptions, and claim.
   - Domain non-emptiness obligations when required by downstream interpretation.
   - Witness obligations for existential claims lacking explicit witnesses.
   - Discharge obligations for each unproven assumption dependency.
   - Semantic-resolution obligations for opaque or external symbols.
   - Trust-boundary obligations for imported axioms, libraries, or checker results.

8. **Apply no-overclaim policy**
   - If any required obligation is open, theorem cannot lower as `verified`.
   - If trust boundary is external, theorem cannot be described as internally proved.
   - If proof is absent, output must be `conjectural` unless Core marks it explicitly false/invalid.
   - Diagnostics must distinguish “recorded claim” from “proved theorem”.

9. **Emit diagnostics**
   - Include source span for every generated obligation.
   - Include severity: info, warning, error, invalid.
   - Include suggested next action where possible.

## Obligation Categories

- `wf.type`: type or universe well-formedness.
- `wf.term`: term expression well-formedness.
- `wf.quantifier`: binder dependency and domain validity.
- `proof.missing`: missing proof term or proof step.
- `proof.external`: reliance on external checker/library/axiom.
- `semantics.opaque`: unresolved symbol or translation gap.
- `domain.nonempty`: required non-empty domain not established.
- `exists.witness`: existential witness not supplied or not checked.
- `boundary.no_overclaim`: status would overstate evidence.

## No-Overclaim Invariants

- `verified` implies zero open proof-critical obligations.
- `verified` implies checker provenance is present.
- `imported` implies trust boundary id is present.
- `conjectural` must not be rendered as theorem in user-facing summaries without qualifier.
- Opaque semantics must remain visible in both VAM data and diagnostics.
- Lowering warnings must survive serialization.

## Suggested Implementation Order

1. Define VAM theorem schema and proof status enum.
2. Implement structural lowering for ids, context, assumptions, and claim body.
3. Add quantifier lowering with bounded-domain handling.
4. Add obligation builder with stable obligation ids.
5. Add proof payload lowering and status calculation.
6. Add no-overclaim validator as a final pass.
7. Add golden fixtures for verified, imported, partial, conjectural, and invalid examples.

## Minimal Acceptance Checks

- A theorem with no proof lowers to `conjectural`, not `verified`.
- A theorem with external proof lowers to `imported` and names the trust boundary.
- A theorem with unresolved symbols carries `semantics.opaque` obligations.
- A bounded quantifier preserves its bound as an assumption or domain constraint.
- Diagnostics can point back to Core source spans.
- Serialization preserves proof status, obligations, and no-overclaim notes.
