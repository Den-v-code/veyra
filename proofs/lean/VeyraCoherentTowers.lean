/-
I1 formal boundary: `PrefixTower` is an all-natural-depth hypothesis.  The
finite Python windows do not construct this completed family.  The modular
result is the standard prime-power residue law, expressed as observer
restriction; no novelty, p-adic completion, or set-theoretic claim is made.
-/

set_option autoImplicit false

abbrev PrefixTower (α : Type) := (n : Nat) → Fin n → α

def PrefixCoherent {α : Type} (tower : PrefixTower α) : Prop :=
  ∀ {m n : Nat}, (h : m ≤ n) → (i : Fin m) →
    tower n (Fin.castLE h i) = tower m i

def PrefixTower.stream {α : Type} (tower : PrefixTower α) (n : Nat) : α :=
  tower (n + 1) ⟨n, Nat.lt_succ_self n⟩

def PrefixTower.Matches {α : Type} (tower : PrefixTower α)
    (stream : Nat → α) : Prop :=
  ∀ (n : Nat) (i : Fin n), stream i.val = tower n i

theorem THM_I1_001_prefix_tower_recovers_stream {α : Type}
    (tower : PrefixTower α) (coherent : PrefixCoherent tower) :
    tower.Matches tower.stream := by
  intro n i
  let j : Fin (i.val + 1) := ⟨i.val, Nat.lt_succ_self i.val⟩
  have h : i.val + 1 ≤ n := i.isLt
  have hr := coherent h j
  have hc : Fin.castLE h j = i := by
    apply Fin.ext
    rfl
  simpa [PrefixTower.stream, j, hc] using hr.symm

theorem THM_I1_002_prefix_observers_determine_stream {α : Type}
    (tower : PrefixTower α) (coherent : PrefixCoherent tower)
    (candidate : Nat → α) (hmatches : tower.Matches candidate) :
    candidate = tower.stream := by
  funext n
  let i : Fin (n + 1) := ⟨n, Nat.lt_succ_self n⟩
  have recoveredMatches : tower.Matches tower.stream :=
    THM_I1_001_prefix_tower_recovers_stream tower coherent
  calc
    candidate n = tower (n + 1) i := hmatches (n + 1) i
    _ = tower.stream n := (recoveredMatches (n + 1) i).symm

structure PrefixConflict {α : Type} (tower : PrefixTower α) where
  small : Nat
  large : Nat
  le : small ≤ large
  index : Fin small
  disagrees :
    tower large (Fin.castLE le index) ≠ tower small index

theorem THM_I1_003_prefix_conflict_blocks_global_stream {α : Type}
    (tower : PrefixTower α) (conflict : PrefixConflict tower) :
    ¬ ∃ stream : Nat → α, tower.Matches stream := by
  intro existsStream
  rcases existsStream with ⟨stream, hmatch⟩
  apply conflict.disagrees
  calc
    tower conflict.large (Fin.castLE conflict.le conflict.index) =
        stream conflict.index.val :=
      (hmatch conflict.large (Fin.castLE conflict.le conflict.index)).symm
    _ = tower conflict.small conflict.index :=
      hmatch conflict.small conflict.index

theorem THM_I1_004_modular_addition_preserves_refinement (p k aNext a bNext b : Nat)
    (ha : aNext % (p ^ (k + 1)) = a)
    (hb : bNext % (p ^ (k + 1)) = b) :
    ((aNext + bNext) % (p ^ (k + 2))) % (p ^ (k + 1)) =
      (a + b) % (p ^ (k + 1)) := by
  calc
    ((aNext + bNext) % (p ^ (k + 2))) % (p ^ (k + 1)) =
        (aNext + bNext) % (p ^ (k + 1)) :=
      Nat.mod_mod_of_dvd _ (Nat.pow_dvd_pow p (Nat.le_succ (k + 1)))
    _ =
        (aNext % (p ^ (k + 1)) + bNext % (p ^ (k + 1))) %
          (p ^ (k + 1)) := by
      rw [Nat.add_mod]
    _ = (a + b) % (p ^ (k + 1)) := by rw [ha, hb]
