# Research Lean module memory

Version: **0.3.0**. Status: **`INTERNAL_RESEARCH_CANDIDATE`**.

- `manifest.json` is canonical: exactly 53 stable dependencies, ten research
  sources, 87 declarations, 41 literal headline claim rows, 87 axiom-closure
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

## Session Notes (2026-08-30)

- Added `VeyraResearchR16Z4Audit.lean` as the tenth manifest-bound research
  source. Its single headline theorem is axiom-free on the pinned Lean toolchain.
- The theorem checks all 4×4 Z4 shift/observer combinations against an exact
  greatest-admitted-lower decision predicate and separately checks the existing
  five-state no-greatest partiality shape. Python hostile coverage binds the
  exact Z4 observer partitions, cyclic maps, expected-best table, and the exact
  five-state partiality fixture to the executable `observer_descent` runtime.
- Exact replay: 63/63 sources, 87/87 declarations and axiom rows, no skipped
  sources. The Lean file is a standalone finite model and does not formally
  depend on `THM-R16-001..003`. This is a bounded formal audit only: the 64 composition-gap rows,
  universal descent totality, novelty, and R8 promotion remain outside claim.

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
