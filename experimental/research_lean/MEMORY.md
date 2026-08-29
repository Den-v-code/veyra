# Research Lean module memory

Version: **0.4.0**. Status: **`INTERNAL_RESEARCH_CANDIDATE`**.

- `manifest.json` is canonical: exactly 53 stable dependencies, ten research
  sources, 88 declarations, 42 literal headline claim rows, 88 axiom-closure
  rows, and domain-separated aggregate roots.
- `scripts/check_research_lean.py` always uses a fresh temporary snapshot and
  `.olean` tree, exact toolchain version/commit, bounded work, token-aware
  scanning, generated declaration audit, and final original-source rehash.
  Never add a persistent correctness cache.
- Research declarations do not change stable theorem IDs or statuses.
  THM-001–003 remain `CONJECTURE`; W-001 is not promoted by this research bridge.
- Shadow scope is the unary `Recurrence` image only; number theory is classical
  `Nat`/`Int`, not native Veyra arithmetic.
- One-tact bridge scope is the explicit singleton-generated path-word realization
  and its exact R9 image only; it is not an AX-007 exhaustion theorem.
- Native-number scope now has two carrier theorems: a ready native Mode exposes
  its exact tact count through the length observer; stable THM-F002 applies to
  that count, and the existing general research Fermat corollary applies under
  the explicit local `Prime run.length` premise. No native prime generation,
  unit-Breath/orbit coverage, stable THM-F003, layer promotion, or blanket
  native-number formalization follows.

## Session Notes (2026-08-30) — prime-length Fermat bridge

- Added `RESEARCH_NN_T002_ready_mode_prime_length_fermat` in the existing
  native-number research source. For any already-ready native Mode, if its exact
  tact count satisfies local `Veyra.Prime` and does not divide `a`, the existing
  general Fermat corollary yields `a^(run.length-1) % run.length = 1`.
- The theorem reuses the same neutral length carrier as T001 and imports the
  already-audited Fermat corollary rather than modeling native unit Breaths or
  multiplicative orbits. Exact closure is `propext` + `Quot.sound`.
- Exact replay: 63/63 sources, 88/88 declarations and axiom rows, no skipped
  sources. Stable THM-F003 remains executable evidence only; no R8 promotion.

## Session Notes (2026-08-30)

- Added `VeyraResearchNativeNumberBridge.lean` as the tenth manifest-bound
  research source: one headline declaration with exact `propext` closure.
- Extended the existing stable native semantics only with a neutral `length`
  observer/response and unregistered helper `native_length_observes_ready_mode`;
  stable R4 theorem IDs remain `THM-R4-001..007`.
- The research theorem composes that carrier with the existing stable
  `THM-F002_euclid_escape_mod` for any already-ready native Mode and any `k`.
  This closes a native-runtime-to-formal-arithmetic carrier gap without claiming
  prime infinitude, Fermat, R8 promotion, or a third theorem-derived nucleus.
- Exact replay: 63/63 sources, 87/87 declarations and axiom rows, no skipped
  sources; the new theorem depends only on `propext`.

## Session Notes (2026-08-28)

- Rebased the singleton-tact path-word bridge onto the 53-source stable Lean
  inventory after the TR-1/TR-2 merge and regenerated all checker counts and
  aggregate evidence roots from the checker contract.
- The source remains 21 declarations / 7 headlines; 11 axiom rows are empty and
  10 depend only on `propext`. Stable theorem statuses remain unchanged.

## Session Notes (2026-08-14)

- Integrated PR #40 as an isolated manifest-bound candidate.
- Renamed T008 from an independence claim to cross-product reassociation.
- Renewed only the changed stable `VeyraProofElaboration.lean` digest plus the
  derived base/proof roots after PR #37; the research root and candidate
  theorem/claim/axiom/toolchain inventories remain byte-for-byte unchanged.
