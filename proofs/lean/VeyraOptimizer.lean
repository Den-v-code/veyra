namespace Veyra

/--
Checked local-law artifact only: this file covers seven bounded local laws —
observer-alias lookup preservation, same-observer compress-idempotent local-window idempotence,
visible-use observer preservation,
different-observer compress-idempotent rejection, obstruction-boundary compress-idempotent rejection,
same-pair compress-alias lookup preservation,
and unused dead-shadow lookup preservation.
The scope is a tiny lookup model only;
it does not cover broad execution, emitted code, or performance claims.
-/
abbrev ObserverKind := String
abbrev ShadowKind := String
abbrev Reg := Nat
abbrev ObserverDecl := Reg × ObserverKind
abbrev CompressDecl := Reg × Reg × Reg
abbrev ShadowDecl := Reg × ShadowKind
abbrev VisibleUseDecl := Reg × Reg

/-- Lookup returns the first register assigned to an observer kind. -/
def lookupObserver : List ObserverDecl → ObserverKind → Option Reg
  | [], _ => none
  | (reg, kind') :: tail, kind =>
      if kind' = kind then some reg else lookupObserver tail kind

/--
A single observer-alias local-law slice: if two adjacent observers have the same string kind,
keep the first declaration as the canonical representative and drop the alias.
-/
def observerAliasStep (head alias : ObserverDecl) (tail : List ObserverDecl) : List ObserverDecl :=
  if head.2 = alias.2 then head :: tail else head :: alias :: tail

/-- Lookup returns the first compress destination for a source/observer pair. -/
def lookupCompress : List CompressDecl → Reg → Reg → Option Reg
  | [], _, _ => none
  | (dst, src', obs') :: tail, src, obs =>
      if src' = src ∧ obs' = obs then some dst else lookupCompress tail src obs

/-- Lookup returns the first shadow kind assigned to a register. -/
def lookupShadow : List ShadowDecl → Reg → Option ShadowKind
  | [], _ => none
  | (dst', kind) :: tail, query =>
      if dst' = query then some kind else lookupShadow tail query

/--
A single compress-alias local-law slice: if two adjacent COMPRESS declarations have
the same source and observer registers, keep the first destination as canonical.
-/
def compressAliasStep (head alias : CompressDecl) (tail : List CompressDecl) : List CompressDecl :=
  if head.2.1 = alias.2.1 ∧ head.2.2 = alias.2.2 then head :: tail else head :: alias :: tail

/--
A tiny dead-shadow local-law slice: an unused local shadow declaration is dropped
while preserving lookups for every queried register other than the dropped destination.
-/
def deadShadowDrop (_candidate : ShadowDecl) (tail : List ShadowDecl) : List ShadowDecl :=
  tail

/--
Tiny local-window model for the compress-idempotent slice.  A window is either still an
adjacent observer pair or is already compressed to the canonical head observer.  This is
only a local law over one observer window.
-/
inductive ObserverWindow where
  | adjacent (head alias : ObserverDecl) (tail : List ObserverDecl)
  | compressed (head : ObserverDecl) (tail : List ObserverDecl)
  deriving Repr, DecidableEq

/--
Compress one local observer window when the two observer kinds are the same string.
Non-matching observer kinds are left as the same adjacent local window.
-/
def compressObserverWindow : ObserverWindow → ObserverWindow
  | ObserverWindow.adjacent head alias tail =>
      if head.2 = alias.2 then
        ObserverWindow.compressed head tail
      else
        ObserverWindow.adjacent head alias tail
  | ObserverWindow.compressed head tail => ObserverWindow.compressed head tail

/--
Evidence-boundary local model: if the candidate feeds an obstruction witness,
the local window must stay visible even when the observer kind matches.
-/
def compressObserverWindowWithEvidence (feedsObstruction : Bool) (window : ObserverWindow) :
    ObserverWindow :=
  if feedsObstruction then window else compressObserverWindow window

/-- Rewrite a visible same-observer use by changing only the observed register. -/
def rewriteVisibleUse (candidate source : Reg) (use : VisibleUseDecl) : VisibleUseDecl :=
  if use.1 = candidate then (source, use.2) else use

/-- Read the observer register of a visible local use. -/
def visibleUseObserver (use : VisibleUseDecl) : Reg :=
  use.2

/-- Duplicate observer kinds keep the first register as the canonical representative. -/
theorem observerAlias_keeps_first
    (r₁ r₂ : Reg) (k : ObserverKind) (tail : List ObserverDecl) :
    lookupObserver (observerAliasStep (r₁, k) (r₂, k) tail) k = some r₁ := by
  simp [observerAliasStep, lookupObserver]

/-- Removing an adjacent duplicate observer kind does not change lookups for other kinds. -/
theorem observerAlias_preserves_other
    (r₁ r₂ : Reg) (k q : ObserverKind) (h : q ≠ k) (tail : List ObserverDecl) :
    lookupObserver (observerAliasStep (r₁, k) (r₂, k) tail) q =
      lookupObserver ((r₁, k) :: (r₂, k) :: tail) q := by
  have hkq : k ≠ q := by
    intro hEq
    exact h hEq.symm
  simp [observerAliasStep, lookupObserver, hkq]

/-- Local observer-alias lookup law preserves lookup results for every queried kind. -/
theorem observerAlias_lookup_invariant
    (r₁ r₂ : Reg) (k q : ObserverKind) (tail : List ObserverDecl) :
    lookupObserver (observerAliasStep (r₁, k) (r₂, k) tail) q =
      lookupObserver ((r₁, k) :: (r₂, k) :: tail) q := by
  by_cases hq : q = k
  · subst hq
    simp [observerAliasStep, lookupObserver]
  · exact observerAlias_preserves_other r₁ r₂ k q hq tail

/--
Compress-idempotent checked slice: applying the same local same-observer compression
twice reaches the same local window as applying it once.  This proves only the
single-window law for equal observer-kind strings.
-/
theorem compressIdempotent_sameObserver_local_law
    (r₁ r₂ : Reg) (k : ObserverKind) (tail : List ObserverDecl) :
    compressObserverWindow
        (compressObserverWindow (ObserverWindow.adjacent (r₁, k) (r₂, k) tail)) =
      compressObserverWindow (ObserverWindow.adjacent (r₁, k) (r₂, k) tail) := by
  simp [compressObserverWindow]

/--
Visible-use checked slice: rewriting a local visible use from the candidate register
to its source register changes only the observed register and preserves the observer
register. This is only a local row for same-observer use contexts.
-/
theorem compressIdempotent_visibleUseObserver_local_law
    (candidate source : Reg) (use : VisibleUseDecl) :
    visibleUseObserver (rewriteVisibleUse candidate source use) = visibleUseObserver use := by
  cases use with
  | mk used observer =>
      by_cases h : used = candidate
      · simp [rewriteVisibleUse, visibleUseObserver, h]
      · simp [rewriteVisibleUse, visibleUseObserver, h]

/--
Different-observer checked slice: a local compress-idempotent window with different
observer kinds is left unchanged. This checks the rejection side of the local rule only.
-/
theorem compressIdempotent_differentObserver_reject_local_law
    (r₁ r₂ : Reg) (k₁ k₂ : ObserverKind) (tail : List ObserverDecl) (h : k₁ ≠ k₂) :
    compressObserverWindow (ObserverWindow.adjacent (r₁, k₁) (r₂, k₂) tail) =
      ObserverWindow.adjacent (r₁, k₁) (r₂, k₂) tail := by
  simp [compressObserverWindow, h]

/--
Obstruction-boundary checked slice: a local compress-idempotent candidate that feeds
obstruction evidence is kept visible rather than normalized away.
-/
theorem compressIdempotent_obstructionBoundary_reject_local_law
    (r₁ r₂ : Reg) (k : ObserverKind) (tail : List ObserverDecl) :
    compressObserverWindowWithEvidence true (ObserverWindow.adjacent (r₁, k) (r₂, k) tail) =
      ObserverWindow.adjacent (r₁, k) (r₂, k) tail := by
  simp [compressObserverWindowWithEvidence]

/--
Compress-alias checked slice: adjacent duplicate COMPRESS declarations with the same
source and observer registers preserve every local source/observer lookup and keep the
first destination as the representative for that queried pair.
-/
theorem compressAlias_samePair_local_law
    (dst₁ dst₂ src obs querySrc queryObs : Reg) (tail : List CompressDecl) :
    lookupCompress (compressAliasStep (dst₁, src, obs) (dst₂, src, obs) tail) querySrc queryObs =
      lookupCompress ((dst₁, src, obs) :: (dst₂, src, obs) :: tail) querySrc queryObs := by
  by_cases hSrc : src = querySrc
  · subst hSrc
    by_cases hObs : obs = queryObs
    · subst hObs
      simp [compressAliasStep, lookupCompress]
    · have hObsNe : obs ≠ queryObs := hObs
      simp [compressAliasStep, lookupCompress, hObsNe]
  · have hSrcNe : src ≠ querySrc := hSrc
    simp [compressAliasStep, lookupCompress, hSrcNe]

/--
Dead-shadow checked slice: dropping one unused local shadow declaration preserves
local shadow lookup for queried registers other than the dropped destination.
-/
theorem deadShadow_unusedLookup_local_law
    (dst query : Reg) (kind : ShadowKind) (tail : List ShadowDecl) (h : query ≠ dst) :
    lookupShadow (deadShadowDrop (dst, kind) tail) query =
      lookupShadow ((dst, kind) :: tail) query := by
  have hDstQuery : dst ≠ query := by
    intro hEq
    exact h hEq.symm
  simp [deadShadowDrop, lookupShadow, hDstQuery]

end Veyra
