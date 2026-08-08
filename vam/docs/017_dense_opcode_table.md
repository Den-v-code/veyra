# Dense Opcode Table Metadata v0.1

## Scope

This is metadata groundwork only. It assigns stable dense opcode IDs to the
current VAM instruction mnemonics and records arity, operand classes, and
side-effect/certificate/obstruction flags.

It is **not** a dense bytecode encoder, does **not** change the `.vmasm` parser,
does **not** change the VAM0 JSON payload, and is not wired into the interpreter,
optimizer, native runtime, or certificate path yet.

## Operand classes

- `dest_reg` — destination register `%rN`.
- `reg` — source register `%rN`.
- `label` — non-register string label.
- `observer_kind` — non-register string observer name.
- `claim` — non-register string claim/obstruction label.
- `boundary` — non-register string certificate boundary.

## Stable opcode IDs

| ID | Mnemonic | Arity | Operand classes | Flags |
|---:|---|---:|---|---|
| `0x01` | `REZ` | 2 | `dest_reg, label` | — |
| `0x02` | `NOD` | 3 | `dest_reg, reg, label` | — |
| `0x03` | `TACT` | 4 | `dest_reg, reg, reg, label` | — |
| `0x04` | `BREATH` | 2+ | `dest_reg, reg...` | — |
| `0x05` | `MODE` | 2 | `dest_reg, reg` | — |
| `0x06` | `OBSERVER` | 2 | `dest_reg, observer_kind` | — |
| `0x07` | `OBSERVE` | 3 | `dest_reg, reg, reg` | — |
| `0x08` | `ECHO` | 4 | `dest_reg, reg, reg, reg` | side-effect |
| `0x09` | `OBSTRUCT` | 3 | `dest_reg, claim, reg` | side-effect, obstruction |
| `0x0A` | `COMPRESS` | 3 | `dest_reg, reg, reg` | — |
| `0x0B` | `CERT` | 4 | `dest_reg, claim, reg, boundary` | side-effect, certificate |

## Validator boundary

`vam/src/opcodes.py` classifies existing `Instruction` rows and rejects unknown
mnemonics, arity mismatches, and operand-class mismatches. The validator is an
audit helper for future dense encoding work; existing parser/VM behavior remains
the source of execution truth.
