# VAM Core Language lowering v0.5

## Scope

`vam.src.compiler` is the first bridge from the current Veyra Core Language into VAM IR. It lowers the finite executable subset:

```text
rez:x
nod:x
nod(rez:x)
tact(nod:a,nod:b)
breath(tact(...), ...)
mode(breath(...))
observer:length|kind|label|trace|boundary
echo(left,right,observer:...)
shell(echo(...), echo(...), ...)  # finite direct echo children only
```

The compiler emits destination-register VAM instructions and can append a `CERT` row for ordinary root relations. Shell lowering intentionally disables top-level `CERT` and emits a non-certificate finite conjunction carrier instead.

## Reference flow

```text
Core source
  -> parse_veyra / normalize_veyra / evaluate_native strict preflight
  -> Instruction IR
  -> VAM0 binary frame
  -> optimizer
  -> interpreter trace/certificate
```

Example:

```python
from vam.src import compile_source, encode_vmbc, decode_vmbc, optimize, execute

source = "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:length)"
compiled = compile_source(source, claim="core-length-echo")
program = decode_vmbc(encode_vmbc(compiled.program))
state = execute(optimize(program).optimized)
assert state.certs[0].field("accepted") is True
```

## Semantics preserved now

- Core terms are normalized and elaborated by `src.core.semantic_kernel.evaluate_native()` before lowering; open modes, non-contiguous breaths, and unknown observers cannot enter compiled VAM.
- `nod:x` becomes an explicit `REZ` plus `NOD`, so VAM never has implicit point/residue construction.
- `echo(left,right,observer:o)` becomes VAM `ECHO` over compiled modes and observer.
- The certificate is accepted only if the VAM interpreter observes a passed `Echo` evidence object.
- Finite supported shells lower to child `ECHO` rows; blocked/unsupported shell children become explicit `OBSTRUCT` rows and never accepted shell certificates.
- VAM `kind`/`label`/`length`/`trace`/`boundary` responses are parity-tested against strict Core/native semantics for `Rez`, `Nod`, `Tact`, `Breath`, and `Mode`.
- The `vam_reference_v1` certificate covers this Core -> VAM -> VAM0 -> optimizer -> interpreter path.

## Boundary

This is not a full proof assistant or full Core compiler. Raw hand-written VAM remains more permissive than compiled Core; finite theorem/shell carriers are transport objects only, and proof traces, quantifiers, source maps through VAM0, and domain-specific shadows still require explicit lowering rules.
