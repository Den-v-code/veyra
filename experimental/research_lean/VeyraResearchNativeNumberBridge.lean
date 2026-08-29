import VeyraNativeSemantics
import VeyraEcho
import VeyraResearchFermatCorollary

set_option autoImplicit false

namespace Veyra

/-
Research-only carrier bridge for the existing native-number N1 line.

Claim:
* for any tact list that already evaluates to a ready native Mode, the native
  length observer returns exactly run.length;
* the same run.length is then fed to the already-stable THM-F002
  product-plus-one law;
* if that same run.length satisfies the local research Prime predicate, the
  existing general Fermat corollary applies to it.

Nonclaims:
* no prime generation or resonance-prime theory;
* no formalization of native unit-Breath construction, multiplicative orbits,
  or coverage from the executable F003 rows;
* no stable THM-F003 or R8/layer promotion;
* no claim that every native-number certificate is formally covered.
-/

theorem RESEARCH_NN_T001_ready_mode_length_euclid_escape
    (run : List VeyraTact) (readyMode : VeyraMode)
    (ready : evalMode run = .ready readyMode) (k : Nat) :
    observeMode .length run = some (.length run.length) ∧
      (run.length * k + 1) % run.length = 1 % run.length := by
  constructor
  · exact native_length_observes_ready_mode run readyMode ready
  · exact THM_F002_euclid_escape_mod run.length k

#print axioms RESEARCH_NN_T001_ready_mode_length_euclid_escape

theorem RESEARCH_NN_T002_ready_mode_prime_length_fermat
    (run : List VeyraTact) (readyMode : VeyraMode)
    (ready : evalMode run = .ready readyMode)
    (a : Nat) (hp : Prime run.length) (hpa : ¬ run.length ∣ a) :
    observeMode .length run = some (.length run.length) ∧
      a ^ (run.length - 1) % run.length = 1 := by
  constructor
  · exact native_length_observes_ready_mode run readyMode ready
  · exact RESEARCH_FC_T002_fermat_corollary_one run.length a hp hpa

#print axioms RESEARCH_NN_T002_ready_mode_prime_length_fermat

end Veyra
