# Definitions 059–115

Part of the public [Theorem and Definition Registry](../../THEOREMS.md).

## Definitions 059–115

## DEF-059 — Mode transformer
A rule from input shadows/traces to output shadows/traces under declared observers.

## DEF-060 — Transformer composition
For transformers `F` and `G`, `(F∘G)(x)=F(G(x))`.

## DEF-061 — Affine lift
The inverse of nonconstant affine transformer `F(x)=ax+b` is `(x-b)/a`; failure marks hiding.

## DEF-062 — Fixed residue
A value `x` with `F(x) ⇔ x` under the chosen observer.

## DEF-063 — Graph shadow
A finite observer table `{(x,F(x))}`; continuous graph geometry is a later completion.
## DEF-064 — Power weave
Integer powers are repeated multiplicative weave in the ratio shadow layer.

## DEF-065 — Transformer iterate
`F^0=id` and `F^(n+1)=F∘F^n`.

## DEF-066 — Root lift
A root is an inverse lift of power weave; failure is recorded as an obstruction.

## DEF-067 — Transition-count lift
A logarithm is a search for transition count `n` with `B^n ⇔ Q`.
## DEF-068 — Completion shadow
A nested family of rational observer intervals representing a not-yet-internal object.

## DEF-069 — Refinement
`J` refines `I` when `I.lower ≤ J.lower ≤ J.upper ≤ I.upper`.

## DEF-070 — Tail limit certificate
A finite certificate that sampled tail values remain within tolerance of a candidate shadow.

## DEF-071 — No-jump condition
A continuity seed: refining input should not cause uncontrolled output jumps.

## DEF-072 — Input tremor
A finite symmetric family of rational perturbations around an anchor mode.

## DEF-073 — Echo-continuity certificate
A finite no-jump witness: all sampled output echoes remain within tolerance of the anchor output.

## DEF-074 — Drift quotient
A local change shadow formed by output drift divided by input drift.

## DEF-075 — Area braid
A finite accumulation of equal-width output strips over an interval shadow.
## DEF-076 — Event point
An anchored observation package whose coordinates are ratio shadows, not primitive dots.

## DEF-077 — Tremor corridor
The bounded interpolation family between two event points.

## DEF-078 — Separation echo
Squared coordinate drift between events; length is a later completion lift.

## DEF-079 — Turn echo
A two-dimensional orientation determinant: left, right, or flat.

## DEF-080 — Area echo
A finite area shadow derived from turn determinant magnitude.
## DEF-081 — Corridor congruence
Two corridors are congruent when their squared separation echoes are equal.

## DEF-082 — Triangle signature
A triangle event family encoded by sorted side echoes and optional turn orientation.

## DEF-083 — Constant-separation shell
A circle-like shell of events at fixed squared separation from a center event.

## DEF-084 — Parallel drift
Two plane corridors with zero direction determinant under the turn observer.

## DEF-085 — Plane relabel
An affine relabeling of two-dimensional event shadows.
## DEF-086 — Theorem card
An executable claim certificate with relation, obstruction, and exact evidence.

## DEF-087 — Dot echo
The sum of coordinate-wise products of two displacement echoes.

## DEF-088 — Pythagorean separation card
A right-apex certificate that squared hypotenuse echo decomposes into leg echoes.

## DEF-089 — Corridor-shell intersection card
A quadratic parameter certificate for corridor crossing of a constant-separation shell.

## DEF-090 — Relabel composition card
A certificate that composed plane relabeling equals sequential relabeling on event shadows.
## DEF-091 — Theorem spec
A registry contract for an executable theorem card: claim, dependencies, success relations, obstructions, and hook.

## DEF-092 — Dependency edge
A directed edge from theorem ID to required definition ID.

## DEF-093 — Registry check
Validation of a produced card against known dependencies and accepted success relations.

## DEF-094 — Obstruction catalog
The declared finite vocabulary of allowed failure modes for a theorem spec.

## DEF-095 — Sage theorem hook
A stable name by which the Sage lab can later expose a theorem/check object.
## DEF-096 — Linear equation card
A theorem card wrapping linear solution and residual verification.

## DEF-097 — Polynomial identity card
A theorem card certifying polynomial identity by coefficient echoes.

## DEF-098 — Continuity card
A theorem card promoting finite echo-continuity certificates.

## DEF-099 — Drift stability card
A theorem card comparing drift quotients across refinement steps.

## DEF-100 — Area additivity card
A theorem card certifying finite area braid additivity over adjacent intervals.
## DEF-101 — Curriculum node
A school concept bucket with domain, grade band, definitions, theorem IDs, and coverage status.

## DEF-102 — Curriculum edge
A directed dependency relation between curriculum nodes.

## DEF-103 — Curriculum gap
A missing or partially covered concept with explicit reason and missing theorem IDs.

## DEF-104 — Domain coverage
Covered/total concept counts grouped by curriculum domain.

## DEF-105 — Sage export row
A tuple linking concept, domain, theorem ID, and Sage hook.
## DEF-106 — Cyclic phase
A finite phase event represented by an index modulo a positive cycle length.

## DEF-107 — Cyclic period card
A theorem card certifying that a full cycle advance returns to the same phase.

## DEF-108 — Chord echo
A rational cyclic shell echo symmetric under shortest-distance complement.

## DEF-109 — Finite distribution
A finite weighted observer family with positive total weight.

## DEF-110 — Event probability
The ratio of selected event weight to total distribution weight.

## DEF-111 — Probability complement card
A theorem card certifying that event and complement probabilities sum to one.

## DEF-112 — Sample echo
A finite tuple of ratio observations for statistics.

## DEF-113 — Sample mean
The ratio echo obtained by dividing total sample weight by sample count.

## DEF-114 — Sample variance
The mean squared deviation echo of a sample.

## DEF-115 — Mean balance card
A theorem card certifying that deviations from sample mean sum to zero.
