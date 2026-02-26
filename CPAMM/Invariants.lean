import CPAMM.Transitions

/-!
  CPAMM-1 Phase 2: Safety Invariants

  Show that transition relations preserve validity and LP accounting consistency.
-/

theorem valid_preserved_addLiquidity
    {α : Type*} [DecidableEq α] (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (ht : AddLiquidity s s' addr dx dy) :
    Valid s' := by
  rcases hv with ⟨hx, hy, hL_nonneg, hbal_nonneg, hf_nonneg, hf_lt_one⟩
  rcases ht with
    ⟨hdx_pos, hdy_pos, _, hx', hy', hL', hbal_addr', hbal_other', hf'⟩
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · linarith [hx', hx, hdx_pos]
  · linarith [hy', hy, hdy_pos]
  · by_cases hL0 : s.L = 0
    · have hL_eq : s'.L = dx := by simpa [hL0] using hL'
      linarith [hL_eq, hdx_pos]
    · have hterm_nonneg : 0 ≤ s.L * dx / s.x := by
        have : 0 ≤ s.L * dx := mul_nonneg hL_nonneg (le_of_lt hdx_pos)
        exact div_nonneg this (le_of_lt hx)
      have hL_eq : s'.L = s.L + s.L * dx / s.x := by simpa [hL0] using hL'
      linarith [hL_eq, hL_nonneg, hterm_nonneg]
  · intro a
    by_cases ha : a = addr
    · subst ha
      have hmint_nonneg : 0 ≤ s'.L - s.L := by
        by_cases hL0 : s.L = 0
        · have hL_eq : s'.L = dx := by simpa [hL0] using hL'
          linarith [hL_eq, hL0, hdx_pos]
        · have hterm_nonneg : 0 ≤ s.L * dx / s.x := by
            have : 0 ≤ s.L * dx := mul_nonneg hL_nonneg (le_of_lt hdx_pos)
            exact div_nonneg this (le_of_lt hx)
          have hL_eq : s'.L = s.L + s.L * dx / s.x := by simpa [hL0] using hL'
          linarith [hL_eq, hterm_nonneg]
      have hold_nonneg : 0 ≤ s.balances a := hbal_nonneg a
      linarith [hbal_addr', hold_nonneg, hmint_nonneg]
    · have hsame : s'.balances a = s.balances a := hbal_other' a ha
      linarith [hsame, hbal_nonneg a]
  · simpa [hf'] using hf_nonneg
  · simpa [hf'] using hf_lt_one

theorem valid_preserved_removeLiquidity
    {α : Type*} [DecidableEq α] (s s' : CpammState α) (addr : α) (dL : ℚ)
    (hv : Valid s)
    (ht : RemoveLiquidity s s' addr dL) :
    Valid s' := by
  rcases hv with ⟨hx, hy, hL_nonneg, hbal_nonneg, hf_nonneg, hf_lt_one⟩
  rcases ht with
    ⟨hdL_pos, hdL_le_bal, hdL_lt_L, hx', hy', hL', hbal_addr', hbal_other', hf'⟩
  have hL_pos : 0 < s.L := lt_trans hdL_pos hdL_lt_L
  have hfrac_lt_one : dL / s.L < 1 := by
    have : dL < 1 * s.L := by simpa using hdL_lt_L
    exact (div_lt_iff₀ hL_pos).2 this
  have hfactor_pos : 0 < 1 - dL / s.L := by linarith
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · have hx_eq : s'.x = s.x * (1 - dL / s.L) := by
      calc
        s'.x = s.x - s.x * dL / s.L := hx'
        _ = s.x * (1 - dL / s.L) := by ring
    have hx'_pos : 0 < s.x * (1 - dL / s.L) := mul_pos hx hfactor_pos
    linarith [hx_eq, hx'_pos]
  · have hy_eq : s'.y = s.y * (1 - dL / s.L) := by
      calc
        s'.y = s.y - s.y * dL / s.L := hy'
        _ = s.y * (1 - dL / s.L) := by ring
    have hy'_pos : 0 < s.y * (1 - dL / s.L) := mul_pos hy hfactor_pos
    linarith [hy_eq, hy'_pos]
  · have : 0 < s'.L := by linarith [hL', hdL_lt_L]
    exact le_of_lt this
  · intro a
    by_cases ha : a = addr
    · subst ha
      have hold_nonneg : 0 ≤ s.balances a := hbal_nonneg a
      linarith [hbal_addr', hold_nonneg, hdL_le_bal]
    · have hsame : s'.balances a = s.balances a := hbal_other' a ha
      linarith [hsame, hbal_nonneg a]
  · simpa [hf'] using hf_nonneg
  · simpa [hf'] using hf_lt_one

theorem valid_preserved_swapXforY
    {α : Type*} (s s' : CpammState α) (dx : ℚ)
    (hv : Valid s)
    (ht : SwapXforY s s' dx) :
    Valid s' := by
  rcases hv with ⟨hx, _, hL_nonneg, hbal_nonneg, hf_nonneg, hf_lt_one⟩
  rcases ht with
    ⟨hdx_pos, _, hx', hy', hy'_pos, hL', hbal', hf'⟩
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · linarith [hx', hx, hdx_pos]
  · exact hy'_pos
  · simpa [hL'] using hL_nonneg
  · intro a
    simpa [hbal'] using hbal_nonneg a
  · simpa [hf'] using hf_nonneg
  · simpa [hf'] using hf_lt_one

theorem valid_preserved_swapYforX
    {α : Type*} (s s' : CpammState α) (dy : ℚ)
    (hv : Valid s)
    (ht : SwapYforX s s' dy) :
    Valid s' := by
  rcases hv with ⟨_, hy, hL_nonneg, hbal_nonneg, hf_nonneg, hf_lt_one⟩
  rcases ht with
    ⟨hdy_pos, _, hy', hx', hx'_pos, hL', hbal', hf'⟩
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact hx'_pos
  · linarith [hy', hy, hdy_pos]
  · simpa [hL'] using hL_nonneg
  · intro a
    simpa [hbal'] using hbal_nonneg a
  · simpa [hf'] using hf_nonneg
  · simpa [hf'] using hf_lt_one

theorem consistent_preserved_addLiquidity
    {α : Type*} [DecidableEq α] [Fintype α]
    (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (hc : Consistent s)
    (ht : AddLiquidity s s' addr dx dy) :
    Consistent s' := by
  rcases hv with ⟨_, _, _, _, _, _⟩
  rcases ht with
    ⟨_, _, _, _, _, _, hbal_addr', hbal_other', _⟩
  unfold Consistent at hc ⊢
  let minted : ℚ := s'.L - s.L
  have hsum_bal :
      Finset.univ.sum s'.balances =
        Finset.univ.sum (fun a : α => s.balances a + (if a = addr then minted else (0 : ℚ))) := by
    refine Finset.sum_congr rfl ?_
    intro a _
    by_cases ha : a = addr
    · subst ha
      simp [minted, hbal_addr']
    · simp [minted, ha, hbal_other' a ha]
  have hsum_delta :
      Finset.univ.sum (fun a : α => if a = addr then minted else (0 : ℚ)) = minted := by
    simp
  have hsum_split :
      Finset.univ.sum (fun a : α => s.balances a + (if a = addr then minted else (0 : ℚ))) =
        Finset.univ.sum s.balances + Finset.univ.sum (fun a : α => if a = addr then minted else (0 : ℚ)) := by
    simp [Finset.sum_add_distrib]
  calc
    s'.L = s.L + minted := by simp [minted]
    _ = Finset.univ.sum s.balances + minted := by simp [hc]
    _ = Finset.univ.sum s.balances + Finset.univ.sum (fun a : α => if a = addr then minted else (0 : ℚ)) := by
      rw [hsum_delta]
    _ = Finset.univ.sum (fun a : α => s.balances a + (if a = addr then minted else (0 : ℚ))) := by
      symm
      exact hsum_split
    _ = Finset.univ.sum s'.balances := by
      symm
      exact hsum_bal

theorem consistent_preserved_removeLiquidity
    {α : Type*} [DecidableEq α] [Fintype α]
    (s s' : CpammState α) (addr : α) (dL : ℚ)
    (hv : Valid s)
    (hc : Consistent s)
    (ht : RemoveLiquidity s s' addr dL) :
    Consistent s' := by
  rcases hv with ⟨_, _, _, _, _, _⟩
  rcases ht with
    ⟨_, _, _, _, _, hL', hbal_addr', hbal_other', _⟩
  unfold Consistent at hc ⊢
  let burned : ℚ := -dL
  have hsum_bal :
      Finset.univ.sum s'.balances =
        Finset.univ.sum (fun a : α => s.balances a + (if a = addr then burned else (0 : ℚ))) := by
    refine Finset.sum_congr rfl ?_
    intro a _
    by_cases ha : a = addr
    · subst ha
      simpa [burned, sub_eq_add_neg] using hbal_addr'
    · simp [burned, ha, hbal_other' a ha]
  have hsum_delta :
      Finset.univ.sum (fun a : α => if a = addr then burned else (0 : ℚ)) = burned := by
    simp
  have hsum_split :
      Finset.univ.sum (fun a : α => s.balances a + (if a = addr then burned else (0 : ℚ))) =
        Finset.univ.sum s.balances + Finset.univ.sum (fun a : α => if a = addr then burned else (0 : ℚ)) := by
    simp [Finset.sum_add_distrib]
  calc
    s'.L = s.L + burned := by
      simpa [burned, sub_eq_add_neg] using hL'
    _ = Finset.univ.sum s.balances + burned := by simp [hc]
    _ = Finset.univ.sum s.balances + Finset.univ.sum (fun a : α => if a = addr then burned else (0 : ℚ)) := by
      rw [hsum_delta]
    _ = Finset.univ.sum (fun a : α => s.balances a + (if a = addr then burned else (0 : ℚ))) := by
      symm
      exact hsum_split
    _ = Finset.univ.sum s'.balances := by
      symm
      exact hsum_bal
