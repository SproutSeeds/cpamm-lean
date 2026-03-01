import Mathlib

/-!
  Protocol Template: Rounding Surface Skeleton

  Use this file to mirror each `floor_div`/quantization surface from
  `System.json.transitions[].update_model.rounding[]` into explicit theorem
  obligations.
-/

/-- Generic floor-div lower-bound pattern: floor never exceeds exact quotient. -/
theorem nat_div_le_rat_div_template (a b : Nat) (hb : 0 < b) :
    (a / b : Nat) ≤ (a : ℚ) / (b : ℚ) := by
  have _ : 0 < (b : ℚ) := by exact_mod_cast hb
  exact (Nat.cast_div_le (m := a) (n := b) (α := ℚ))

/-- Generic floor-div upper-gap pattern: floor is within `1` of exact quotient. -/
theorem rat_div_sub_one_lt_nat_div_template (a b : Nat) (hb : 0 < b) :
    (a : ℚ) / (b : ℚ) - 1 < (a / b : Nat) := by
  have hbq_pos : 0 < (b : ℚ) := by exact_mod_cast hb
  have hmod_lt : (a % b : Nat) < b := Nat.mod_lt a hb
  have hdiv_decomp :
      (a : ℚ) / (b : ℚ) =
        (a / b : Nat) + (a % b : Nat) / (b : ℚ) := by
    have hnat : b * (a / b) + (a % b) = a := Nat.div_add_mod a b
    have hnatQ : (b : ℚ) * (a / b : Nat) + (a % b : Nat) = (a : ℚ) := by
      exact_mod_cast hnat
    calc
      (a : ℚ) / (b : ℚ) = ((b : ℚ) * (a / b : Nat) + (a % b : Nat)) / (b : ℚ) := by
        rw [hnatQ]
      _ = (a / b : Nat) + (a % b : Nat) / (b : ℚ) := by
        field_simp [ne_of_gt hbq_pos]
  have hmod_frac_lt_one : (a % b : Nat) / (b : ℚ) < 1 := by
    have hmod_cast_lt : ((a % b : Nat) : ℚ) < (b : ℚ) := by exact_mod_cast hmod_lt
    exact (div_lt_one hbq_pos).2 hmod_cast_lt
  have hdiv_lt_succ : (a : ℚ) / (b : ℚ) < (a / b : Nat) + 1 := by
    rw [hdiv_decomp]
    linarith [hmod_frac_lt_one]
  linarith [hdiv_lt_succ]

/-!
  Engagement checklist pattern:

  For each `rounding` surface in `System.json` where
  `type = "floor_div"`:
  1. Introduce a concrete output definition over Nat arithmetic.
  2. Prove floor-underestimation and within-1 bounds.
  3. Prove downstream safety impact bounds (positivity, no-overdraw, etc.).

  Example mapping:
  - `rounding[].id = "swap_floor_div"` ->
    theorems similar to `nat_div_le_rat_div_template` and
    `rat_div_sub_one_lt_nat_div_template`,
    then a protocol-specific reserve/output safety theorem.
-/
