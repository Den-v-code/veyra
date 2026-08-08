# VAM v2.9 — Compress-idempotent visible-use observer law

**Status:** accepted seventh checked optimizer local law plus executable accepted witness  
**Boundary:** checked local visible-use law and bounded executable witness only; not a whole-pass proof, not whole-optimizer correctness, not global semantic equivalence, not VAMD optimized emission, and not a speed claim.

## Purpose

v2.9 adds a visible-use preservation row for `compress-idempotent`. When a same-observer nested compression candidate is rewritten to its source in a visible `OBSERVE` context, the observer register of that use must remain unchanged.

This is deliberately small. It does not prove the whole pass. It states one local fact needed by the future optimizer theorem skeleton: the accepted same-observer rewrite changes the observed value register, not the declared observer of the visible use.

## Checked artifact

- Lean file: `proofs/lean/VeyraOptimizer.lean`
- Checked local-law symbol: `Veyra.compressIdempotent_visibleUseObserver_local_law`
- Local-law row: `compress-idempotent.visible-use-observer-local-law`
- Proof bridge boundary: `optimizer-proof-bridge`
- Claim string: `checked-local-laws-not-full-correctness`

The Lean theorem is a tiny row over `VisibleUseDecl := Reg × Reg`: `rewriteVisibleUse` may replace the observed candidate register by the source register, but `visibleUseObserver` is preserved.

## Executable witness

`vam/src/optimizer_prepost.py` now includes `compress-idempotent-visible-observe-use`:

```text
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
OBSERVE %r5, %r4, %r2
ECHO %r6, %r5, %r5, %r2
CERT %r7, "visible-use", %r6, "same observer visible"
```

The witness expects an accepted `compress-idempotent` decision and preserved equivalence:

```text
accepted = true
precondition_status = witnessed
postcondition_status = preserved
optimizer_detail = %r4->%r3 prior_source=%r1 observer=%r2 reason=same-observer-visible
```

## Resulting bridge state

The optimizer proof bridge now has seven checked local laws:

1. `observer-alias.lookup-invariant`
2. `compress-alias.same-pair-local-law`
3. `compress-idempotent.same-observer-local-law`
4. `compress-idempotent.visible-use-observer-local-law`
5. `compress-idempotent.different-observer-reject-local-law`
6. `compress-idempotent.obstruction-boundary-reject-local-law`
7. `dead-shadow.unused-lookup-local-law`

The pre/post witness summary is now `total_rows=7`, `accepted_rows=5`, and `safe_equivalence_rows=7`.

## Non-claims

v2.9 still does not claim optimizer correctness. It adds one checked local visible-use law and one executable witness row. All optimizer passes remain obligation-backed; the future whole-optimizer theorem skeleton still needs explicit assumptions for pass order, data dependencies, obstruction preservation, observer semantics, visible-use rewriting, and report equivalence.
