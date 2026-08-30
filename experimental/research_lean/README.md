# Research Lean candidate

Status: **`INTERNAL_RESEARCH_CANDIDATE`**. This directory is deliberately
outside the 53-source stable Lean inventory and is not part of `make verify`.

The canonical `manifest.json` binds nine research sources, their imports and
SHA-256 digests, 86 declarations (40 headline declarations and 46 helpers), the
40 literal headline signatures and claim boundaries, and the exact axiom
closure printed by Lean. Ordered domain-separated source and proof roots make
the aggregate review identity explicit. The reviewed toolchain is
`leanprover/lean4:v4.30.0-rc2`, Lean `4.30.0-rc2`, commit
`3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc`.

| Source | Declarations | Scope |
|---|---:|---|
| `VeyraResearchBinomSum.lean` | 13 | classical finite binomial-sum identities |
| `VeyraResearchCards.lean` | 11 | fixed arithmetic/counting cards |
| `VeyraResearchFermat.lean` | 5 | classical `Nat` Fermat support |
| `VeyraResearchFermatCorollary.lean` | 4 | classical `Nat` corollaries |
| `VeyraResearchGcd.lean` | 9 | classical `Nat` gcd support |
| `VeyraResearchPrimes.lean` | 6 | classical local `Veyra.Prime` results |
| `VeyraResearchPythagorean.lean` | 6 | classical integer identities |
| `VeyraResearchShadow.lean` | 11 | unary `Recurrence` pulse/silence image only |
| `VeyraResearchOneTactBridge.lean` | 21 | singleton-tact path-word / Nat / unary `Recurrence` / exact R9-image bridge |

The source scanner rejects project-local `sorry`, `admit`, `axiom`,
`postulate`, `constant`, `opaque`, `unsafe`, `extern`, `implemented_by`, and
`sorryAx` code tokens. That is not an “axiom-free” claim: the frozen report has
26 empty closure rows and 60 rows depending on subsets of `propext`,
`Classical.choice`, and `Quot.sound`.

The candidate lane also rejects command-level declaration metaprogramming
(`run_tac`, custom syntax/elaborators/macros, and `Lean.addDecl`) so an unused
injected axiom cannot sit outside the exact 86-row audit.

Run `make research-lean` for a fresh isolated verification. The checker copies
the exact 53 stable and nine research sources into a temporary tree, compiles
a new `.olean` graph, generates all 86 `#check` and `#print axioms` commands,
and rehashes the originals after execution. It has no persistent cache.

## Evidence and trust boundary

`source_roots.base` and `source_roots.research` hash the ordered
`path + NUL + SHA-256` rows under separate length-delimited domains.
`proof_root` then binds those roots, the exact toolchain identity, all 40
literal claim/scope/registry rows, and all 86 ordered axiom closures. The root
does not hash itself or claim binary reproducibility.

The rebased candidate manifest binds the current 53-source stable inventory
and nine research sources at base root
`e1f90dfdc5d4971f25ee671dbe655fb19f6722537d4a425bc41939d65841ed9f`,
research root
`caf7d1c2e0e7e8333132300a0ebe5099e35b4fb70d47033fcc8bf033f4c9f597`,
and proof root
`e82dede61b51d1e2e22ef75f21b093152cb32210ac519142c3ba89df0ff61d3f`.
The complete manifest SHA-256 is
`a38687fa331892a95e8ee155dea90de4ce65c79da16b3cc5ec6ec4151262b49c`.

The trusted computing base remains the selected Lean compiler/kernel and its
reported primitive axioms, local Elan or hosted archive delivery, the Python
checker and host operating system, plus human review of the claim ledger. Exact compiler
version and commit checking is identity evidence, not a bit-for-bit runtime
attestation. Hosted CI verifies its exact clean checkout SHA before and after
replay (a synthetic merge SHA on `pull_request`, not necessarily the public PR
head); integration must separately match the public head. A repository
revision is deliberately not embedded in the same commit it names.

## Nonclaims

- The shadow file covers only the unary `Recurrence` pulse/silence image. It
  does not establish AX-007, LEM-001, a general Mode bridge, or THM-001–003.
- The one-tact bridge covers only the explicitly singleton-generated path-word
  realization. It does not prove that AX-007 excludes additional tacts, does not
  establish general LEM-001, does not identify arbitrary strict modes with `Nat`,
  and does not promote THM-001–003 or W-001.
- The realization-transport label bridge proves that concrete equality-class
  labels induce the same extensional pullback relation when an explicit
  `SamePartitionLabels` premise holds. Exhaustive small-map Python tests check
  that premise for the current normalization/runtime rows; this is not Python
  implementation equivalence, R16 descent existence, P1-A vertical transport,
  category/functor/naturality, or promotion.
- Prime, gcd, and Fermat declarations are classical local `Nat` results, not a
  Veyra resonance-prime theory, native repair, or factorization foundation.
- Counting identities are not event-theoretic or general probability results.
- Integer Pythagorean identities do not promote the stable fixed natural card.
- These declarations have no stable theorem IDs, certificates, package runtime
  surface, public validation, registry promotion, or mathlib equivalence claim.
