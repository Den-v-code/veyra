# VAM v1.9 — Optimizer proof-obligation ledger

**Status:** accepted first slice  
**Boundary:** obligation inventory only; not proof-grade optimizer correctness, not global semantic equivalence, not a speed claim.

## Purpose

v1.9 names the obligations that the current conservative optimizer already relies on. The new ledger is a map of required guards and invariants for each optimizer pass, so future rewrites can be reviewed against explicit rows instead of implicit comments.

The ledger is implemented in `vam/src/optimizer_obligations.py` and is included inside `optimizer_witness_ledger()` under `optimizer_obligation_ledger`.

## Ledger contract

Static rows use:

```text
boundary = proof-obligation-ledger
claim = obligation-map-not-proof
```

Each row names:

- `pass_name`
- `obligation_id`
- `precondition`
- `postcondition`
- `invariant`
- boundary/claim fields

Coverage rows map concrete optimizer decisions from `optimize(program).rows` back onto those obligations, with `accepted-covered` or `rejected-covered` status.

## Current pass families

The first slice covers the current optimizer pass order:

1. `observer-alias`
2. `compress-alias`
3. `compress-idempotent`
4. `dead-shadow`

Rejected rows are first-class evidence. A rejection is not a failure of the ledger; it is the ledger showing that a guard blocked a rewrite.

## Certificate gate

`vam_reference_v1` now checks that:

- the witness ledger carries an `optimizer_obligation_ledger` section;
- all four current pass families are present;
- the ledger boundary and claim match the bounded non-proof contract;
- the obligation section has its own stable digest;
- the v1.9 implementation, tests, and documentation gate are present.

## Non-claims

v1.9 does **not** claim:

- formally verified optimizer correctness;
- a theorem of semantic equivalence;
- exhaustive coverage of all VAM programs;
- optimized VAMD frame emission;
- native speedup;
- replacement of the Python oracle.

## Next pressure

The honest next steps are:

1. split `certify_vam.py` before further gate growth;
2. see `028_vam_v2_0_optimizer_proof_semantics_first_slice.md`, `029_vam_v2_1_compress_idempotent_same_observer_local_law.md`, `030_vam_v2_2_compress_alias_same_pair_local_law.md`, and `031_vam_v2_3_dead_shadow_unused_lookup_local_law.md` plus `034_vam_v2_6_compress_idempotent_reject_law.md` and `035_vam_v2_7_obstruction_boundary_reject_law.md` plus `036_vam_v2_9_visible_use_observer_law.md` for the seven checked local laws;
3. turn more obligations into executable pre/postcondition checks;
4. only later, connect those checks into a whole-optimizer proof.
