namespace Veyra

-- theorem-card: mean-balance
-- Fixed finite shadow only: the sample (1,3,5) has mean 3 and balanced deviations.
theorem THM_S001_mean_balance_1_3_5 :
    ((1 : Int) - 3) + (3 - 3) + (5 - 3) = 0 := by
  decide

#check THM_S001_mean_balance_1_3_5

-- theorem-card: variance-shift
-- Fixed samples only: variance numerators for (1,3,5) and (11,13,15) are both 8.
def varianceNumerator135 : Int :=
  (1 - 3) * (1 - 3) + (3 - 3) * (3 - 3) + (5 - 3) * (5 - 3)

def varianceNumerator111315 : Int :=
  (11 - 13) * (11 - 13) + (13 - 13) * (13 - 13) + (15 - 13) * (15 - 13)

theorem THM_S002_variance_shift_1_3_5_plus_10 :
    varianceNumerator135 = varianceNumerator111315 ∧
    varianceNumerator135 = 8 ∧ varianceNumerator111315 = 8 := by
  decide

#check THM_S002_variance_shift_1_3_5_plus_10

end Veyra
