# Notation Catalog
**Project:** Veyra
**Version:** 4.3.1  
**Updated:** 2026-08-09
## Conventions
| Kind | Convention | Example |
|---|---|---|
| Primitive words | lowercase English/Russian term | nod, breath, mode |
| Veyra zero/one | subscript `V` | `0_V`, `1_V` |
| Stitch/addition | rounded plus/stitch | `⊙`, `⊕` |
| Weave/multiplication | tensor-like | `⊗` |
| Echo-equivalence | approximate equality | `≈` |
| Resonance/divisibility | triangle relation | `a ▹ b` |
## Symbols
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `rez` | rez | act of distinction | DEF-001 |
| `●` / `nod` | nod | stable residue of distinction | DEF-002 |
| `τ` | tact | smallest registered transition | DEF-003 |
| `breath` | breath | directed finite tether of tacts | DEF-004 |
| `mode` | mode | closed breath / recurrence | DEF-005 |
| `≈` | echo-equivalence | indistinguishable under admitted tests | DEF-006 |
| `⊙` | stitch | concatenate compatible breaths/modes | DEF-007 |
| `⊕` | mode addition | recurrence stitching | DEF-008 |
| `⊗` | weave | recurrence substitution / multiplication | DEF-009 |
| `0_V` | silent mode | empty closed breath | DEF-010 |
| `1_V` | first mode | one-tact closed breath | DEF-011 |
| `a ▹ b` | resonance | `a` tiles/resonates inside `b` | DEF-012 |
| `≡_m` | phase congruence | same obstruction modulo mode `m` | DEF-013 |
## Naming notes
- **nod** is intentionally not "point".
- **breath** is intentionally not "segment".
- **mode** is intentionally not "number".
- Human terms may appear only as shadows or translations.
## Test-indexed notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `T` | test family | admitted observers for an echo claim | DEF-014 |
| `≈_T` | test-indexed echo | indistinguishable under tests `T` | DEF-015 |
| `T_len` | length test | observes tact count only | DEF-014 |
| `T_bag` | bag/Parikh test | observes tact multiplicities | DEF-014 |
| `T_word` | ordered word test | observes exact tact order | DEF-014 |
| `T_cycle` | cyclic test | observes canonical rotation class | DEF-014 |
## Weave notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `σ` | substitution map | maps driver tacts to replacement modes | DEF-017 |
| `weave_σ(d)` | substitution weave | replace each tact of driver `d` using `σ` | DEF-017 |
| `⊗_len` | length-weave | binary weave: repeat filler by driver length | DEF-018 |
| `Φ` | natural shadow map | maps one-tact mode `τ^n` to `n` | THM-001 |
## Counterexample and compatibility notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `CE-nnn` | counterexample ID | numbered failure/edge case | — |
| `W` | weave schema | operation transforming driver modes | DEF-020 |
| `(T_in,T_out)` | compatibility pair | input/output echo tests for operation well-definedness | DEF-020 |
| `W respects (T_in,T_out)` | schema compatibility | `x≈_{T_in}y` implies `W(x)≈_{T_out}W(y)` | DEF-020 |
## Prime variant notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `P_num` | numeric prime | one-tact `τ^p` where `p` is ordinary prime | DEF-023 |
| `P_ord` | ordered primitive | word not a power of shorter word | DEF-024 |
| `P_cyc` | cyclic primitive | cyclic class not a power of shorter cycle | DEF-025 |
| `P_res(R)` | resonance-prime | no non-unit proper resonant submode under relation `R` | DEF-026 |
| `ρ_cyc(w)` | cyclic root | primitive root of canonical cyclic rotation | DEF-025 |
## Cyclic weave notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `canon_cyc(w)` | cyclic representative | lexicographically least rotation of external word `w` | DEF-027 |
| `cyc_weave_σ(d)` | cyclic weave | substitute canonical driver and canonicalize output cycle | DEF-028 |
| `ord_weave_σ(d)` | ordered weave | linear substitution preserving chosen word cut | DEF-017 |
## Phase resonance notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `rot(w,r)` | rotation | left-rotate word/mode `w` by offset `r` | DEF-029 |
| `phase(part,whole)` | phase offsets | offsets where `rot(whole,r)=part^k` | DEF-029 |
| `▹_cyc` | cyclic resonance | part tiles some rotation of whole | DEF-030 |
| `Ω_res` | resonance obstruction | none / length-obstruction / pattern-obstruction / silent-part | DEF-031 |
## Approximate resonance notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `δ(x,y)` | defect count | number of mismatched tacts between equal-length modes | DEF-033 |
| `Def(i,e,a)` | defect | at index `i`, expected `e`, actual `a` | DEF-032 |
| `▹_{cyc,≤d}` | approximate cyclic resonance | cyclic resonance with at most `d` defects | DEF-034 |
| `bounded-defect` | near-resonance obstruction state | best phase has defects within budget | DEF-034 |
| `over-budget` | near-resonance obstruction state | best phase exceeds defect budget | DEF-034 |
## Resonance spectrum notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `Spec_d(W,C)` | resonance spectrum | ranked profiles for candidates `C` against whole `W` under defect budget `d` | DEF-035 |
| `rank(e)` | spectrum rank | deterministic exploration order for spectrum entry `e` | DEF-036 |
| `best(e)` | best phase match | best offset/defect profile for a spectrum entry | DEF-036 |
## Compression notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `cost(e)` | explanation cost | candidate length plus defect/phase penalties | DEF-037 |
| `save(e)` | compression saving | `len(whole)-cost(e)` | DEF-038 |
| `ratio(e)` | compression ratio | `save(e)/len(whole)` | DEF-039 |
| `w_def` | defect weight | penalty multiplier for each defect | DEF-037 |
| `w_phase` | phase weight | penalty for nonzero phase offset | DEF-037 |
## Processed artifact notation
| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `Artifact(kind,path,rows)` | table artifact | generated processed table metadata | DEF-040 |
| `manifest.json` | generation manifest | parameters and artifact list for a table run | DEF-040 |

