# VAM Roadmap

## 1. VAM Spec

Define the abstract machine:

- registers and heap objects;
- native object kinds: `rez`, `nod`, `tact`, `breath`, `mode`, `observer`, `shadow`, `certificate`;
- instruction semantics;
- error/obstruction model;
- deterministic execution trace;
- no-overclaim boundary.

## 2. Veyra Bytecode

Status: text assembly `.vmasm`, JSON-envelope `VAM0`, and dense `VAMD` frame exist. `docs/017_dense_opcode_table.md`, `docs/020_vam_v1_2_dense_bytecode.md`, `docs/021_vam_v1_3_native_vamd_execution.md`, `docs/022_vam_v1_4_native_optimizer_slice.md`, `docs/023_vam_v1_5_native_optimizer_extension.md`, `vam/src/opcodes.py`, and `vam/src/dense.py` define the checked dense/native path. Native VAMD CLI execution/report parity, bounded decoded VAM0/VAMD optimizer report parity, VAM0-only optimized-frame emission, v1.8/v1.9 witness/obligation/metamorphic evidence, v2.0-v2.9 optimizer Lean local-law bridges and executable pre/post witness rows now exist; speed work remains future work.

## 3. Interpreter

Status: first Python reference executor exists in `vam/src/interpreter.py`. It executes deterministic register programs, records traces/certificates/obstructions, and treats invalid construction as `Obstruction`. `vam/src/errors.py` adds taxonomy rows for current error surfaces. Rust executes VAM0 and VAMD frames through the same `vam0-ref-v1` report contract; native optimizer work now includes decoded-report parity, VAM0-only optimized-frame emission, bounded witness/metamorphic checks, a proof-obligation ledger, and seven checked local-law bridges, while performance work remains later work.

## 4. Assembler / Disassembler

Status: text `.vmasm -> Instruction IR -> canonical .vmasm` and binary `Instruction IR -> VAM0 -> Instruction IR` round-trips exist. Target flow:

```text
program.vmasm -> program.vmbc -> dump.vmasm
```

## 5. Optimizer

Status: conservative optimizer exists in `vam/src/optimizer.py`. It supports duplicate-observer aliasing, obstruction-safe unused shadow pruning, single-definition guards, nested obstruction detection, duplicate `COMPRESS` aliasing, canonical-report fingerprints, and same-observer `compress-idempotent` normalization. Rust now mirrors those bounded optimizer rows under the historic `observer-alias-v1` CLI slice for decoded VAM0/VAMD semantic reports; `docs/018`, `022`-`027`, and `032`-`036` define the parity/emission/witness/obligation contract. Proof-grade equivalence beyond the checked observer-alias, compress-idempotent accepted/rejected/visible-use guards, compress-alias, and dead-shadow local laws plus executable pre/post witness evidence remains future work.

## 6. Compiler from Core Language

Status: first lowering exists in `vam/src/compiler.py` for finite `echo/mode/breath/tact/nod/observer` Core terms. It preflights Core assembly, emits VAM IR, round-trips through `VAM0`/`VAMD`, and is covered by `vam_reference_v1`. Status checks, source-span diagnostics, finite theorem-case carriers, finite shell/conjunction carriers, and proof-object rows now exist. Future work: proof-grade theorem instruction semantics, full source maps through bytecode frames, and richer semantic shadows.

## 7. Native backend

Status: feasibility plan exists in `docs/010_native_backend_feasibility.md`; `docs/013_*`-`016_*`, `docs/021`-`027`, and `docs/032`-`035` cover the Rust VAM0/VAMD inspector/executor slices, bounded optimizer extension, VAMD optimizer report boundary, optimized VAM0 emission, witness/obligation/metamorphic regression evidence, executable pre/post witness rows, execution contract, golden parity, finite semantics, and boundary hardening. First target remains `vam0-ref-v1` parity, not speed. Later targets after reference semantics are stable:

- Rust VM;
- C/LLVM;
- SIMD/GPU kernels;
- FPGA experiments;
- quantum/stabilizer/QEC-specialized backends.

## 8. High-level language

Status: syntax sketch exists in `docs/011_high_level_language.md`, a tiny seed parser exists in `vam/src/highlevel.py`, and isolated HL-1 lowering exists in `vam/src/highlevel_v1.py` for observer aliases plus one finite process/claim block. Design the full process-first language with syntax for:

- theorem cards;
- observer families;
- echo relations;
- obstruction witnesses;
- certification boundaries.

Next slice contract: `docs/019_high_level_next_slice.md` specifies HL-1 finite carriers, observer declarations, straight-line process blocks, and theorem-card import/open boundaries.
