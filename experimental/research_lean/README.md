# Research Lean candidate

Status: **`INTERNAL_RESEARCH_CANDIDATE`**. This directory is deliberately
outside the 53-source stable Lean inventory and is not part of `make verify`.

The canonical `manifest.json` binds ten research sources, their imports and
SHA-256 digests, 93 declarations (47 headline declarations and 46 helpers), the
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
| `VeyraResearchP3OGBounded.lean` | 7 | bounded P3-OG arithmetic/formation/retention/ablation/history formal bridge |

The source scanner rejects project-local `sorry`, `admit`, `axiom`,
`postulate`, `constant`, `opaque`, `unsafe`, `extern`, `implemented_by`, and
`sorryAx` code tokens. That is not an “axiom-free” claim: the frozen report has
26 empty closure rows and 60 rows depending on subsets of `propext`,
`Classical.choice`, and `Quot.sound`.

The candidate lane also rejects command-level declaration metaprogramming
(`run_tac`, custom syntax/elaborators/macros, and `Lean.addDecl`) so an unused
injected axiom cannot sit outside the exact 93-row audit.

Run `make research-lean` for a fresh isolated verification. The checker copies
the exact 53 stable and ten research sources into a temporary tree, compiles
a new `.olean` graph, generates all 93 `#check` and `#print axioms` commands,
and rehashes the originals after execution. It has no persistent cache.

## Evidence and trust boundary

`source_roots.base` and `source_roots.research` hash the ordered
`path + NUL + SHA-256` rows under separate length-delimited domains.
`proof_root` then binds those roots, the exact toolchain identity, all 47
literal claim/scope/registry rows, and all 93 ordered axiom closures. The root
does not hash itself or claim binary reproducibility.

The rebased candidate manifest binds the current 53-source stable inventory
and ten research sources at base root
`4c0722a4fda5cd164cc5bb71acbc87d18b5e85014fb28d46dc017cc0b841628b`,
research root
`f21992f3f11a681a0c41d8c0b9818eb4b7a413a5ad5dfd85c1ff02bfd6d1a179`,
and proof root
`a6c281d7b3e7eb8e282f0401dcf7a5fbbac057553c48e42bc06371f02798c65f`.
The complete manifest SHA-256 is
`01f7e9e7536e0133bbbe7b07a06c0a2725460b263f0880f2534bff03f8d61c5e`.

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
- Prime, gcd, and Fermat declarations are classical local `Nat` results, not a
  Veyra resonance-prime theory, native repair, or factorization foundation.
- Counting identities are not event-theoretic or general probability results.
- Integer Pythagorean identities do not promote the stable fixed natural card.
- These declarations have no stable theorem IDs, certificates, package runtime
  surface, public validation, registry promotion, or mathlib equivalence claim.

- The bounded P3-OG source constructs only the exact finite research model stated
  in its source and imports P3-N2 arithmetic definitions. It does not prove
  Python/Lean implementation equivalence, full DEF-OG-002/009/010,
  `EndogenousArithmeticObserverRole`, THM-P3OG-001/003, HAP, or promotion.
