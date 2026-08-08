# VAM0 Binary Frame v0.3

## Scope

VAM0 is the first binary envelope for VAM instruction IR. It is intentionally simple and deterministic:

```text
magic:    4 bytes = VAM0
version:  u16 = 1
size:     u32 payload byte length
crc32:    u32 payload checksum
payload:  compact UTF-8 JSON instruction table
```

## Implemented API

- `encode_vmbc(program) -> bytes`
- `decode_vmbc(blob) -> list[Instruction]`
- `write_vmbc(path, program)`
- `read_vmbc(path) -> list[Instruction]`

## Round-trip invariant

```text
.vmasm -> Instruction IR -> VAM0 bytes -> Instruction IR -> interpreter trace
```

The decoded IR must be comparable to the original IR and must preserve accepted certificates for the minimal echo fixture.

## Boundary

This is a binary frame, not a compact optimized VM encoding yet. The JSON payload is deliberate: correctness and inspectability first; dense opcodes later.
