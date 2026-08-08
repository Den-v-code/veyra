# Veyra Bytecode Text Draft v0.1

## Text format

Human-readable VAM assembly uses `.vmasm`.

```text
; comment
REZ      %r1, "phase"
NOD      %r2, %r1, "0"
NOD      %r3, %r1, "1"
TACT     %r4, %r2, %r3, "step"
BREATH   %r5, %r4
MODE     %r6, %r5
OBSERVER %r7, "length"
OBSERVE  %r8, %r6, %r7
CERT     %r9, "length-shadow", %r8, "finite demo only"
```

## Register convention

- Registers are `%rN`.
- Registers hold handles to immutable heap objects.
- Rebinding is allowed in text form but compiler/interpreter may lower to SSA later.

## Literal convention

- String literals are UTF-8 quoted strings.
- Integer literals are base-10.
- Future binary bytecode must intern repeated labels.

## Binary frame now implemented

```text
magic:   VAM0
version: u16 = 1
size:    u32 payload length
crc32:   u32 payload checksum
payload: compact JSON instruction table
```

## Round-trip requirement

Assembler/disassembler and VAM0 encode/decode must preserve semantics:

```text
parse(vmasm) -> encode(vmbc) -> decode(vmasm')
```

`vmasm` and `vmasm'` may differ in formatting but must produce identical traces.
