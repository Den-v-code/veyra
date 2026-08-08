import VeyraPadicLocalRealization

set_option autoImplicit false

/-- Owned all-depth premise bound to two N3 witnesses of one exact family. -/
theorem THM_P3N4_PREMISE_001_same_integer_coordinates {p : Nat}
    {hp : VeyraPrimeWitness p} {z : Int} {x y : ZpVeyra hp}
    (hx : forall n, veyraRho n x = (veyraIntegerFamily hp z).val n)
    (hy : forall n, veyraRho n y = (veyraIntegerFamily hp z).val n) :
    forall n, veyraRho n x = veyraRho n y :=
  fun n => (hx n).trans (hy n).symm

#print axioms THM_P3N4_PREMISE_001_same_integer_coordinates
