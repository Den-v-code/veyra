# VAM Native Backend Feasibility Path

## Purpose

This document defines the narrow path from the current Python VAM reference
stack to a native backend. The first native target is not speed. The first target
is a Rust executable that proves byte-for-byte and trace-level parity with the
existing VAM0 reference contract.

## First target: Rust VAM0 parity

The first native backend milestone is:

```text
VAM0 bytes -> Rust decoder -> Rust interpreter -> canonical trace/certs
```

It must match the Python reference for the supported VAM0 v1 JSON payload and
current instruction set:

```text
REZ, NOD, TACT, BREATH, MODE, OBSERVER, OBSERVE, ECHO, OBSTRUCT, COMPRESS, CERT
```

Required parity properties:

- accept the same valid VAM0 frames as `vam/src/bytecode.py`;
- reject malformed magic, version, size, CRC32, and payloads deterministically;
- execute instructions in the same order;
- produce the same object kinds, register bindings, trace rows, certificate rows,
  and obstruction rows for every oracle fixture;
- never replace an invalid construction with implicit false, null, panic, or
  host-language exception when the reference emits an `Obstruction`.

## Semantics profiles

Native code must make its semantics profile explicit at load/run time.

### `vam0-ref-v1`

The default profile for the Rust parity target. It means:

- VAM0 v1 frame format exactly as documented in `004_vam0_binary_frame.md`;
- JSON payload remains the canonical instruction table, not dense opcodes;
- string labels are UTF-8 and compared by exact scalar-value equality;
- maps/lists are emitted in canonical order when producing oracle output;
- all observer, echo, certificate, compression, and obstruction behavior follows
  the Python reference interpreter;
- optimization is disabled unless a fixture explicitly tests an accepted
  reference optimizer pass.

### `f4-strict`

A future stricter profile for finite-field or arithmetic-heavy extensions. It is
not the first parity target. It may be enabled only after a written spec defines:

- field modulus and element encoding;
- overflow/reduction rules;
- equality and serialization rules;
- forbidden host floating-point behavior;
- cross-language test vectors.

Until then, native code must reject `f4-strict` programs with a clear unsupported
profile error, not silently run them under `vam0-ref-v1`.

## ABI and frame contract

The native boundary is the VAM0 frame, not an unstable in-memory Python object.
Initial ABI:

```text
input:  immutable byte slice containing one VAM0 frame
output: canonical UTF-8 JSON report or structured error code
```

The report must contain:

- `profile`;
- decoded frame metadata: magic, version, size, crc32;
- canonical instruction listing;
- final program counter;
- register table with stable object identifiers or canonical object payloads;
- trace rows;
- certificate rows;
- obstruction rows;
- deterministic error row when decoding or execution fails.

ABI rules:

- input bytes are never mutated;
- all outputs are deterministic for identical input bytes and profile;
- no wall-clock time, randomness, hash-map iteration order, locale, or thread
  scheduling may affect report content;
- panics are bugs at the ABI boundary and must be converted into deterministic
  error rows during testing;
- native extensions may add fields only behind versioned report keys.

## Test oracle

Python remains the oracle until Rust has proved parity over the fixture suite.

Oracle pipeline:

```text
.vmasm/Core source -> Python IR -> VAM0 -> Python report
VAM0              -> Rust report
compare canonical reports
```

Minimum fixture classes:

- minimal echo certificate acceptance;
- binary frame round-trip and CRC rejection;
- every instruction kind at least once;
- invalid construction producing `Obstruction`;
- certificate rejection when evidence is not accepted echo evidence;
- observer alias and dead-shadow optimizer fixtures only when optimizer parity is
  explicitly in scope;
- malformed JSON payloads and unknown opcode rows;
- deterministic repeated runs.

The v0.9 Rust executor slice compares the named golden fixture corpus against the Python canonical report. A Rust release candidate remains blocked unless every fixture has either exact parity or a documented, versioned semantics-profile difference.

## GPU and FPGA later gates

GPU and FPGA work is gated behind Rust parity. They are not implementation
shortcuts.

GPU gate:

- Rust `vam0-ref-v1` parity is green;
- candidate kernels operate on explicit batches with deterministic ordering;
- CPU fallback gives identical reports;
- no rewrite depends on nondeterministic floating-point, atomics, warp ordering,
  or driver-specific behavior;
- benchmark harness proves correctness before recording throughput.

FPGA gate:

- bitstream target has a stable VAM subset spec;
- host ABI is identical to the Rust frame/report contract or has a versioned
  adapter;
- simulation vectors match the Python and Rust oracles;
- synthesis timing/resource reports are stored separately from semantic claims;
- certificate/obstruction semantics are preserved at the host boundary.

## No-speedup boundary

Until the parity target and gates above are complete, the native backend makes no
speedup claim. Specifically:

- no claim of being faster than Python;
- no claim of compiler optimality;
- no GPU, FPGA, SIMD, or parallel advantage claim;
- no proof-assistant completeness claim;
- no theorem-validity claim beyond the same bounded certificate rows accepted by
  the reference interpreter.

The only early success metric is semantic parity: same accepted frames, same
rejections, same trace/certificate/obstruction meaning.

## Feasibility milestones

1. Add a Rust crate scaffold under `vam/native/` without replacing Python. ✅
2. Implement VAM0 header validation and CRC checks. ✅
3. Decode the JSON instruction table into Rust IR. ✅
4. Execute `vam0-ref-v1` without optimizer support. ✅ first slice
5. Emit reports comparable with Python oracle output. ✅ first slice
6. Add fixture comparison tests for all current instruction kinds. ✅ golden fixture slice
7. Expand malformed-payload/obstruction-shape coverage, then evaluate dense opcodes, optimizer parity, GPU, or FPGA experiments.
