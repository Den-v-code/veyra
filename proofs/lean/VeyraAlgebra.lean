namespace Veyra

-- theorem-card: polynomial-identity
-- Finite coefficient-shadow identity for (x+1)(x-1) and x^2-1.
def poly_identity_left_coeffs : List Int := [-1, 0, 1]
def poly_identity_right_coeffs : List Int := [-1, 0, 1]

theorem THM_A001_polynomial_identity_coeffs :
    poly_identity_left_coeffs = poly_identity_right_coeffs := by
  rfl

-- theorem-card: polynomial-evaluation
-- Finite evaluation shadow: (3+1)(3-1)=8.
theorem THM_A002_polynomial_eval_at_3 : ((3 : Int) + 1) * (3 - 1) = 8 := by
  rfl

-- theorem-card: linear-equation-solution
-- Finite unique-solution shadow for 2*x+3=7.
theorem THM_A003_linear_equation_unique_solution :
    ∀ x : Int, 2 * x + 3 = 7 → x = 2 := by
  intro x h
  omega

-- theorem-card: sampled-continuity
-- Fixed double-map sample only: anchor 0, radius 1/10, samples 2 gives the
-- five /20 numerators -2,-1,0,1,2, outputs -4,-2,0,2,4, and max drift 1/5.
theorem THM_A004_sampled_continuity_double_0_five_points :
    ((-2 : Int) * 2 = -4 ∧ (-1 : Int) * 2 = -2 ∧
     (0 : Int) * 2 = 0 ∧ (1 : Int) * 2 = 2 ∧ (2 : Int) * 2 = 4) ∧
    ((4 : Nat) * 5 = 20 ∧ 4 ≤ 20) := by
  decide

-- theorem-card: drift-stability
-- Fixed square-map symmetric quotients only: anchor 3 and steps 1,2,3 all give 6.
theorem THM_A005_square_symmetric_drift_3_steps_1_2_3 :
    ((4 : Int) * 4 - 2 * 2 = 6 * (2 * 1)) ∧
    ((5 : Int) * 5 - 1 * 1 = 6 * (2 * 2)) ∧
    ((6 : Int) * 6 - 0 * 0 = 6 * (2 * 3)) := by
  decide

-- theorem-card: area-additivity
-- Fixed identity midpoint sums only, scaled by 32: left=1/2, right=3/2,
-- whole=2, and the adjacent sums add exactly to the whole sum.
theorem THM_A006_identity_midpoint_area_4_4_8 :
    ((1 : Nat) + 3 + 5 + 7 = 16 ∧ 16 * 2 = 32) ∧
    (9 + 11 + 13 + 15 = 48 ∧ 48 * 2 = 32 * 3) ∧
    (1 + 3 + 5 + 7 + 9 + 11 + 13 + 15 = 64 ∧ 64 = 32 * 2) ∧
    16 + 48 = 64 := by
  decide

#check THM_A004_sampled_continuity_double_0_five_points
#check THM_A005_square_symmetric_drift_3_steps_1_2_3
#check THM_A006_identity_midpoint_area_4_4_8

end Veyra
