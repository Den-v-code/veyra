# VAM v2.0 — Optimizer proof semantics first slice

**Status:** accepted first checked slice  
**Boundary:** observer-alias only; not full optimizer correctness, not global semantic equivalence, not a speed claim.

## Purpose

v2.0 turns one local law under a v1.9 optimizer obligation into a checked artifact. The selected slice is the safest local law: when two adjacent observer declarations have the same string observer kind, keeping the first declaration preserves lookup results by observer kind. This is narrower than the whole optimizer pass.

## Checked artifact

- Lean file: `proofs/lean/VeyraOptimizer.lean`
- Bridge module: `vam/src/optimizer_proofs.py`
- Checked local-law symbol: `Veyra.observerAlias_lookup_invariant`
- Check command: `elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraOptimizer.lean`

The Lean file defines a small `lookupObserver` model and proves that the adjacent duplicate observer-kind rewrite preserves lookup results for every queried kind.

## Bridge ledger

`optimizer_proof_rows()` binds all current optimizer obligation rows to a proof status:

1. `observer-alias` — `lean-checked-local-law` for `observer-alias.lookup-invariant`, pass remains obligation-backed
2. `compress-alias` — `obligation-only`
3. `compress-idempotent` — promoted in `029_vam_v2_1_compress_idempotent_same_observer_local_law.md`
4. `dead-shadow` — promoted in `031_vam_v2_3_dead_shadow_unused_lookup_local_law.md`

Static row fields keep the contract explicit:

```text
boundary = optimizer-proof-bridge
claim = checked-local-laws-not-full-correctness
```

## Certificate gate

`vam_reference_v1` now requires:

- the proof bridge rows to keep the boundary/claim fields;
- exactly `observer-alias.lookup-invariant` to be marked as the checked local law;
- all current optimizer passes to remain obligation-backed;
- `proofs/lean/VeyraOptimizer.lean` to pass Lean;
- the v2.0 tests and documentation gates to exist.

## Non-claims

v2.0 does **not** claim:

- proof of the whole optimizer or whole observer-alias pass;
- proof-grade equivalence for `COMPRESS` or dead-shadow pruning;
- exhaustive program coverage;
- optimized VAMD frame emission;
- native speedup;
- replacement of the Python semantic oracle.

## Next pressure

v2.1 promotes `compress-idempotent.same-observer-local-law`; v2.2 promotes `compress-alias.same-pair-local-law`; v2.3 promotes `dead-shadow.unused-lookup-local-law`; see docs `029`-`031`.

Remaining pressure:

1. connect checked local laws to executable pre/postcondition witnesses;
2. split `certify_vam.py` before more gate growth;
3. keep future laws local before any pass-level theorem;
4. only then discuss a whole-optimizer theorem.
