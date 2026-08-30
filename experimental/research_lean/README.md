# Research Lean candidate

Status: **`INTERNAL_RESEARCH_CANDIDATE`**. This directory is deliberately
outside the 53-source stable Lean inventory and is not part of `make verify`.

The canonical `manifest.json` binds ten research sources, their imports and
SHA-256 digests, 87 declarations (41 headline declarations and 46 helpers), the
41 literal headline signatures and claim boundaries, and the exact axiom
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
| `VeyraResearchR16Z4Audit.lean` | 1 | bounded four-state Z4 best-lower audit plus finite no-greatest partiality witness |

The source scanner rejects project-local `sorry`, `admit`, `axiom`,
`postulate`, `constant`, `opaque`, `unsafe`, `extern`, `implemented_by`, and
`sorryAx` code tokens. That is not an “axiom-free” claim: the frozen report has
27 empty closure rows and 60 rows depending on subsets of `propext`,
`Classical.choice`, and `Quot.sound`.

The candidate lane also rejects command-level declaration metaprogramming
(`run_tac`, custom syntax/elaborators/macros, and `Lean.addDecl`) so an unused
injected axiom cannot sit outside the exact 87-row audit.

Run `make research-lean` for a fresh isolated verification. The checker copies
the exact 53 stable and ten research sources into a temporary tree, compiles
a new `.olean` graph, generates all 86 `#check` and `#print axioms` commands,
and rehashes the originals after execution. It has no persistent cache.

## Evidence and trust boundary

`source_roots.base` and `source_roots.research` hash the ordered
`path + NUL + SHA-256` rows under separate length-delimited domains.
`proof_root` then binds those roots, the exact toolchain identity, all 41
literal claim/scope/registry rows, and all 87 ordered axiom closures. The root
does not hash itself or claim binary reproducibility.

The rebased candidate manifest binds the current 53-source stable inventory
and ten research sources at base root
`4c0722a4fda5cd164cc5bb71acbc87d18b5e85014fb28d46dc017cc0b841628b`,
research root
`d2a574edc19637a618be173482355995807200f9e1c5b65e933dd4a6112008e8`,
and proof root
`774f2c0661561adface14741f180fa10d241434449bc4fc79b0493904ad0e2ca`.
The complete manifest SHA-256 is
`beb2930b364c690cfc3755dc6745188b1a12179e232f166045687dbb453d281c`.

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
- The R16 Z4 audit is a standalone finite Lean mirror bounded to the exact four-state doctrine, four cyclic shifts, four admitted observer partitions, and one separate five-state partiality witness. Hostile Python tests bind those exact partitions, shifts, and the five-state fixture to the executable runtime. It formally covers the 16 best-lower rows only; it does not formally depend on `THM-R16-001..003`, and the 64 composition-gap rows remain executable Python evidence. It proves no universal descent totality, novelty, or promotion.
- Prime, gcd, and Fermat declarations are classical local `Nat` results, not a
  Veyra resonance-prime theory, native repair, or factorization foundation.
- Counting identities are not event-theoretic or general probability results.
- Integer Pythagorean identities do not promote the stable fixed natural card.
- These declarations have no stable theorem IDs, certificates, package runtime
  surface, public validation, registry promotion, or mathlib equivalence claim.
