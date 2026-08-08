/- Veyra P3-C1: ranked termination plus complete local joins imply generated finite confluence. -/

universe u

namespace VeyraGeneratedConfluence

inductive Path {α : Type u} (step : α → α → Prop) : α → α → Prop where
  | refl (x : α) : Path step x x
  | head {x y z : α} : step x y → Path step y z → Path step x z

namespace Path

variable {α : Type u} {step : α → α → Prop}

 theorem append {x y z : α} : Path step x y → Path step y z → Path step x z := by
  intro xy yz
  induction xy with
  | refl => exact yz
  | head edge tail ih => exact .head edge (ih yz)

 theorem rank_le (rank : α → Nat)
    (decreases : ∀ {x y}, step x y → rank y < rank x)
    {x y : α} (path : Path step x y) : rank y ≤ rank x := by
  induction path with
  | refl => exact Nat.le_refl _
  | head edge tail ih => exact Nat.le_trans ih (Nat.le_of_lt (decreases edge))

end Path

def Joinable {α : Type u} (step : α → α → Prop) (x y : α) : Prop :=
  ∃ w, Path step x w ∧ Path step y w

def LocallyJoinable {α : Type u} (step : α → α → Prop) : Prop :=
  ∀ {x y z}, step x y → step x z → Joinable step y z

def ConfluentFrom {α : Type u} (step : α → α → Prop) (x : α) : Prop :=
  ∀ {y z}, Path step x y → Path step x z → Joinable step y z

 theorem THM_P3C1_001_ranked_local_to_generated_confluence
    {α : Type u} (step : α → α → Prop) (rank : α → Nat)
    (decreases : ∀ {x y}, step x y → rank y < rank x)
    (localJoin : LocallyJoinable step) : ∀ x, ConfluentFrom step x := by
  intro root
  have proof : ∀ n x, rank x = n →
      ∀ {y z}, Path step x y → Path step x z → Joinable step y z :=
    fun n => Nat.strongRecOn n (fun bound ih x rankX => by
      intro y z xy xz
      cases xy with
      | refl => exact ⟨z, xz, .refl z⟩
      | @head _ y1 y edgeXY tailY =>
        cases xz with
        | refl => exact ⟨y, .refl y, .head edgeXY tailY⟩
        | @head _ z1 z edgeXZ tailZ =>
          obtain ⟨w, pathYW, pathZW⟩ := localJoin edgeXY edgeXZ
          have rankY : rank y1 < bound := rankX ▸ decreases edgeXY
          have rankZ : rank z1 < bound := rankX ▸ decreases edgeXZ
          have rankW : rank w < bound :=
            Nat.lt_of_le_of_lt (Path.rank_le rank decreases pathYW) rankY
          obtain ⟨q, pathYQ, pathWQ⟩ := ih (rank y1) rankY y1 rfl tailY pathYW
          obtain ⟨r, pathZR, pathWR⟩ := ih (rank z1) rankZ z1 rfl tailZ pathZW
          obtain ⟨t, pathQT, pathRT⟩ := ih (rank w) rankW w rfl pathWQ pathWR
          exact ⟨t, Path.append pathYQ pathQT, Path.append pathZR pathRT⟩)
  intro y z xy xz
  exact proof (rank root) root rfl xy xz

#print axioms THM_P3C1_001_ranked_local_to_generated_confluence

end VeyraGeneratedConfluence
