# VAM Spec v0.1

## Machine model

A VAM program executes over a finite machine state:

```text
State = (pc, registers, heap, trace, certs)
```

- `pc` — instruction pointer.
- `registers` — symbolic handles such as `%r0`, `%r1`.
- `heap` — immutable Veyra objects.
- `trace` — append-only execution events.
- `certs` — accepted certificate rows.

## Object kinds

| Kind | Meaning |
|---|---|
| `Rez` | primitive resonance/name atom |
| `Nod` | labeled node over a `Rez` |
| `Tact` | relation/contact between nodes |
| `Breath` | finite process step sequence |
| `Mode` | closed process object |
| `Observer` | projection from object to shadow |
| `Shadow` | observed finite evidence |
| `Echo` | equality/equivalence of shadows under observer family |
| `Obstruction` | witness that a proposed echo/rewrite fails |
| `Certificate` | bounded executable claim with boundary text |

## Core instructions

| Instruction | Stack/register effect | Meaning |
|---|---|---|
| `REZ dst, label` | `dst <- Rez(label)` | create resonance atom |
| `NOD dst, rez, label` | `dst <- Nod(rez,label)` | create node |
| `TACT dst, left, right, label` | `dst <- Tact(left,right,label)` | create relation |
| `BREATH dst, tact...` | `dst <- Breath(tacts)` | create process path |
| `MODE dst, breath` | `dst <- Mode(breath)` | close process into mode |
| `OBSERVER dst, kind` | `dst <- Observer(kind)` | declare observer |
| `OBSERVE dst, obj, obs` | `dst <- Shadow(obj,obs)` | project object |
| `ECHO dst, a, b, obs` | `dst <- Echo(a,b,obs)` | compare shadows |
| `OBSTRUCT dst, claim, witness` | `dst <- Obstruction(...)` | record failure witness |
| `COMPRESS dst, obj, obs` | `dst <- compressed(obj)` | observer-scoped compression |
| `CERT dst, claim, evidence, boundary` | `dst <- Certificate(...)` | bounded acceptance row |

## Determinism

VAM v0.1 is deterministic. Same bytecode plus same initial heap must produce same trace and certificates.

## Error model

VAM does not silently coerce invalid objects. Invalid construction yields an `Obstruction`, not an implicit false theorem.

## Non-claim boundary

VAM v0.1 only defines an abstract execution contract. It does not claim native speed, hardware advantage, compiler optimality, quantum advantage, or formal proof-assistant completeness.
