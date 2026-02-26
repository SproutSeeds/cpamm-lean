import CPAMM.Economics

/-!
  CPAMM-1 Phase 5: Rounding Bounds
-/

/-- Floor division underestimates the exact rational result. -/
theorem nat_div_le_rat_div (a b : ℕ) (hb : 0 < b) :
    (a / b : ℕ) ≤ (a : ℚ) / (b : ℚ) := by
  have _ : 0 < (b : ℚ) := by exact_mod_cast hb
  exact (Nat.cast_div_le (m := a) (n := b) (α := ℚ))

/-- Floor division is within 1 of the exact rational result. -/
theorem rat_div_sub_one_lt_nat_div (a b : ℕ) (hb : 0 < b) :
    (a : ℚ) / (b : ℚ) - 1 < (a / b : ℕ) := by
  have hbq_pos : 0 < (b : ℚ) := by exact_mod_cast hb
  have hbq_ne : (b : ℚ) ≠ 0 := ne_of_gt hbq_pos
  have hmod_lt : (a % b : ℕ) < b := Nat.mod_lt a hb
  have hdiv_decomp :
      (a : ℚ) / (b : ℚ) =
        (a / b : ℕ) + (a % b : ℕ) / (b : ℚ) := by
    have hnat : b * (a / b) + (a % b) = a := Nat.div_add_mod a b
    have hnatQ : (b : ℚ) * (a / b : ℕ) + (a % b : ℕ) = (a : ℚ) := by
      exact_mod_cast hnat
    calc
      (a : ℚ) / (b : ℚ) = ((b : ℚ) * (a / b : ℕ) + (a % b : ℕ)) / (b : ℚ) := by
        rw [hnatQ]
      _ = (a / b : ℕ) + (a % b : ℕ) / (b : ℚ) := by
        field_simp [hbq_ne]
  have hmod_frac_lt_one : (a % b : ℕ) / (b : ℚ) < 1 := by
    have hmod_cast_lt : ((a % b : ℕ) : ℚ) < (b : ℚ) := by exact_mod_cast hmod_lt
    exact (div_lt_one hbq_pos).2 hmod_cast_lt
  have hdiv_lt_succ : (a : ℚ) / (b : ℚ) < (a / b : ℕ) + 1 := by
    rw [hdiv_decomp]
    linarith [hmod_frac_lt_one]
  linarith [hdiv_lt_succ]

/-- Floor rounding on output preserves positive reserves:
    if `dy_floor = dy_of_swap` rounded down, then `reserveY - dy_floor > 0`. -/
theorem reserves_positive_under_rounding
    (x y f dx : ℚ) (hx : x > 0) (hy : y > 0) (_hf : 0 ≤ f) (hf1 : f < 1)
    (hdx : dx > 0)
    (dy_floor : ℕ)
    (h_floor : (dy_floor : ℚ) ≤ dy_of_swap x y f dx) :
    y - dy_floor > 0 := by
  have h_one_sub_pos : 0 < 1 - f := by linarith [hf1]
  have hdx_eff_pos : 0 < dx * (1 - f) := mul_pos hdx h_one_sub_pos
  have hdx_eff_lt_den : dx * (1 - f) < x + dx * (1 - f) := by linarith [hx]
  have hden_pos : 0 < x + dx * (1 - f) := by linarith [hx, hdx_eff_pos]
  have hdy_lt_y :
      dy_of_swap x y f dx < y := by
    unfold dy_of_swap
    have hmul_lt : y * (dx * (1 - f)) < y * (x + dx * (1 - f)) :=
      mul_lt_mul_of_pos_left hdx_eff_lt_den hy
    exact (div_lt_iff₀ hden_pos).2 hmul_lt
  have hdy_floor_lt_y : (dy_floor : ℚ) < y := lt_of_le_of_lt h_floor hdy_lt_y
  linarith [hdy_floor_lt_y]
