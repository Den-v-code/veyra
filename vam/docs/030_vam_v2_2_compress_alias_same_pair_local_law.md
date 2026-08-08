# VAM v2.2 — Compress-alias same-pair local law

**Status:** accepted third checked local law  
**Boundary:** checked local rewrite law only; not a whole-pass proof, not whole-optimizer correctness, not global semantic equivalence, not a speed claim.

## Purpose

v2.2 promotes the safest `compress-alias` obligation fragment into a checked local law. The local model covers two adjacent `COMPRESS` declarations with the same source register and observer register. In that tiny model, the second destination aliases to the first destination without changing lookup by source/observer pair.

This is narrower than the executable optimizer pass. The Python and Rust optimizers still rely on bounded witnesses, obligation rows, fixture parity, and obstruction-preservation guards for pass-level behavior.

## Checked artifact

- Lean file: `proofs/lean/VeyraOptimizer.lean`
- Bridge module: `vam/src/optimizer_proofs.py`
- Checked local-law symbol: `Veyra.compressAlias_samePair_local_law`
- Existing checked local laws kept:
  - `Veyra.observerAlias_lookup_invariant`
  - `Veyra.compressIdempotent_sameObserver_local_law`
- Check command: `elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraOptimizer.lean`

The Lean model should stay intentionally small: a local `CompressDecl` lookup model plus a same source/observer alias step. It is not a model of every program context or obstruction guard.

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
- `dead-shadow` to be checked only as `dead-shadow.unused-lookup-local-law`;
- all four optimizer passes to remain obligation-backed;
- v2.0/v2.1/v2.2/v2.3 docs and proof-bridge tests to exist.

## Non-claims

v2.2 does **not** claim:

- proof of the whole `compress-alias` pass;
- proof of the whole optimizer;
- global program equivalence;
- optimized VAMD frame emission;
- native speedup or GPU/FPGA readiness;
- replacement of the Python semantic oracle.

## Next pressure

1. connect the checked local laws to executable pre/postcondition witnesses;
2. keep future laws local before any pass-level theorem;
3. split `src/core/certify_vam.py` before the gate grows further;
4. only after enough local laws and witnesses exist, sketch a whole-optimizer theorem.
