# VAM v2.6 — Compress-idempotent different-observer rejection law

**Status:** accepted fifth checked optimizer local law plus executable rejection witness  
**Boundary:** checked local rejection law and bounded executable witness only; not a whole-pass proof, not whole-optimizer correctness, not global semantic equivalence, not VAMD optimized emission, and not a speed claim.

## Purpose

v2.6 adds the first richer compression law after the initial four local laws. The new law covers the rejection side of `compress-idempotent`: if a nested compression uses a different observer than the prior compression, the local window is left unchanged.

This matters because optimizer evidence should cover both accepted rewrites and explicit guard failures. A rejected rewrite can be just as important as an accepted one: it proves that the optimizer keeps semantic boundaries visible when a local precondition is not met.

## Checked artifact

- Lean file: `proofs/lean/VeyraOptimizer.lean`
- Checked local-law symbol: `Veyra.compressIdempotent_differentObserver_reject_local_law`
- Local-law row: `compress-idempotent.different-observer-reject-local-law`
- Proof bridge boundary: `optimizer-proof-bridge`
- Claim string: `checked-local-laws-not-full-correctness`

The Lean theorem is a tiny local-window statement: a different-observer window is unchanged by the local compression step. It is not a theorem about arbitrary programs or all optimizer contexts.

## Executable witness

`vam/src/optimizer_prepost.py` now includes `compress-idempotent-different-observer-reject`:

```text
REZ %r1, "phase"
OBSERVER %r2, "kind"
OBSERVER %r3, "length"
COMPRESS %r4, %r1, %r2
COMPRESS %r5, %r4, %r3
ECHO %r6, %r4, %r5, %r2
```

The witness expects a rejected `compress-idempotent` decision and preserved equivalence:

```text
accepted = false
precondition_status = witnessed
postcondition_status = preserved
optimizer_detail = keep %r5: observer differs source=%r4 observer=%r3 prior=%r2
```

## Non-claims

v2.6 still does not claim optimizer correctness. It only adds one checked local rejection law and one executable witness row. All optimizer passes remain obligation-backed, and a future whole-optimizer theorem skeleton still needs explicit assumptions for pass order, data dependencies, obstruction preservation, observer semantics, and report equivalence.
