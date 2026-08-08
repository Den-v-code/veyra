/- P3-C2: generated typed-setoid transport coherence and separate symbolic Nat-op reduction. -/
import Std.Tactic

universe u v
namespace VeyraTransportCoherence

inductive Path {α : Type u} (step : α → α → Prop) : α → α → Type u where
  | refl (x : α) : Path step x x
  | head {x y z : α} : step x y → Path step y z → Path step x z

namespace Path
variable {α : Type u} {step : α → α → Prop}

def append {x y z : α} : Path step x y → Path step y z → Path step x z
  | .refl _, yz => yz
  | .head edge tail, yz => .head edge (append tail yz)

theorem rank_le (rank : α → Nat)
    (decreases : ∀ {x y}, step x y → rank y < rank x)
    {x y : α} (path : Path step x y) : rank y ≤ rank x := by
  induction path with
  | refl => exact Nat.le_refl _
  | head edge _ ih => exact Nat.le_trans ih (Nat.le_of_lt (decreases edge))
end Path

variable {α : Type u} {step : α → α → Prop} {carrier : α → Type v}

def transport (edgeMap : ∀ {x y}, step x y → carrier x → carrier y) :
    ∀ {x y}, Path step x y → carrier x → carrier y
  | _, _, .refl _ => id
  | _, _, .head edge tail => (transport edgeMap tail) ∘ edgeMap edge

theorem transport_append (edgeMap : ∀ {x y}, step x y → carrier x → carrier y)
    {x y z} (p : Path step x y) (q : Path step y z) :
    ∀ a, transport (carrier := carrier) edgeMap (Path.append p q) a =
      transport (carrier := carrier) edgeMap q
        (transport (carrier := carrier) edgeMap p a) := by
  induction p with
  | refl => intro a; rfl
  | head edge tail ih =>
      intro a
      exact ih q (edgeMap edge a)

theorem transport_respects (setoid : ∀ x, Setoid (carrier x))
    (edgeMap : ∀ {x y}, step x y → carrier x → carrier y)
    (edgeRespect : ∀ {x y} (e : step x y) {a b},
      (setoid x).r a b → (setoid y).r (edgeMap e a) (edgeMap e b))
    {x y} (p : Path step x y) {a b} :
    (setoid x).r a b →
      (setoid y).r (transport (carrier := carrier) edgeMap p a)
        (transport (carrier := carrier) edgeMap p b) := by
  intro related
  induction p with
  | refl => exact related
  | head edge tail ih => exact ih (edgeRespect edge related)

def Commutes (setoid : ∀ x, Setoid (carrier x))
    (edgeMap : ∀ {x y}, step x y → carrier x → carrier y)
    {x y z} (p : Path step x y) (q : Path step x z) : Prop :=
  ∃ (t : α) (a : Path step y t) (b : Path step z t), ∀ value,
    (setoid t).r
      (transport (carrier := carrier) edgeMap a
        (transport (carrier := carrier) edgeMap p value))
      (transport (carrier := carrier) edgeMap b
        (transport (carrier := carrier) edgeMap q value))

def LocalCommutes (setoid : ∀ x, Setoid (carrier x))
    (edgeMap : ∀ {x y}, step x y → carrier x → carrier y) : Prop :=
  ∀ {x y z} (e : step x y) (f : step x z),
    ∃ (w : α) (a : Path step y w) (b : Path step z w), ∀ value,
      (setoid w).r (transport (carrier := carrier) edgeMap a (edgeMap e value))
        (transport (carrier := carrier) edgeMap b (edgeMap f value))

