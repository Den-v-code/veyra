import VeyraPrimePowerProductiveBridge

set_option autoImplicit false

/-- Output of the closed negative-only offset pressure program. -/
def veyraOffsetProgramOutput {p : Nat} (hp : VeyraPrimeWitness p)
    (z offset : Int) (n : Nat) : VeyraZMod hp n :=
  veyraResidueProgramOutput hp (z + offset) n

/-- Operational semantics of the closed offset pressure program. -/
def veyraOffsetProgramEval {p : Nat} (hp : VeyraPrimeWitness p)
    (z offset : Int) (n : Nat) (r : VeyraZMod hp n) : Prop :=
  veyraResidueProgramEval hp (z + offset) n r

theorem THM_P3A1B_PRESSURE_001_total {p : Nat} (hp : VeyraPrimeWitness p)
    (z offset : Int) : forall n, exists r : VeyraZMod hp n,
      veyraOffsetProgramEval hp z offset n r := by
  exact THM_P3A1B_001_total hp (z + offset)

theorem THM_P3A1B_PRESSURE_002_coherent {p : Nat}
    (hp : VeyraPrimeWitness p) (z offset : Int) (m n : Nat) (h : m <= n)
    (r : VeyraZMod hp n) (s : VeyraZMod hp m) :
    veyraOffsetProgramEval hp z offset n r ->
      veyraOffsetProgramEval hp z offset m s -> veyraReduce hp h r = s := by
  exact THM_P3A1B_003_process_coherent hp (z + offset) m n h r s

#print axioms THM_P3A1B_PRESSURE_001_total
#print axioms THM_P3A1B_PRESSURE_002_coherent
