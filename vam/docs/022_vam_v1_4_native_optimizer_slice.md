# VAM v1.4 — Native optimizer parity slice

**Status:** implemented as a bounded parity checkpoint.  
**Scope:** native Rust `observer-alias-v1` only, plus VAMD boundary/parity expansion and a speed-neutral harness.

## What changed

VAM v1.4 adds the first native optimizer pass to the Rust backend:

```text
VAM0 bytes -> Rust decoder -> Rust optimizer observer-alias-v1 -> Rust executor -> semantic report
```

The pass removes a duplicate `OBSERVER` row only when:

- the duplicate observer has the same declared kind;
- the destination register is defined exactly once;
- later uses are rewritten to the earlier observer register;
- the optimized program still matches the Python optimizer rows and canonical execution report.

The CLI surface is explicit:

```bash
source ~/.cargo/env
cargo run --manifest-path vam/native/Cargo.toml -- \
  --optimize observer-alias-v1 program.vam0
```

## Deliberate boundaries

- `observer-alias-v1` accepts `VAM0` only.
- `VAMD` optimizer input is rejected with `unsupported-profile`.
- This is not a full native optimizer.
- The optimized report is semantic only; it intentionally has no `frame` object because no optimized frame is emitted yet.
- No speedup/performance claim exists.
- Python remains the oracle for optimizer rows and canonical reports.

## Boundary hardening

The v1.4 tests expand native VAMD failure surfaces:

- short frame;
- bad version;
- payload length mismatch;
- CRC mismatch;
- unknown opcode;
- bad argument tag;
- invalid UTF-8;
- unknown magic.

## Expanded parity fixtures

The new native parity tests compare VAM0 and VAMD Rust reports against Python reports for:

- duplicate `COMPRESS`;
- idempotent `COMPRESS`;
- obstruction chains;
- compiled Core rows;
- finite shell carriers;
- HL-1 observer/process lowering.

This is broader fixture pressure, not proof-grade equivalence.

## Benchmark harness

`vam/benchmarks/semantic_parity.py` is an optional parity harness:

```bash
PYTHONPATH=. python3 vam/benchmarks/semantic_parity.py --quiet
```

It compares Python and native semantic reports across VAM0/VAMD fixtures and prints `claim=speed-neutral`. Elapsed time is operational metadata only.

## Remaining native/backend work

- Native `COMPRESS` alias/idempotence optimizer slices: closed by v1.5, see `023_vam_v1_5_native_optimizer_extension.md`.
- Native dead-shadow pruning with obstruction-preservation rows: closed by v1.5, see `023_vam_v1_5_native_optimizer_extension.md`.
- Native optimized-frame emission if needed.
- Proof-grade equivalence beyond fixture reports.
- Performance backends only after semantic parity gates remain green.
