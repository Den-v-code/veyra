# VAM v1.5 — Native optimizer extension boundary

**Status:** implemented bounded checkpoint.  
**Scope:** native Rust optimizer slices that extend the v1.4 observer-alias parity path without claiming a full optimizer, proof, or speedup.

## Purpose

VAM v1.5 narrows the next native optimizer work to a small set of semantics-preserving rewrites that can be checked against the existing Python oracle and golden reports:

```text
VAM0 bytes -> Rust decoder -> bounded Rust optimizer slices -> Rust executor -> semantic report
```

The v1.5 extension is about parity and boundary discipline. It is not a backend performance milestone.

## Implemented slices

### 1. Duplicate `COMPRESS` aliasing

A duplicate `COMPRESS` may be removed only when the native pass can prove, within the local program rows, that the later row repeats an earlier compression with the same effective inputs and observer context.

Required behavior:

- rewrite later uses of the duplicate destination to the earlier destination;
- preserve the original semantic report;
- emit optimizer rows compatible with the Python oracle;
- reject or leave unchanged any ambiguous dependency chain.

This mirrors the v1.4 duplicate-observer shape, but the key is `COMPRESS` equivalence rather than observer kind alone.

### 2. Same-observer compress-idempotent

A same-observer idempotent `COMPRESS` slice may collapse repeated compression only when the observer identity and compressed source relation are unchanged.

Allowed shape:

```text
COMPRESS %r2, %source_x, %obs_a
COMPRESS %r3, %r2,       %obs_a   # may alias to %r2 under same-observer-visible uses
```

Unsafe or out-of-scope cases must remain unchanged, including:

- different observer registers;
- shadowed or redefined inputs;
- intervening rows that can change the effective observation context;
- malformed or unsupported profiles.

### 3. Dead-shadow pruning

Dead-shadow pruning removes rows whose destinations are provably unused and whose removal cannot change obstruction, diagnostics, or semantic report rows.

The slice is intentionally conservative:

- prune only locally dead shadow rows;
- preserve obstruction-preservation evidence rows;
- do not remove rows that may affect diagnostics or oracle-visible metadata;
- prefer no rewrite over a risky rewrite.

### 4. Unsafe-case boundaries

Every native optimization slice must treat the following as hard boundaries:

- unsupported bytecode profiles, including optimizer input that is not accepted by the slice;
- unknown opcodes or malformed arguments;
- input redefinition or alias chains that the slice does not fully model;
- mixed observer contexts;
- obstruction chains that are not explicitly preserved;
- any case where Python oracle rows and native rows would diverge.

Boundary cases should either reject with the existing native error vocabulary or execute unoptimized, depending on the contract for that input path.

## Oracle parity contract

Python remains the optimizer oracle for v1.5.

Native optimizer output is acceptable only when all relevant parity checks agree with the Python side:

- optimizer rows;
- canonical semantic report;
- obstruction/diagnostic preservation where present;
- unchanged behavior for unsafe or unsupported cases.

Fixture parity is evidence for this bounded slice only. It is not a proof-grade equivalence result.

## Non-claims

VAM v1.5 explicitly does **not** claim:

- a full native optimizer;
- proof-grade optimizer correctness;
- optimized-frame emission as a completed backend feature;
- optimized VAMD frame emission or dense-byte rewrite support;
- speedup or performance improvement;
- replacement of the Python oracle.

Any timing output from harnesses is operational metadata unless a later document defines a performance benchmark contract.

## Acceptance checklist

Before treating a v1.5 slice as complete, require:

- native and Python semantic reports match on targeted fixtures;
- optimizer rows match the Python oracle on targeted fixtures;
- unsafe fixtures are rejected or left unoptimized as specified;
- obstruction-preserving cases remain oracle-visible;
- no documentation or CLI text advertises speed, proof, or full-optimizer claims.
