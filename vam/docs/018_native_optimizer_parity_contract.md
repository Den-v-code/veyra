# 018 — Native optimizer parity contract

This document is the gate for any future Rust/native VAM optimizer. It does not
implement that optimizer. It defines what must be proven before native code may
rewrite VAM programs instead of merely decoding/executing them.

Native optimizer work is blocked until this contract has fixture coverage and a
comparison harness against the Python reference optimizer in `vam/src/optimizer.py`.

## Scope

The contract applies only to the current VAM reference profile:

```text
profile: vam0-ref-v1
input:   immutable VAM0 v1 frame bytes with compact UTF-8 JSON instruction table
output:  deterministic optimizer parity report plus canonical execution report
```

The supported instruction vocabulary is the current VAM0/ref-v1 set:

```text
REZ, NOD, TACT, BREATH, MODE, OBSERVER, OBSERVE, ECHO, OBSTRUCT, COMPRESS, CERT
```

Optimization is opt-in. A native executor must continue to run with optimization
disabled unless a test or caller explicitly requests optimizer parity mode.

## Input profiles

### Accepted profile: `vam0-ref-v1`

A native optimizer candidate may only consume programs that first pass the same
VAM0 decoder boundary as the native executor:

- magic/version/size/CRC are valid;
- payload is valid UTF-8 JSON using the current instruction-table shape;
- every opcode is known to `vam0-ref-v1`;
- instruction argument arity and register spelling are decoded exactly as the
  Python path would decode them;
- no dense opcode, binary IR shortcut, or host-specific object is introduced.

### Rejected profiles

The optimizer must deterministically reject, without rewriting:

- `f4-strict` until a separate arithmetic semantics spec exists;
- dense-opcode payloads;
- GPU/FPGA/SIMD batch profiles;
- programs whose decoder boundary would fail in Python or Rust execution parity;
- any unversioned profile extension.

Profile rejection is a boundary result, not an optimizer rejection row.

## Allowed passes

A native optimizer may implement only the Python reference passes, in the same
order, with the same guard semantics and audit rows:

1. `observer-alias`
   - May remove a duplicate `OBSERVER` definition with the same kind.
   - Requires a single definition for the duplicate destination.
   - Rewrites later non-destination register operands through the alias.
2. `compress-alias`
   - May remove a duplicate `COMPRESS` of the same `(source, observer)` pair.
   - Requires single definitions for destination, prior destination, source, and
     observer.
   - Must reject if either compression object contains obstruction evidence.
3. `compress-idempotent`
   - May collapse a nested same-observer compression only when all involved
     registers are single-definition.
   - Observer object must be an `Observer` whose kind is one of the reference
     idempotent kinds: `boundary`, `kind`, `label`, `length`, `trace`.
   - Target, source, and candidate objects must contain no obstruction evidence.
   - All downstream uses of the candidate must remain inside the same observer
     context; direct `CERT` or `OBSTRUCT` use is a rejection.
4. `dead-shadow`
   - May remove unused `OBSERVE` or `COMPRESS` rows only.
   - Must not remove `CERT`, `OBSTRUCT`, or `ECHO` rows.
   - Must reject dead rows with multiple definitions or obstruction evidence.

No native pass may be added, reordered, fused, or weakened under this contract.
Any new pass requires a new versioned contract document and fixtures.

## Optimizer parity report

Before native optimization is considered implemented, the comparison harness must
produce a deterministic parity report containing at least:

- `profile`: `vam0-ref-v1`;
- `optimizer_contract`: `native-optimizer-parity-v1`;
- canonical original instruction rows;
- canonical Python optimized instruction rows;
- canonical native optimized instruction rows;
- Python optimizer audit rows;
- native optimizer audit rows;
- Python equivalence summary for original vs optimized program;
- native execution report for the native optimized program;
- Python canonical execution report for the Python optimized program;
- boundary or mismatch error row when parity fails.

The canonical JSON serialization must be stable under repeated runs: sorted map
keys, stable list order, no wall-clock time, randomness, locale, hash-map order,
thread scheduling, pointer addresses, or panic text in comparable fields.

## Canonical report equivalence

For every fixture where the Python optimizer accepts any rewrite, native parity
requires all of the following:

1. Python and native optimized instruction rows are identical.
2. Python and native optimizer audit rows are identical.
3. Python `canonical_report(optimized_program, execute(optimized_program))`
   equals the native execution report for the native optimized program over the
   comparable `vam0-ref-v1` fields.
4. Python `compare_optimizer_programs(original, optimized).safe` is true.
5. Certificate acceptance rows match the original program.
6. Obstruction rows and nested obstruction counts match the original program.
7. Selected semantic root evidence is preserved.

Full original-vs-optimized report equality is not required because a valid
optimizer may remove instructions. The required original-vs-optimized comparison
is the conservative equivalence fingerprint: roots, certificates, obstructions,
and obstruction counts.

## Rejected-row parity

