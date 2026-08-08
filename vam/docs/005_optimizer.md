# VAM Conservative Optimizer v0.6

## Scope

The first optimizer is intentionally conservative. It optimizes only when an audit row can explain why a rewrite preserves VAM semantics.

Implemented passes:

1. `observer-alias` — remove duplicate `OBSERVER` declarations with the same observer kind and rewrite later uses to the canonical register.
2. `compress-alias` — alias duplicate `COMPRESS` rows with identical source/observer only under single-definition and obstruction-free checks.
3. `dead-shadow` — remove unused `OBSERVE` / `COMPRESS` rows only when the defining row is single-definition and does not produce top-level or nested `Obstruction`.

## Reject rule

If a candidate row produces top-level or nested `Obstruction`, or if its destination/source/observer definition is ambiguous, the optimizer keeps it and emits a rejected optimization row. Failed constructions are evidence and must not be optimized away.

## Certificate boundary

`vam_reference_v1` now checks:

```text
.vmasm -> IR -> VAM0 -> IR -> optimizer -> interpreter -> certificate
```

This is not a general compiler optimizer. `vam/src/equivalence.py` now adds execution-summary evidence for tested original/optimized pairs, but proof of global optimality and native backend rewrites remain future work.