## Weighted defect notation

| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `κ(e,a)` | directed defect cost | cost of replacing expected tact `e` by actual tact `a` | DEF-041 |
| `Def_w(i,e,a,c)` | weighted defect | defect at index `i` with cost `c` | DEF-042 |
| `▹_{cyc,κ≤B}` | weighted cyclic resonance | cyclic near-resonance with total defect cost at most budget `B` | DEF-043 |

## Tact aura notation

| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `A_r(x\|C)` | tact aura | cyclic radius-`r` context marks around tact `x` in context `C` | DEF-044 |
| `sim_A(x,y)` | aura similarity | Jaccard overlap of two tact auras | DEF-045 |
| `κ_A(x,y)` | aura-derived defect cost | cost derived from `1-sim_A(x,y)` with nonzero mismatch floor | DEF-046 |

## Balance and ratio notation

| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `B=(B⁺,B⁻)` | balance mode | arising and fading recurrence pair | DEF-047 |
| `opp(B)` | opposite balance | swaps arising/fading poles | DEF-048 |
| `⊞` | balance stitch | add balances by stitching equal-polarity components | DEF-047 |
| `len±(B)` | signed length shadow | `len(B⁺)-len(B⁻)` | DEF-047 |
| `Q=B/S` | ratio mode | balance measured against non-silent scale mode | DEF-049 |
| `shadow(Q)` | rational length shadow | `len±(B)/len(S)` | DEF-050 |
| `raw_add(Q,R)` | raw ratio addition | native cross-scale addition before canonical reduction | DEF-378 |
| `⋉` | scale weave | external scale-mode length-weave product | DEF-377 |

## Order and magnitude notation

| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `≻_len` | length dominance | balance comparison by signed length gap | DEF-051 |
| `\|B\|_len` | balance magnitude | one-tact mode for absolute signed length | DEF-052 |
| `≻_rat` | ratio dominance | ratio comparison by rational shadow gap | DEF-053 |
| `[L,U]` | ratio interval | observer-relative interval between ratio bounds | DEF-054 |

## Equation notation

| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `F(x)=A·x⊕B` | linear ratio form | ratio transformer with coefficient and offset | DEF-055 |
| `F(x)⇔G(x)` | linear constraint | equation between two ratio forms | DEF-056 |
| `Res(x)` | equation residual | difference between left and right evaluated forms | DEF-056 |
| `Ω_eq` | equation obstruction | none / identity / parallel-obstruction | DEF-057 |

## Polynomial notation

| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `P(x)` | polynomial ratio form | finite ratio-coefficient transformer schema | DEF-058 |
| `deg(P)` | polynomial degree | highest nonzero coefficient index | DEF-058 |
| `P'(x)` | formal derivative | coefficient-shift change shadow | DEF-058 |

## Sage laboratory notation

| Symbol | Name | Meaning | Registry |
|---|---|---|---|
| `VeyraModes(Σ)` | Sage mode parent | executable parent for modes over alphabet `Σ` | implementation |
| `VeyraBalances(τ)` | Sage balance parent | executable parent for balance modes over tact `τ` | implementation |
| `VeyraRatios(τ)` | Sage ratio parent | executable parent for ratio modes over tact `τ` | implementation |
| `VeyraPolynomials(τ,x)` | Sage polynomial parent | executable parent for polynomial ratio forms | implementation |

## Extended notation

The remaining stable symbols are listed in the
[extended notation registry](docs/reference/notation-extended.md), covering
transformers, completion, geometry, finite statistics, Sage facades, Core
Language, native resonance, observer doctrine, and completion principles.

## Status interpretation

Notation names an object or schema; it does not promote its mathematical status.
For `AXIOM`, `CONJECTURE`, `FORMALLY_PROVED`, `PUBLICLY_VALIDATED`, and
`INTERNAL_RESEARCH_CANDIDATE`, consult [THEOREMS.md](THEOREMS.md).