Rejected optimizer decisions are observable contract data. Native parity must
match Python rejected rows exactly for pass name, action, detail, accepted flag,
and row order.

If Python emits a rejected row, native must:

- emit the same rejected row;
- preserve the same instruction row in the optimized output;
- avoid applying a later rewrite that would make the rejection unobservable;
- keep the final canonical report equivalent to the Python optimized report.

If Python silently does not consider a row for a pass, native must also emit no
row. Native code must not invent advisory warnings in the comparable audit row
stream; extra diagnostics require a versioned non-comparable field.

## Obstruction preservation

Obstructions are semantic evidence, not errors to be optimized away.

A native optimizer must preserve:

- explicit `OBSTRUCT` side-effect rows;
- construction-type obstructions from invalid `NOD`, `TACT`, `BREATH`, `MODE`,
  `OBSERVE`, and `COMPRESS` uses;
- missing-register witness obstructions;
- nested obstructions inside compressed or observed shadows;
- obstruction data reachable from certificate evidence;
- obstruction counts and obstruction report rows used by equivalence checks.

A native optimizer must never convert an obstruction into `false`, `null`, an
empty object, a skipped instruction, or a host-language exception.

## Fixture classes required before implementation

The fixture suite must include positive and negative cases for each class below:

- baseline accepted echo certificate;
- every instruction kind in one executable corpus;
- VAM0 frame round-trip plus malformed magic, version, size, CRC, UTF-8, JSON,
  unknown opcode, and argument-shape failures;
- explicit manual obstruction;
- construction-type obstruction for each relevant primitive;
- missing-register witness obstruction;
- nested obstruction inside `OBSERVE`/`COMPRESS` shadows;
- shell transported, shell blocked, and shell unsupported carriers;
- observer alias accepted rewrite and non-rewrite surfaces;
- duplicate compression accepted rewrite;
- duplicate compression rejected for multiple definitions and obstruction;
- idempotent compression accepted rewrite;
- idempotent compression rejected for different observer, malformed observer,
  non-idempotent observer kind, multiple definitions, nested obstruction,
  candidate feeding `CERT`, candidate feeding `OBSTRUCT`, and downstream use
  outside the same observer context;
- dead-shadow removal for unused `OBSERVE` and `COMPRESS`;
- dead-shadow rejection for multiple definitions and obstruction evidence;
- deterministic repeated-run comparison for every optimizer fixture.

Every rejection reason reachable in the Python optimizer must have at least one
named fixture before a native optimizer implementation is accepted.

## Failure taxonomy

Parity harness failures must be classified as one of:

- `decode-boundary`: VAM0 magic/version/size/CRC/UTF-8/JSON/opcode/arity mismatch;
- `unsupported-profile`: profile is not `vam0-ref-v1` optimizer parity mode;
- `optimizer-row-mismatch`: accepted/rejected audit rows differ;
- `optimized-program-mismatch`: optimized instruction rows differ;
- `execution-report-mismatch`: native optimized execution report differs from
  Python optimized canonical report;
- `semantic-equivalence-blocked`: original vs optimized equivalence is not safe;
- `obstruction-preservation-failure`: obstruction rows or nested counts differ;
- `certificate-preservation-failure`: certificate acceptance differs;
- `nondeterminism`: repeated runs over identical input produce different reports;
- `native-panic`: native code panicked, trapped, or leaked a host exception across
  the ABI boundary.

`native-panic` is always a bug. It is not a valid semantic rejection.

## Non-claims

This contract does not claim:

- that a native optimizer exists today;
- speedup over Python;
- dense opcode support;
- GPU, FPGA, SIMD, or parallel optimizer readiness;
- theorem-prover completeness;
- `f4-strict` arithmetic semantics;
- permission to add new rewrites;
- proof of optimizer correctness beyond bounded fixture and canonical-report
  parity against the Python reference.

## Checklist

Before native optimizer implementation begins:

- [ ] `vam0-ref-v1` input profile is the only accepted optimizer profile.
- [ ] Unsupported profiles reject before optimization.
- [ ] Pass order is fixed: `observer-alias`, `compress-alias`,
      `compress-idempotent`, `dead-shadow`.
- [ ] Fixture corpus covers every accepted rewrite class.
- [ ] Fixture corpus covers every Python rejection reason.
- [ ] Optimizer audit rows are canonical and compared exactly.
- [ ] Python optimized instruction rows and native optimized instruction rows are
      compared exactly.
- [ ] Python optimized canonical report and native optimized execution report are
      compared over stable `vam0-ref-v1` fields.
- [ ] Original-vs-optimized conservative equivalence summary is safe.
- [ ] Obstruction rows and nested obstruction counts are preserved.
- [ ] Certificate acceptance is preserved.
- [ ] Repeated runs are byte-stable after canonical JSON serialization.
- [ ] Failure taxonomy is emitted by the harness.
- [ ] No speed, dense-opcode, hardware, or proof-assistant claim is made.
