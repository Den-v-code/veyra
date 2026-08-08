# Definitions 116–176

Part of the public [Theorem and Definition Registry](../../THEOREMS.md).

## Definitions 116–176

## DEF-116 — Combinatorial count echo
An exact finite count echo such as factorial or binomial choice count.

## DEF-117 — Binomial symmetry card
A theorem card certifying `C(n,k)=C(n,n-k)`.

## DEF-118 — Probability union card
A theorem card certifying `P(A∪B)=P(A)+P(B)-P(A∩B)`.

## DEF-119 — Probability independence card
A theorem card classifying `P(A∩B)=P(A)P(B)`.

## DEF-120 — Variance shift card
A theorem card certifying sample variance invariance under constant shifts.

## DEF-121 — Sage export row
A JSON-ready bridge row from Veyra theorem/curriculum registry to future Sage objects.

## DEF-122 — Sage theorem spec wrapper
A Sage-facing immutable wrapper for one Veyra theorem registry spec.

## DEF-123 — Sage curriculum node wrapper
A Sage-facing immutable wrapper for one school-core curriculum concept.

## DEF-124 — Veyra school-core facade
The `VeyraSchoolCore` object combining theorem specs, curriculum nodes, missing-concept checks, and export rows.

## DEF-125 — Sage facade export dictionary
A JSON-ready dictionary emitted from a `VeyraExportRow` for notebooks, labs, and future Sage parents.

## DEF-126 — Sage proof object
A theorem spec promoted into a Sage-facing object that can check executable Veyra theorem cards.

## DEF-127 — Sage proof check
The result of checking a theorem card against dependencies, success relations, and obstruction catalog.

## DEF-128 — Sage proof graph
A query facade over theorem-definition edges, domain index, and curriculum paths.

## DEF-129 — Veyra notebook cell
A markdown or code cell generated from Veyra school/proof facades.

## DEF-130 — Veyra notebook artifact
A markdown/ipynb-renderable lab artifact built from Veyra registry summaries, paths, and export rows.

## DEF-131 — Domain notebook spec
A descriptor for one focused theorem-domain notebook and its theorem IDs.

## DEF-132 — Domain theorem notebook family
The generated family of domain notebooks over all current Sage-hook theorem domains.

## DEF-133 — Executable card example
A reproducible theorem-card instance that can be checked by a Sage-facing proof object.

## DEF-134 — Card example summary
Coverage summary counting executable theorem-card examples, ready checks, and domains.

## DEF-135 — Executable card notebook
A domain notebook whose code cells run theorem-card examples and assert ready proof checks.

## DEF-136 — Refutation example
An intentional failing theorem-card instance that must be blocked by a Sage-facing proof object.

## DEF-137 — Mutation card
A deliberately corrupted card used to test checker boundaries when valid inputs are tautologically successful.

## DEF-138 — Refutation notebook
A domain notebook whose code cells run bad/mutated cards and assert blocked proof checks.

## DEF-139 — Refutation search candidate
A parameterized theorem-card candidate evaluated by the proof checker during negative search.

## DEF-140 — Refutation search hit
A blocked candidate discovered by parameterized search, with parameters and obstruction.

## DEF-141 — Refutation search report
A per-domain report counting tried candidates and blocked hits.

## DEF-142 — Veyra grammar
The atom/call syntax accepted by the Core Language parser.

## DEF-143 — Veyra kind
A typed expression class: rez, nod, tact, breath, mode, trace, weight, relation, observer, obstruction, or value.

## DEF-144 — Veyra assembly rule
A constructor/type compatibility rule checked before an expression can be inferred.

## DEF-145 — Echo relation
Observer-indexed sameness relation `echo(left,right,observer)`, used instead of primitive equality.

## DEF-146 — Veyra inference state
The triad `ready`, `blocked`, `unknown` returned by the language inference engine.

## DEF-147 — Veyra normal form
Canonical structural trace used to compare and persist expressions.

## DEF-148 — Semantic shadow
Declared external-domain projection of a Veyra expression into arithmetic, geometry, logic, or generic views.

## DEF-149 — Veyra interpreter
The pipeline parse → type-check → normalize → infer → semantic shadow.

## DEF-150 — School translation row
A bridge from a school-math term to its Veyra-language expression and caveat.

## DEF-151 — Source span
A half-open source range with line/column start used to locate grammar objects.

## DEF-152 — Veyra token
A lexical unit carrying token kind, original text, and source span.

## DEF-153 — Spanned expression
A Veyra expression AST node preserving the source span that generated it.

## DEF-154 — Parse diagnostic
A structured grammar obstruction with source span, expected token, and found token.

## DEF-155 — Span-to-plain bridge
The projection from spanned AST back to the v0.1 plain `VeyraExpr` inference layer.

## DEF-156 — Veyra proof step
A source-spanned rule application recording input kinds/statuses, output kind/status, and obstruction.

## DEF-157 — Veyra proof trace
The full proof-object record for one source expression, including parse result, normal form, final check, and steps.

## DEF-158 — Veyra proof summary
A compact count of ready, blocked, and unknown steps in a proof trace.

## DEF-159 — Language mutation case
A generated malformed or edge source expression with expected proof-trace status.

## DEF-160 — Language mutation result
The actual proof-trace outcome of one mutation case compared to its expected status.

## DEF-161 — Language mutation report
Aggregate counts for mutation cases by blocked, unknown, ready, and unexpected outcomes.

## DEF-162 — Sage language lab
A Sage-facing facade over Core Language interpreter, proof trace, and mutation report.

## DEF-163 — Sage language result row
A JSON-ready interpretation row containing source, normal form, status, kind, domain, and obstruction.

## DEF-164 — Sage language trace row
A JSON-ready compact proof-trace row containing parse status, final status, counts, and boundary rules.

## DEF-165 — Sage language notebook
A notebook artifact that runs the Core Language wrapper smoke checks.
## DEF-166 — Generated mutation family — Deterministic mutation probes sharing arity, constructor, observer, or label axis.
## DEF-167 — Generated mutation family report — Aggregate generated-family blocked/unknown/ready/unexpected counts.
## DEF-168 — Property language fuzz case — Seed-generated probe whose expected status follows a family law.
## DEF-169 — Language shrink witness — Minimal representative preserving a larger probe obstruction class.
## DEF-170 — Property fuzz report — Seeded property-fuzz counts plus shrink success counts.
## DEF-171 — Language coverage cell — Per-family row counting cases and status outcomes.
## DEF-172 — Language coverage report — Aggregate matrix summary of families, cases, missed families, and shrink witnesses.
## DEF-173 — Span diagnostic case — Parser diagnostic probe with expected token, found token, message, line, and column.
## DEF-174 — Span diagnostic coverage report — Aggregate source-span diagnostic counts for cases, excerpts, multiline inputs, missed checks, and unexpected outcomes.
## DEF-175 — Veyra Essence axiom
A declared non-school primitive principle with a witness hook tying it to executable Veyra layers.

## DEF-176 — Essence/Core readiness report
A finite report counting Essence axioms, ready core layers, checklist items, missing layers, and final `core_ready` status.

## Active registry from DEF-177
