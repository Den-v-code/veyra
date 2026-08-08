# VAM v2.1 — Compress-idempotent same-observer local law

**Status:** accepted second checked local law  
**Boundary:** checked local rewrite law only; not a whole-pass proof, not whole-optimizer correctness, not global semantic equivalence, not a speed claim.

## Purpose

v2.1 promotes the safest `compress-idempotent` obligation fragment into a checked local law. The law models one adjacent same-observer window and proves that applying the local compression step twice reaches the same local window as applying it once.

This is intentionally narrower than the executable optimizer pass. The Python and Rust optimizers still rely on bounded witnesses, obligation rows, and fixture parity for pass-level behavior.

## Checked artifact

- Lean file: `proofs/lean/VeyraOptimizer.lean`
- Bridge module: `vam/src/optimizer_proofs.py`
- Checked local-law symbol: `Veyra.compressIdempotent_sameObserver_local_law`
- Previous local law kept: `Veyra.observerAlias_lookup_invariant`
- Check command: `elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraOptimizer.lean`

The Lean model adds `ObserverWindow` and `compressObserverWindow` to isolate one local same-observer rewrite. That local model is enough to check idempotence of the rewrite, but it is not a model of every program context.

## Bridge ledger

`optimizer_proof_rows()` now binds current optimizer obligations as follows:

1. `observer-alias` — `lean-checked-local-law` for `observer-alias.lookup-invariant`, pass remains obligation-backed.
2. `compress-alias` — `obligation-only`.
3. `compress-idempotent` — `lean-checked-local-law` for `compress-idempotent.same-observer-local-law`, pass remains obligation-backed.
4. `dead-shadow` — promoted in `031_vam_v2_3_dead_shadow_unused_lookup_local_law.md`.

v2.2 promotes `compress-alias.same-pair-local-law`; v2.3 promotes `dead-shadow.unused-lookup-local-law`; see docs `030` and `031`.

Static row fields remain:

```text
boundary = optimizer-proof-bridge
claim = checked-local-laws-not-full-correctness
```

## Certificate gate

`vam_reference_v1` now requires:

- both required Lean symbols to exist and Lean-check in `VeyraOptimizer.lean`;
- exactly two checked local laws in the optimizer proof summary;
- `compress-alias` and `dead-shadow` were still `obligation-only` in the v2.1 gate;
- all four optimizer passes to remain obligation-backed;
- v2.0/v2.1 docs and proof-bridge tests to exist.

## Non-claims

v2.1 does **not** claim:

- proof of the whole `compress-idempotent` pass;
- proof of the whole optimizer;
- global program equivalence;
- optimized VAMD frame emission;
- native speedup or GPU/FPGA readiness;
- replacement of the Python semantic oracle.

## Next pressure

1. connect checked local laws to executable pre/postcondition witnesses;
2. keep future laws local before any pass-level theorem;
3. split `src/core/certify_vam.py` before the gate grows further;
4. only after enough local laws and witnesses exist, sketch a whole-optimizer theorem.
