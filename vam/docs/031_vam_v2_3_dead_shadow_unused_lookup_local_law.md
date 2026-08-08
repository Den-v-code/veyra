# VAM v2.3 — Dead-shadow unused-lookup local law

**Status:** accepted fourth checked local law  
**Boundary:** checked local lookup/drop law only; not a whole-pass proof, not whole-optimizer correctness, not global semantic equivalence, not VAMD emission, not a speed claim.

## Purpose

v2.3 promotes the smallest `dead-shadow` obligation fragment into a checked local law. The local model covers dropping one shadow declaration whose destination is known not to be the later lookup query. In that tiny lookup model, removing the unused declaration preserves lookup for the queried destination.

This is narrower than executable dead-shadow pruning. The Python and Rust optimizers still rely on bounded witnesses, obligation rows, fixture parity, single-definition guards, nested-obstruction checks, and obstruction-preservation rejects for pass-level behavior.

## Checked artifact

- Lean file: `proofs/lean/VeyraOptimizer.lean`
- Bridge module: `vam/src/optimizer_proofs.py`
- Checked local-law symbol: `Veyra.deadShadow_unusedLookup_local_law`
- Local-law row: `dead-shadow.unused-lookup-local-law`
- Existing checked local laws kept:
  - `Veyra.observerAlias_lookup_invariant`
  - `Veyra.compressIdempotent_sameObserver_local_law`
  - `Veyra.compressAlias_samePair_local_law`
- Check command: `elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraOptimizer.lean`

The Lean model should stay intentionally small: a local `ShadowDecl` lookup model plus one `deadShadowDrop` step. It is not a model of every program context, liveness proof, or obstruction guard.

## Bridge ledger

`optimizer_proof_rows()` now binds current optimizer obligations as follows:

1. `observer-alias` — `lean-checked-local-law` for `observer-alias.lookup-invariant`, pass remains obligation-backed.
2. `compress-alias` — `lean-checked-local-law` for `compress-alias.same-pair-local-law`, pass remains obligation-backed.
3. `compress-idempotent` — `lean-checked-local-law` for `compress-idempotent.same-observer-local-law`, pass remains obligation-backed.
4. `dead-shadow` — `lean-checked-local-law` for `dead-shadow.unused-lookup-local-law`, pass remains obligation-backed.

Static row fields remain:

```text
boundary = optimizer-proof-bridge
claim = checked-local-laws-not-full-correctness
```

## Certificate gate

`vam_reference_v1` should require:

- all five required Lean symbols to exist and Lean-check in `VeyraOptimizer.lean`;
- currently seven checked local laws in the optimizer proof summary;
- all four optimizer passes to remain obligation-backed;
- v2.0/v2.1/v2.2/v2.3 docs and proof-bridge tests to exist.

## Non-claims

v2.3 does **not** claim:

- proof of the whole `dead-shadow` pass;
- proof of the whole optimizer;
- global program equivalence;
- optimized VAMD frame emission;
- native speedup or GPU/FPGA readiness;
- replacement of the Python semantic oracle.

## Next pressure

1. v2.4-v2.9 connect the checked local laws to executable pre/postcondition witness rows;
2. split near-cap certificate/proof modules before the gate grows further;
3. add richer compression laws only as checked local laws plus witnesses first;
4. only after enough local laws and witnesses exist, sketch a whole-optimizer theorem skeleton.
