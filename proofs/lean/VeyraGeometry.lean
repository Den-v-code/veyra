namespace Veyra

-- theorem-card: pythagorean-separation
-- Finite 3-4-5 separation shadow: the square on the hypotenuse equals the two leg squares.
theorem THM_G001_pythagorean_3_4_5 : (3 : Nat) * 3 + 4 * 4 = 5 * 5 := by
  rfl

-- theorem-card: sss-triangle
-- Fixed right triangle and its +10 coordinate shift have side-square triples 9/16/25.
theorem THM_G002_sss_side_squares_shift_10 :
    (((3 : Int) - 0) * (3 - 0) + (0 - 0) * (0 - 0) = 9 ∧
     (0 - 0) * (0 - 0) + (4 - 0) * (4 - 0) = 16 ∧
     ((0 : Int) - 3) * (0 - 3) + (4 - 0) * (4 - 0) = 25) ∧
    (((13 : Int) - 10) * (13 - 10) + (10 - 10) * (10 - 10) = 9 ∧
     (10 - 10) * (10 - 10) + (14 - 10) * (14 - 10) = 16 ∧
     ((10 : Int) - 13) * (10 - 13) + (14 - 10) * (14 - 10) = 25) := by
  decide

-- theorem-card: sas-triangle
-- Fixed perpendicular anchor vectors (3,0) and (0,4): squares 9/16 and dot 0.
theorem THM_G003_sas_anchor_3_4_dot_0 :
    (((3 : Int) - 0) * (3 - 0) + (0 - 0) * (0 - 0) = 9 ∧
     (0 - 0) * (0 - 0) + (4 - 0) * (4 - 0) = 16 ∧
     (3 - 0) * (0 - 0) + (0 - 0) * (4 - 0) = 0) ∧
    (((13 : Int) - 10) * (13 - 10) + (10 - 10) * (10 - 10) = 9 ∧
     (10 - 10) * (10 - 10) + (14 - 10) * (14 - 10) = 16 ∧
     (13 - 10) * (10 - 10) + (10 - 10) * (14 - 10) = 0) := by
  decide

-- theorem-card: line-shell-intersection
-- On (-10,0)->(10,0), t=1/4 and t=3/4 give x=-5 and x=5 on radius-square 25.
theorem THM_G004_diameter_shell_scaled_roots :
    ((-10 : Int) * 4 + 20 * 1 = (-5) * 4 ∧ (-5 : Int) * (-5) = 25) ∧
    ((-10 : Int) * 4 + 20 * 3 = 5 * 4 ∧ (5 : Int) * 5 = 25) := by
  decide

-- theorem-card: plane-relabel-composition
-- Quarter-turn after translation (1,-2) at (2,3): composed and sequential are both (-1,3).
theorem THM_G005_quarter_turn_after_translation :
    ((-((3 : Int) - 2), 2 + 1) = (-1, 3)) ∧
    ((-(1 : Int), 3) = (-1, 3)) ∧
    ((-((3 : Int) - 2), 2 + 1) = (-(1 : Int), 3)) := by
  decide

#check THM_G002_sss_side_squares_shift_10
#check THM_G003_sas_anchor_3_4_dot_0
#check THM_G004_diameter_shell_scaled_roots
#check THM_G005_quarter_turn_after_translation

end Veyra