theorem THM_P3C2_001_ranked_local_to_generated_transport
    (setoid : ∀ x, Setoid (carrier x))
    (edgeMap : ∀ {x y}, step x y → carrier x → carrier y)
    (edgeRespect : ∀ {x y} (e : step x y) {a b},
      (setoid x).r a b → (setoid y).r (edgeMap e a) (edgeMap e b))
    (rank : α → Nat)
    (decreases : ∀ {x y}, step x y → rank y < rank x)
    (localSquare : LocalCommutes setoid edgeMap) :
    ∀ x y z (p : Path step x y) (q : Path step x z), Commutes setoid edgeMap p q := by
  intro root
  have proof : ∀ n x, rank x = n →
      ∀ y z (p : Path step x y) (q : Path step x z), Commutes setoid edgeMap p q :=
    fun n => Nat.strongRecOn n (fun bound ih x rankX => by
      intro y z p q
      cases p with
      | refl => exact ⟨z, q, .refl z, fun value => (setoid z).refl _⟩
      | @head _ y1 y edgeY tailY =>
        cases q with
        | refl => exact ⟨y, .refl y, .head edgeY tailY, fun value => (setoid y).refl _⟩
        | @head _ z1 z edgeZ tailZ =>
          obtain ⟨w, pathYW, pathZW, localEq⟩ := localSquare edgeY edgeZ
          have rankY : rank y1 < bound := rankX ▸ decreases edgeY
          have rankZ : rank z1 < bound := rankX ▸ decreases edgeZ
          have rankW : rank w < bound :=
            Nat.lt_of_le_of_lt (Path.rank_le rank decreases pathYW) rankY
          obtain ⟨u, pathYU, pathWU, eqY⟩ :=
            ih (rank y1) rankY y1 rfl y w tailY pathYW
          obtain ⟨v, pathZV, pathWV, eqZ⟩ :=
            ih (rank z1) rankZ z1 rfl z w tailZ pathZW
          obtain ⟨t, pathUT, pathVT, eqW⟩ :=
            ih (rank w) rankW w rfl u v pathWU pathWV
          refine ⟨t, Path.append pathYU pathUT, Path.append pathZV pathVT, ?_⟩
          intro value
          simp only [transport_append]
          have h1 := transport_respects setoid edgeMap edgeRespect pathUT
            (eqY (edgeMap edgeY value))
          have h2 := transport_respects setoid edgeMap edgeRespect pathUT
            (transport_respects setoid edgeMap edgeRespect pathWU (localEq value))
          have h3 := eqW
            (transport (carrier := carrier) edgeMap pathZW (edgeMap edgeZ value))
          have h4 := transport_respects setoid edgeMap edgeRespect pathVT
            ((setoid v).symm (eqZ (edgeMap edgeZ value)))
          exact (setoid t).trans h1 ((setoid t).trans h2 ((setoid t).trans h3 h4))
      )
  intro y z p q
  exact proof (rank root) root rfl y z p q

namespace NatOp

def modulus (p n : Nat) : Nat := p ^ (n + 1)

theorem modulus_pos {p : Nat} (hp : 2 ≤ p) (n : Nat) : 0 < modulus p n :=
  Nat.pow_pos (Nat.zero_lt_of_lt hp)

def ZMod (p n : Nat) := Fin (modulus p n)

def reduce {p : Nat} (hp : 2 ≤ p) {m n : Nat} (_h : m ≤ n)
    (x : ZMod p n) : ZMod p m :=
  ⟨x.val % modulus p m, Nat.mod_lt _ (modulus_pos hp m)⟩

theorem modulus_dvd (p : Nat) {m n : Nat} (h : m ≤ n) : modulus p m ∣ modulus p n :=
  Nat.pow_dvd_pow p (Nat.add_le_add_right h 1)

theorem THM_P3C2_002_natop_reduction_identity {p : Nat} (hp : 2 ≤ p)
    (n : Nat) (x : ZMod p n) : reduce hp (Nat.le_refl n) x = x := by
  apply Fin.ext
  exact Nat.mod_eq_of_lt x.isLt

theorem THM_P3C2_003_natop_reduction_composition {p : Nat} (hp : 2 ≤ p)
    {k m n : Nat} (hkm : k ≤ m) (hmn : m ≤ n) (x : ZMod p n) :
    reduce hp hkm (reduce hp hmn x) = reduce hp (Nat.le_trans hkm hmn) x := by
  apply Fin.ext
  exact Nat.mod_mod_of_dvd x.val (modulus_dvd p hkm)

end NatOp

#print axioms THM_P3C2_001_ranked_local_to_generated_transport
#print axioms NatOp.THM_P3C2_002_natop_reduction_identity
#print axioms NatOp.THM_P3C2_003_natop_reduction_composition
end VeyraTransportCoherence
