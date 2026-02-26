import CPAMM.Invariants

/-!
  CPAMM-1 Phase 3: Economic Theorems
-/

theorem product_preserved_swap_no_fee
    {α : Type*} (s s' : CpammState α) (dx : ℚ)
    (hv : Valid s)
    (hf : s.f = 0)
    (ht : SwapXforY s s' dx) :
    product s' = product s := by
  rcases hv with ⟨hx, hy, _, _, _, _⟩
  rcases ht with
    ⟨hdx_pos, _, hx', hy', _, _, _, _⟩
  have hden_pos : 0 < s.x + dx := by linarith
  have hden_ne : s.x + dx ≠ 0 := ne_of_gt hden_pos
  calc
    product s' = (s.x + dx) * (s.y - dy_of_swap s.x s.y 0 dx) := by
      simp [product, hx', hy', hf]
    _ = s.x * s.y := by
      simp [dy_of_swap]
      field_simp [hden_ne]
      ring
    _ = product s := by simp [product]

theorem product_nondecreasing_swap_with_fee
    {α : Type*} (s s' : CpammState α) (dx : ℚ)
    (hv : Valid s)
    (hf : s.f > 0)
    (ht : SwapXforY s s' dx) :
    product s' ≥ product s := by
  rcases hv with ⟨hx, hy, _, _, hf_nonneg, hf_lt_one⟩
  rcases ht with
    ⟨hdx_pos, _, hx', hy', _, _, _, _⟩
  let den : ℚ := s.x + dx * (1 - s.f)
  have h_one_sub_pos : 0 < 1 - s.f := by linarith
  have hdx_eff_pos : 0 < dx * (1 - s.f) := mul_pos hdx_pos h_one_sub_pos
  have hden_pos : 0 < den := by
    unfold den
    linarith [hx, hdx_eff_pos]
  have hden_ne : den ≠ 0 := ne_of_gt hden_pos
  have hdx_eff_lt_dx : dx * (1 - s.f) < dx := by
    have h_one_sub_lt_one : 1 - s.f < 1 := by linarith [hf]
    have : dx * (1 - s.f) < dx * 1 := mul_lt_mul_of_pos_left h_one_sub_lt_one hdx_pos
    simpa using this
  have hden_le_num : den ≤ s.x + dx := by
    unfold den
    linarith [hdx_eff_lt_dx]
  have hratio_ge_one : 1 ≤ (s.x + dx) / den := (one_le_div hden_pos).2 hden_le_num
  have hprod_nonneg : 0 ≤ s.x * s.y := le_of_lt (mul_pos hx hy)
  have hscaled :
      s.x * s.y ≤ s.x * s.y * ((s.x + dx) / den) := by
    simpa [one_mul] using (mul_le_mul_of_nonneg_left hratio_ge_one hprod_nonneg)
  have hprod_formula :
      product s' = s.x * s.y * ((s.x + dx) / den) := by
    calc
      product s' = (s.x + dx) * (s.y - dy_of_swap s.x s.y s.f dx) := by
        simp [product, hx', hy']
      _ = s.x * s.y * ((s.x + dx) / den) := by
        unfold den
        simp [dy_of_swap]
        field_simp [hden_ne]
        ring
  calc
    product s = s.x * s.y := by simp [product]
    _ ≤ s.x * s.y * ((s.x + dx) / den) := hscaled
    _ = product s' := by simp [hprod_formula]

theorem output_bounded_by_reserve
    {α : Type*} (s s' : CpammState α) (dx : ℚ)
    (hv : Valid s)
    (ht : SwapXforY s s' dx) :
    s.y - s'.y < s.y := by
  rcases hv with ⟨_, _, _, _, _, _⟩
  rcases ht with
    ⟨_, _, _, _, hy'_pos, _, _, _⟩
  linarith

theorem remove_liquidity_proportional
    {α : Type*} [DecidableEq α] (s s' : CpammState α) (addr : α) (dL : ℚ)
    (hv : Valid s)
    (ht : RemoveLiquidity s s' addr dL) :
    (s.x - s'.x) / s.x = (s.y - s'.y) / s.y := by
  rcases hv with ⟨hx, hy, _, _, _, _⟩
  rcases ht with
    ⟨_, _, _, hx', hy', _, _, _, _⟩
  have hx_ne : s.x ≠ 0 := ne_of_gt hx
  have hy_ne : s.y ≠ 0 := ne_of_gt hy
  have hxdiff : s.x - s'.x = s.x * dL / s.L := by linarith [hx']
  have hydiff : s.y - s'.y = s.y * dL / s.L := by linarith [hy']
  calc
    (s.x - s'.x) / s.x = (s.x * dL / s.L) / s.x := by rw [hxdiff]
    _ = dL / s.L := by
      field_simp [hx_ne]
    _ = (s.y * dL / s.L) / s.y := by
      field_simp [hy_ne]
    _ = (s.y - s'.y) / s.y := by rw [hydiff]
