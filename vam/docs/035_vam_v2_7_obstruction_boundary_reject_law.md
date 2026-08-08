# VAM v2.7 — Compress-idempotent obstruction-boundary rejection law

**Status:** accepted sixth checked optimizer local law plus executable rejection witness  
**Boundary:** checked local rejection law and bounded executable witness only; not a whole-pass proof, not whole-optimizer correctness, not global semantic equivalence, not VAMD optimized emission, and not a speed claim.

## Purpose

v2.7 adds the second rejection-side compression guard for `compress-idempotent`. If a same-observer nested compression candidate feeds `OBSTRUCT` evidence, the optimizer must keep that candidate visible rather than normalizing it away.

This closes an important semantic hole in the evidence map: rejected rows are not failure noise. They are how VAM records that obstruction evidence is first-class and must not be erased by local compression convenience.

## Checked artifact

- Lean file: `proofs/lean/VeyraOptimizer.lean`
- Checked local-law symbol: `Veyra.compressIdempotent_obstructionBoundary_reject_local_law`
- Local-law row: `compress-idempotent.obstruction-boundary-reject-local-law`
- Proof bridge boundary: `optimizer-proof-bridge`
- Claim string: `checked-local-laws-not-full-correctness`

The Lean theorem is a tiny local-window statement: a candidate with an obstruction-evidence boundary is left unchanged. It is not a theorem about arbitrary programs or a whole optimizer pass.

## Executable witness

`vam/src/optimizer_prepost.py` now includes `compress-idempotent-obstruction-boundary-reject`:

```text
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
OBSTRUCT %r5, %r4, "boundary"
```

The witness expects a rejected `compress-idempotent` decision and preserved equivalence:

```text
accepted = false
precondition_status = witnessed
postcondition_status = preserved
optimizer_detail = keep %r4: candidate feeds OBSTRUCT evidence boundary
```

## Resulting bridge state

v2.7 left the optimizer proof bridge with six checked local laws:

1. `observer-alias.lookup-invariant`
2. `compress-alias.same-pair-local-law`
3. `compress-idempotent.same-observer-local-law`
4. `compress-idempotent.different-observer-reject-local-law`
5. `compress-idempotent.obstruction-boundary-reject-local-law`
6. `dead-shadow.unused-lookup-local-law`

At v2.7 the pre/post witness summary was `total_rows=6`, `accepted_rows=4`, and `safe_equivalence_rows=6`; v2.9 supersedes this with the visible-use observer row documented in `036_vam_v2_9_visible_use_observer_law.md`.

## Non-claims

v2.7 still does not claim optimizer correctness. It adds one checked local rejection law and one executable witness row. All optimizer passes remain obligation-backed; the future whole-optimizer theorem skeleton still needs explicit assumptions for pass order, data dependencies, obstruction preservation, observer semantics, and report equivalence.
