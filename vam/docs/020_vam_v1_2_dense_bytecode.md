# VAM v1.2 Dense Bytecode Specification

## 1. Purpose

VAMD is the dense binary successor to the existing VAM0 JSON-envelope frame.
VAM0 is intentionally simple and inspectable: it wraps a JSON instruction table
inside a binary envelope. That made early round-tripping easy, but it leaves
opcode identity, operand tagging, and runtime decoding too indirect for the
next slice of the stack.

VAMD exists to provide a compact, explicit wire format for encoder/runtime
parity:

- one opcode byte per instruction,
- typed operands on the wire,
- stable binary layout for Python and Rust implementations,
- less dependence on JSON parsing for the core instruction path.

This document does **not** claim a performance breakthrough, a proof-assistant
integration, or a semantic upgrade over VAM0. It only defines a denser frame
for the same instruction family.

## 2. Relation to VAM0

VAM0 remains the reference-friendly frame:

- easier to inspect in tests and fixtures,
- useful for human-readable tooling,
- suitable for early validation and compatibility checks.

VAMD is the dense transport:

- better for native CLI integration,
- better for runtime/encoder parity testing,
- better for future non-JSON pipelines.

Both frames carry the same instruction vocabulary. VAMD is not a new language;
it is a new byte-level representation of the same VAM IR slice.

## 3. Frame layout

All multi-byte integers are **big-endian**.

### 3.1 Outer header

```text
magic:        4 bytes  = b"VAMD"
version:      u16      = 1
payload_len:  u32      = length in bytes of payload
crc32:        u32      = CRC-32 of payload bytes
payload:      payload_len bytes
```

The header byte layout matches `>4sHII`:

- `4s` = magic `b"VAMD"`
- `H`  = version
- `I`  = payload length
- `I`  = payload CRC-32

`payload_len` covers only the payload, not the header.

`crc32` is computed over the exact payload byte sequence.

### 3.2 Payload layout

```text
instruction_count: u16
instructions:      repeated instruction records
```

Each instruction record is:

```text
opcode:    u8
line:      u32
arg_count: u8
args:      repeated encoded arguments
```

### 3.3 Argument encoding

Each argument begins with a one-byte tag:

- `1` = register
- `2` = integer
- `3` = string

Argument bodies:

```text
reg arg:
  tag:   u8 = 1
  value: u16

int arg:
  tag:   u8 = 2
  value: i64

str arg:
  tag:   u8 = 3
  len:   u16
  bytes: len bytes of UTF-8
```

String bytes must be valid UTF-8.

## 4. Opcode table

Dense opcode IDs are stable and reserved for the VAM v1.2 slice.

| Opcode | Mnemonic | Meaning |
|---:|---|---|
| `0x01` | `REZ` | initialize / bind a result register |
| `0x02` | `NOD` | structural node operation |
| `0x03` | `TACT` | three-operand tactical operation |
| `0x04` | `BREATH` | variadic breath operation |
| `0x05` | `MODE` | mode selection / routing |
| `0x06` | `OBSERVER` | observer construction |
| `0x07` | `OBSERVE` | observation / readback |
| `0x08` | `ECHO` | echo / emission operation |
| `0x09` | `OBSTRUCT` | obstruction operation |
| `0x0A` | `COMPRESS` | compression-oriented transform |
| `0x0B` | `CERT` | certificate boundary / certificate operation |

These IDs correspond to the dense opcode table used by the encoder and runtime
and must not be reassigned within version 1.

## 5. Instruction invariants

A VAMD payload is valid only if all of the following hold:

1. `magic == b"VAMD"`.
2. `version == 1`.
3. `payload_len` exactly matches the payload byte count.
4. `crc32(payload)` exactly matches the header checksum.
5. `instruction_count` is fully consumable by the payload.
6. Every instruction opcode is in `0x01..0x0B`.
7. Every instruction record has a parseable `line` and `arg_count`.
8. Every argument tag is one of `1`, `2`, or `3`.
9. Register arguments fit in `u16`.
10. Integer arguments fit in signed `i64`.
11. String arguments are UTF-8 and their declared length fits in `u16`.
12. The payload has no trailing undecoded bytes after the declared instruction
    set is consumed.

## 6. Error boundaries

The decoder must fail closed on structural errors:

- invalid magic,
- unsupported version,
- truncated header,
- payload length mismatch,
- CRC mismatch,
- truncated instruction record,
- truncated argument body,
- unknown opcode,
- unknown argument tag,
- invalid UTF-8,
- declared counts that overrun the payload.

The encoder must fail before writing bytes if an instruction cannot be
represented faithfully in the dense frame.

The runtime must not guess missing data, infer unknown tags, or silently coerce
out-of-range values.

## 7. Acceptance tests

Minimum acceptance coverage for this spec:

- Encode a known instruction list, decode it, and compare the IR for equality.
- Reject a frame with the wrong magic.
- Reject a frame with a bad CRC32.
- Reject a frame with a mismatched `payload_len`.
- Reject a frame with an unknown opcode.
- Reject a frame with an unknown argument tag.
- Reject a frame with invalid UTF-8 in a string argument.
- Verify that `instruction_count` and per-instruction `arg_count` are honored.
- Verify that opcode IDs `0x01..0x0B` map to the documented mnemonics.

A minimal golden fixture should round-trip through:

```text
encoder -> VAMD bytes -> decoder -> same instruction IR
```

## 8. Non-claims

VAMD is deliberately limited in scope. It does **not** claim:

- faster execution by itself,
- lower proof burden,
- proof-assistant completeness,
- a replacement for VAM0 in all tooling,
- compatibility with unknown future opcodes,
- semantic changes to the instruction set.

Dense opcodes are intended for encoder/runtime parity and wire efficiency,
not as a benchmark result or formal guarantee.

## 9. Implementation notes

Python and Rust implementations should treat this document as the source of
truth for byte layout and validation behavior.

Suggested next steps:

1. Add a Python encoder/decoder that round-trips the dense frame. ✅ v1.2
2. Add a Rust parser with the same tests and fixtures. ✅ v1.2
3. Integrate VAMD into the native CLI path. ✅ v1.3 via magic autodetect
4. Keep VAM0 available for human-readable and regression-oriented use.
5. Add cross-language parity tests so both implementations reject the same bad
   frames and accept the same golden fixtures.

## 10. Summary

VAM0 = readable bootstrap frame.
VAMD = dense bytecode frame for the same VAM instruction family.

The contract is simple: exact bytes in, exact bytes out, explicit failures on
corruption, and no hidden reinterpretation.
