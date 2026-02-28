import CPAMM.Rounding

/-!
  CPAMM-1 Phase 6: Refinement Layer

  The Solidity relations below model integer arithmetic directly.
  For swaps, simulation is to bounded floor-rounded abstract relations.
-/

/-- A concrete address type for Solidity refinement proofs. -/
abbrev SolAddress := ℕ

/-- Lean model of Solidity contract storage. -/
structure SolidityStorage where
  reserveX : ℕ
  reserveY : ℕ
  totalSupply : ℕ
  balanceOf : SolAddress → ℕ
  feeNumerator : ℕ
  feeDenominator : ℕ
  h_denom_pos : 0 < feeDenominator

/-- Solidity fee interpreted in rationals. -/
def solidityFee (σ : SolidityStorage) : ℚ :=
  (σ.feeNumerator : ℚ) / (σ.feeDenominator : ℚ)

/-- Effective input amount after fee under integer arithmetic. -/
def inputEff (σ : SolidityStorage) (amount : ℕ) : ℕ :=
  amount * (σ.feeDenominator - σ.feeNumerator) / σ.feeDenominator

/-- Solidity output for `swapXforY` under integer arithmetic. -/
def dyOutX (σ : SolidityStorage) (dx : ℕ) : ℕ :=
  σ.reserveY * inputEff σ dx / (σ.reserveX + inputEff σ dx)

/-- Solidity output for `swapYforX` under integer arithmetic. -/
def dxOutY (σ : SolidityStorage) (dy : ℕ) : ℕ :=
  σ.reserveX * inputEff σ dy / (σ.reserveY + inputEff σ dy)

/-- LP shares minted by Solidity under integer arithmetic. -/
def mintedShares (σ : SolidityStorage) (dx : ℕ) : ℕ :=
  if σ.totalSupply = 0 then dx
  else σ.totalSupply * dx / σ.reserveX

/-- X reserve returned on removeLiquidity under integer arithmetic. -/
def removeX (σ : SolidityStorage) (shares : ℕ) : ℕ :=
  σ.reserveX * shares / σ.totalSupply

/-- Y reserve returned on removeLiquidity under integer arithmetic. -/
def removeY (σ : SolidityStorage) (shares : ℕ) : ℕ :=
  σ.reserveY * shares / σ.totalSupply

/-- Abstraction map from Solidity storage to abstract CPAMM state. -/
def alpha (σ : SolidityStorage) : CpammState SolAddress :=
  { x := (σ.reserveX : ℚ)
    y := (σ.reserveY : ℚ)
    L := (σ.totalSupply : ℚ)
    balances := fun a => (σ.balanceOf a : ℚ)
    f := solidityFee σ }

/-- Abstract swapXforY relation with floor-rounded output bounded by the exact model output. -/
def SwapXforYFloor {α : Type*} (s s' : CpammState α) (dx : ℚ) : Prop :=
  dx > 0 ∧
  ∃ dyFloor : ℕ,
    (dyFloor : ℚ) > 0 ∧
    (dyFloor : ℚ) ≤ dy_of_swap s.x s.y s.f dx ∧
    s'.x = s.x + dx ∧
    s'.y = s.y - dyFloor ∧
    s'.y > 0 ∧
    s'.L = s.L ∧
    s'.balances = s.balances ∧
    s'.f = s.f

/-- Abstract swapYforX relation with floor-rounded output bounded by the exact model output. -/
def SwapYforXFloor {α : Type*} (s s' : CpammState α) (dy : ℚ) : Prop :=
  dy > 0 ∧
  ∃ dxFloor : ℕ,
    (dxFloor : ℚ) > 0 ∧
    (dxFloor : ℚ) ≤ dy_of_swap s.y s.x s.f dy ∧
    s'.y = s.y + dy ∧
    s'.x = s.x - dxFloor ∧
    s'.x > 0 ∧
    s'.L = s.L ∧
    s'.balances = s.balances ∧
    s'.f = s.f

/-- Abstract addLiquidity relation with floor-bounded LP minting. -/
def AddLiquidityFloor {α : Type*} [DecidableEq α]
    (s s' : CpammState α) (addr : α) (dx dy : ℚ) : Prop :=
  dx > 0 ∧
  dy > 0 ∧
  (s.L > 0 → dx * s.y = dy * s.x) ∧
  s'.x = s.x + dx ∧
  s'.y = s.y + dy ∧
  (if s.L = 0 then s'.L = dx
   else s'.L ≤ s.L + s.L * dx / s.x ∧ s'.L > s.L + s.L * dx / s.x - 1) ∧
  s'.balances addr = s.balances addr + (s'.L - s.L) ∧
  (∀ a : α, a ≠ addr → s'.balances a = s.balances a) ∧
  s'.f = s.f

/-- Abstract removeLiquidity relation with floor-bounded reserve outputs. -/
def RemoveLiquidityFloor {α : Type*} [DecidableEq α]
    (s s' : CpammState α) (addr : α) (dL : ℚ) : Prop :=
  0 < dL ∧
  dL ≤ s.balances addr ∧
  dL < s.L ∧
  ∃ outX outY : ℕ,
    (outX : ℚ) ≤ s.x * dL / s.L ∧
    s.x * dL / s.L - 1 < (outX : ℚ) ∧
    (outY : ℚ) ≤ s.y * dL / s.L ∧
    s.y * dL / s.L - 1 < (outY : ℚ) ∧
    s'.x = s.x - outX ∧
    s'.y = s.y - outY ∧
    s'.x > 0 ∧
    s'.y > 0 ∧
    s'.L = s.L - dL ∧
    s'.balances addr = s.balances addr - dL ∧
    (∀ a : α, a ≠ addr → s'.balances a = s.balances a) ∧
    s'.f = s.f

/-- Solidity swapXforY relation (integer floor arithmetic). -/
def SoliditySwapXforY (σ σ' : SolidityStorage) (dx : ℕ) : Prop :=
  dx > 0 ∧
  inputEff σ dx > 0 ∧
  dyOutX σ dx > 0 ∧
  dyOutX σ dx < σ.reserveY ∧
  σ'.reserveX = σ.reserveX + dx ∧
  σ'.reserveY = σ.reserveY - dyOutX σ dx ∧
  σ'.totalSupply = σ.totalSupply ∧
  σ'.balanceOf = σ.balanceOf ∧
  σ'.feeNumerator = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator

/-- Solidity swapYforX relation (integer floor arithmetic). -/
def SoliditySwapYforX (σ σ' : SolidityStorage) (dy : ℕ) : Prop :=
  dy > 0 ∧
  inputEff σ dy > 0 ∧
  dxOutY σ dy > 0 ∧
  dxOutY σ dy < σ.reserveX ∧
  σ'.reserveY = σ.reserveY + dy ∧
  σ'.reserveX = σ.reserveX - dxOutY σ dy ∧
  σ'.totalSupply = σ.totalSupply ∧
  σ'.balanceOf = σ.balanceOf ∧
  σ'.feeNumerator = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator

/-- Solidity addLiquidity relation (integer floor arithmetic). -/
def SolidityAddLiquidity (σ σ' : SolidityStorage) (addr : SolAddress) (dx dy : ℕ) : Prop :=
  dx > 0 ∧
  dy > 0 ∧
  (σ.totalSupply > 0 → dx * σ.reserveY = dy * σ.reserveX) ∧
  mintedShares σ dx > 0 ∧
  σ'.reserveX = σ.reserveX + dx ∧
  σ'.reserveY = σ.reserveY + dy ∧
  σ'.totalSupply = σ.totalSupply + mintedShares σ dx ∧
  σ'.balanceOf addr = σ.balanceOf addr + mintedShares σ dx ∧
  (∀ a : SolAddress, a ≠ addr → σ'.balanceOf a = σ.balanceOf a) ∧
  σ'.feeNumerator = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator

/-- Solidity removeLiquidity relation (integer floor arithmetic). -/
def SolidityRemoveLiquidity (σ σ' : SolidityStorage) (addr : SolAddress) (shares : ℕ) : Prop :=
  0 < shares ∧
  shares ≤ σ.balanceOf addr ∧
  shares < σ.totalSupply ∧
  removeX σ shares ≤ σ.reserveX ∧
  removeY σ shares ≤ σ.reserveY ∧
  σ'.reserveX = σ.reserveX - removeX σ shares ∧
  σ'.reserveY = σ.reserveY - removeY σ shares ∧
  σ'.totalSupply = σ.totalSupply - shares ∧
  σ'.balanceOf addr = σ.balanceOf addr - shares ∧
  (∀ a : SolAddress, a ≠ addr → σ'.balanceOf a = σ.balanceOf a) ∧
  σ'.feeNumerator = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator

theorem frac_mul_div_mono
    (x y t1 t2 : ℚ)
    (hx : 0 < x) (hy : 0 ≤ y) (ht1 : 0 ≤ t1) (ht1_le_t2 : t1 ≤ t2) :
    y * t1 / (x + t1) ≤ y * t2 / (x + t2) := by
  have ht2 : 0 ≤ t2 := le_trans ht1 ht1_le_t2
  have hden1 : 0 < x + t1 := add_pos_of_pos_of_nonneg hx ht1
  have hden2 : 0 < x + t2 := add_pos_of_pos_of_nonneg hx ht2
  have hcore : t1 * (x + t2) ≤ t2 * (x + t1) := by
    nlinarith [mul_le_mul_of_nonneg_left ht1_le_t2 (le_of_lt hx)]
  have hcore_y : y * t1 * (x + t2) ≤ y * t2 * (x + t1) := by
    simpa [mul_assoc] using (mul_le_mul_of_nonneg_left hcore hy)
  have hleft :
      (y * t1 / (x + t1)) * ((x + t1) * (x + t2)) = y * t1 * (x + t2) := by
    field_simp [ne_of_gt hden1, ne_of_gt hden2]
  have hright :
      (y * t2 / (x + t2)) * ((x + t1) * (x + t2)) = y * t2 * (x + t1) := by
    field_simp [ne_of_gt hden1, ne_of_gt hden2]
  have hmul :
      (y * t1 / (x + t1)) * ((x + t1) * (x + t2))
        ≤ (y * t2 / (x + t2)) * ((x + t1) * (x + t2)) := by
    rw [hleft, hright]
    exact hcore_y
  have hprod_pos : 0 < (x + t1) * (x + t2) := mul_pos hden1 hden2
  exact le_of_mul_le_mul_right hmul hprod_pos

theorem inputEff_cast_le_exact
    (σ : SolidityStorage) (dx : ℕ)
    (hfee_lt_one : solidityFee σ < 1) :
    (inputEff σ dx : ℚ) ≤ (dx : ℚ) * (1 - solidityFee σ) := by
  have hden_pos_q : 0 < (σ.feeDenominator : ℚ) := by
    exact_mod_cast σ.h_denom_pos
  have hnum_lt_den_q : (σ.feeNumerator : ℚ) < (σ.feeDenominator : ℚ) := by
    have : (σ.feeNumerator : ℚ) < 1 * (σ.feeDenominator : ℚ) := by
      exact (div_lt_iff₀ hden_pos_q).1 (by simpa [solidityFee] using hfee_lt_one)
    simpa using this
  have hnum_lt_den : σ.feeNumerator < σ.feeDenominator := by
    exact_mod_cast hnum_lt_den_q
  have hnum_le_den : σ.feeNumerator ≤ σ.feeDenominator := Nat.le_of_lt hnum_lt_den
  have hfloor :
      (inputEff σ dx : ℚ) ≤
        (dx : ℚ) * ((σ.feeDenominator - σ.feeNumerator : ℕ) : ℚ) / (σ.feeDenominator : ℚ) := by
    simpa [inputEff] using
      (nat_div_le_rat_div
        (dx * (σ.feeDenominator - σ.feeNumerator))
        σ.feeDenominator
        σ.h_denom_pos)
  have hrewrite :
      (dx : ℚ) * ((σ.feeDenominator - σ.feeNumerator : ℕ) : ℚ) / (σ.feeDenominator : ℚ) =
        (dx : ℚ) * (1 - solidityFee σ) := by
    rw [Nat.cast_sub hnum_le_den]
    unfold solidityFee
    field_simp [ne_of_gt hden_pos_q]
  simpa [hrewrite] using hfloor

theorem dyOutX_cast_le_dy_of_swap
    (σ : SolidityStorage) (dx : ℕ)
    (hv : Valid (alpha σ)) :
    (dyOutX σ dx : ℚ) ≤
      dy_of_swap (σ.reserveX : ℚ) (σ.reserveY : ℚ) (solidityFee σ) (dx : ℚ) := by
  rcases hv with ⟨hx, hy, _, _, _, hf_lt_one⟩
  have hx_nat_pos : 0 < σ.reserveX := by
    simpa [alpha] using (show (alpha σ).x > 0 from hx)
  have hinput_nonneg : 0 ≤ (inputEff σ dx : ℚ) := by exact_mod_cast (Nat.zero_le (inputEff σ dx))
  have hden_nat_pos : 0 < σ.reserveX + inputEff σ dx :=
    Nat.add_pos_left hx_nat_pos (inputEff σ dx)
  have hfloor :
      (dyOutX σ dx : ℚ) ≤
        ((σ.reserveY * inputEff σ dx : ℕ) : ℚ) / ((σ.reserveX + inputEff σ dx : ℕ) : ℚ) := by
    simpa [dyOutX] using
      (nat_div_le_rat_div
        (σ.reserveY * inputEff σ dx)
        (σ.reserveX + inputEff σ dx)
        hden_nat_pos)
  have hinput_bound :
      (inputEff σ dx : ℚ) ≤ (dx : ℚ) * (1 - solidityFee σ) :=
    inputEff_cast_le_exact σ dx hf_lt_one
  have hratio_mono :
      (σ.reserveY : ℚ) * (inputEff σ dx : ℚ) / ((σ.reserveX : ℚ) + (inputEff σ dx : ℚ))
        ≤
      (σ.reserveY : ℚ) * ((dx : ℚ) * (1 - solidityFee σ)) /
        ((σ.reserveX : ℚ) + ((dx : ℚ) * (1 - solidityFee σ))) := by
    exact frac_mul_div_mono
      (σ.reserveX : ℚ) (σ.reserveY : ℚ)
      (inputEff σ dx : ℚ)
      ((dx : ℚ) * (1 - solidityFee σ))
      hx (le_of_lt hy) hinput_nonneg hinput_bound
  have hfloor' :
      (dyOutX σ dx : ℚ) ≤
        (σ.reserveY : ℚ) * (inputEff σ dx : ℚ) / ((σ.reserveX : ℚ) + (inputEff σ dx : ℚ)) := by
    simpa [Nat.cast_mul, Nat.cast_add] using hfloor
  exact le_trans hfloor' (by simpa [dy_of_swap] using hratio_mono)

theorem dxOutY_cast_le_dy_of_swap
    (σ : SolidityStorage) (dy : ℕ)
    (hv : Valid (alpha σ)) :
    (dxOutY σ dy : ℚ) ≤
      dy_of_swap (σ.reserveY : ℚ) (σ.reserveX : ℚ) (solidityFee σ) (dy : ℚ) := by
  rcases hv with ⟨hx, hy, _, _, _, hf_lt_one⟩
  have hy_nat_pos : 0 < σ.reserveY := by
    simpa [alpha] using (show (alpha σ).y > 0 from hy)
  have hinput_nonneg : 0 ≤ (inputEff σ dy : ℚ) := by exact_mod_cast (Nat.zero_le (inputEff σ dy))
  have hden_nat_pos : 0 < σ.reserveY + inputEff σ dy :=
    Nat.add_pos_left hy_nat_pos (inputEff σ dy)
  have hfloor :
      (dxOutY σ dy : ℚ) ≤
        ((σ.reserveX * inputEff σ dy : ℕ) : ℚ) / ((σ.reserveY + inputEff σ dy : ℕ) : ℚ) := by
    simpa [dxOutY] using
      (nat_div_le_rat_div
        (σ.reserveX * inputEff σ dy)
        (σ.reserveY + inputEff σ dy)
        hden_nat_pos)
  have hinput_bound :
      (inputEff σ dy : ℚ) ≤ (dy : ℚ) * (1 - solidityFee σ) :=
    inputEff_cast_le_exact σ dy hf_lt_one
  have hratio_mono :
      (σ.reserveX : ℚ) * (inputEff σ dy : ℚ) / ((σ.reserveY : ℚ) + (inputEff σ dy : ℚ))
        ≤
      (σ.reserveX : ℚ) * ((dy : ℚ) * (1 - solidityFee σ)) /
        ((σ.reserveY : ℚ) + ((dy : ℚ) * (1 - solidityFee σ))) := by
    exact frac_mul_div_mono
      (σ.reserveY : ℚ) (σ.reserveX : ℚ)
      (inputEff σ dy : ℚ)
      ((dy : ℚ) * (1 - solidityFee σ))
      hy (le_of_lt hx) hinput_nonneg hinput_bound
  have hfloor' :
      (dxOutY σ dy : ℚ) ≤
        (σ.reserveX : ℚ) * (inputEff σ dy : ℚ) / ((σ.reserveY : ℚ) + (inputEff σ dy : ℚ)) := by
    simpa [Nat.cast_mul, Nat.cast_add] using hfloor
  exact le_trans hfloor' (by simpa [dy_of_swap] using hratio_mono)

theorem sim_swapXforY
    (σ σ' : SolidityStorage) (dx : ℕ)
    (hv : Valid (alpha σ))
    (hstep : SoliditySwapXforY σ σ' dx) :
    SwapXforYFloor (alpha σ) (alpha σ') (dx : ℚ) := by
  rcases hstep with
    ⟨hdx_pos, _, hdy_pos, hdy_lt_reserve, hresX, hresY, hL', hbal', hnum', hden'⟩
  unfold SwapXforYFloor
  refine ⟨by exact_mod_cast hdx_pos, ?_⟩
  refine ⟨dyOutX σ dx, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact_mod_cast hdy_pos
  · exact dyOutX_cast_le_dy_of_swap σ dx hv
  · change (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) + (dx : ℚ)
    exact_mod_cast hresX
  · change (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) - (dyOutX σ dx : ℚ)
    rw [hresY, Nat.cast_sub (Nat.le_of_lt hdy_lt_reserve)]
  · have hy_nat : 0 < σ'.reserveY := by
      rw [hresY]
      exact Nat.sub_pos_of_lt hdy_lt_reserve
    change (σ'.reserveY : ℚ) > 0
    exact_mod_cast hy_nat
  · change (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ)
    exact_mod_cast hL'
  · refine ⟨?_, ?_⟩
    · ext a
      change (σ'.balanceOf a : ℚ) = (σ.balanceOf a : ℚ)
      simp [hbal']
    · simp [alpha, solidityFee, hnum', hden']

theorem sim_swapYforX
    (σ σ' : SolidityStorage) (dy : ℕ)
    (hv : Valid (alpha σ))
    (hstep : SoliditySwapYforX σ σ' dy) :
    SwapYforXFloor (alpha σ) (alpha σ') (dy : ℚ) := by
  rcases hstep with
    ⟨hdy_pos, _, hdx_pos, hdx_lt_reserve, hresY, hresX, hL', hbal', hnum', hden'⟩
  unfold SwapYforXFloor
  refine ⟨by exact_mod_cast hdy_pos, ?_⟩
  refine ⟨dxOutY σ dy, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact_mod_cast hdx_pos
  · exact dxOutY_cast_le_dy_of_swap σ dy hv
  · change (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) + (dy : ℚ)
    exact_mod_cast hresY
  · change (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) - (dxOutY σ dy : ℚ)
    rw [hresX, Nat.cast_sub (Nat.le_of_lt hdx_lt_reserve)]
  · have hx_nat : 0 < σ'.reserveX := by
      rw [hresX]
      exact Nat.sub_pos_of_lt hdx_lt_reserve
    change (σ'.reserveX : ℚ) > 0
    exact_mod_cast hx_nat
  · change (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ)
    exact_mod_cast hL'
  · refine ⟨?_, ?_⟩
    · ext a
      change (σ'.balanceOf a : ℚ) = (σ.balanceOf a : ℚ)
      simp [hbal']
    · simp [alpha, solidityFee, hnum', hden']

theorem sim_addLiquidity
    (σ σ' : SolidityStorage) (addr : SolAddress) (dx dy : ℕ)
    (hv : Valid (alpha σ))
    (hstep : SolidityAddLiquidity σ σ' addr dx dy) :
    ∃ dx' dy' : ℚ, AddLiquidityFloor (alpha σ) (alpha σ') addr dx' dy' := by
  rcases hv with ⟨hx, _, _, _, _, _⟩
  rcases hstep with
    ⟨hdx_pos, hdy_pos, hprop, _, hresX, hresY, hL', hbal_addr',
      hbal_other', hnum', hden'⟩
  refine ⟨(dx : ℚ), (dy : ℚ), ?_⟩
  unfold AddLiquidityFloor
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact_mod_cast hdx_pos
  · exact_mod_cast hdy_pos
  · intro hL_pos
    change (σ.totalSupply : ℚ) > 0 at hL_pos
    have hL_pos_nat : 0 < σ.totalSupply := by exact_mod_cast hL_pos
    have hprop_nat : dx * σ.reserveY = dy * σ.reserveX := hprop hL_pos_nat
    change (dx : ℚ) * (σ.reserveY : ℚ) = (dy : ℚ) * (σ.reserveX : ℚ)
    exact_mod_cast hprop_nat
  · change (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) + (dx : ℚ)
    exact_mod_cast hresX
  · change (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) + (dy : ℚ)
    exact_mod_cast hresY
  · change
      (if (σ.totalSupply : ℚ) = 0 then
          (σ'.totalSupply : ℚ) = (dx : ℚ)
        else
          (σ'.totalSupply : ℚ) ≤
            (σ.totalSupply : ℚ) + (σ.totalSupply : ℚ) * (dx : ℚ) / (σ.reserveX : ℚ) ∧
          (σ'.totalSupply : ℚ) >
            (σ.totalSupply : ℚ) + (σ.totalSupply : ℚ) * (dx : ℚ) / (σ.reserveX : ℚ) - 1)
    by_cases hL0 : σ.totalSupply = 0
    · have htotal0 : σ'.totalSupply = dx := by
        simpa [mintedShares, hL0] using hL'
      have hcast0 : (σ'.totalSupply : ℚ) = (dx : ℚ) := by exact_mod_cast htotal0
      have hL0q : (σ.totalSupply : ℚ) = 0 := by exact_mod_cast hL0
      simpa [hL0q] using hcast0
    · have hx_nat_pos : 0 < σ.reserveX := by
        simpa [alpha] using (show (alpha σ).x > 0 from hx)
      have hfloor_le :
          (mintedShares σ dx : ℚ) ≤
            (σ.totalSupply : ℚ) * (dx : ℚ) / (σ.reserveX : ℚ) := by
        simpa [mintedShares, hL0, Nat.cast_mul, mul_assoc, mul_comm, mul_left_comm] using
          (nat_div_le_rat_div (σ.totalSupply * dx) σ.reserveX hx_nat_pos)
      have hfloor_gt :
          (σ.totalSupply : ℚ) * (dx : ℚ) / (σ.reserveX : ℚ) - 1 < (mintedShares σ dx : ℚ) := by
        simpa [mintedShares, hL0, Nat.cast_mul, mul_assoc, mul_comm, mul_left_comm] using
          (rat_div_sub_one_lt_nat_div (σ.totalSupply * dx) σ.reserveX hx_nat_pos)
      have htotal_q :
          (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ) + (mintedShares σ dx : ℚ) := by
        exact_mod_cast hL'
      have hL0q : (σ.totalSupply : ℚ) ≠ 0 := by exact_mod_cast hL0
      simp [hL0q]
      constructor
      · linarith [htotal_q, hfloor_le]
      · linarith [htotal_q, hfloor_gt]
  · change (σ'.balanceOf addr : ℚ) =
      (σ.balanceOf addr : ℚ) + ((σ'.totalSupply : ℚ) - (σ.totalSupply : ℚ))
    have hbal_q :
        (σ'.balanceOf addr : ℚ) = (σ.balanceOf addr : ℚ) + (mintedShares σ dx : ℚ) := by
      exact_mod_cast hbal_addr'
    have htotal_q :
        (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ) + (mintedShares σ dx : ℚ) := by
      exact_mod_cast hL'
    linarith [hbal_q, htotal_q]
  · intro a ha
    change (σ'.balanceOf a : ℚ) = (σ.balanceOf a : ℚ)
    exact_mod_cast (hbal_other' a ha)
  · simp [alpha, solidityFee, hnum', hden']

theorem sim_removeLiquidity
    (σ σ' : SolidityStorage) (addr : SolAddress) (dL : ℕ)
    (hv : Valid (alpha σ))
    (hstep : SolidityRemoveLiquidity σ σ' addr dL) :
    ∃ dL' : ℚ, RemoveLiquidityFloor (alpha σ) (alpha σ') addr dL' := by
  rcases hv with ⟨hx, hy, _, _, _, _⟩
  rcases hstep with
    ⟨hdL_pos, hdL_le_bal, hdL_lt_supply, _hdx_le, _hdy_le,
      hresX, hresY, hL', hbal_addr', hbal_other', hnum', hden'⟩
  have hL_nat_pos : 0 < σ.totalSupply := lt_trans hdL_pos hdL_lt_supply
  have hL_q_pos : 0 < (σ.totalSupply : ℚ) := by exact_mod_cast hL_nat_pos
  have hfloor_x_le :
      (removeX σ dL : ℚ) ≤ (σ.reserveX : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ) := by
    simpa [removeX, Nat.cast_mul, mul_assoc, mul_comm, mul_left_comm] using
      (nat_div_le_rat_div (σ.reserveX * dL) σ.totalSupply hL_nat_pos)
  have hfloor_y_le :
      (removeY σ dL : ℚ) ≤ (σ.reserveY : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ) := by
    simpa [removeY, Nat.cast_mul, mul_assoc, mul_comm, mul_left_comm] using
      (nat_div_le_rat_div (σ.reserveY * dL) σ.totalSupply hL_nat_pos)
  have hfloor_x_gt :
      (σ.reserveX : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ) - 1 < (removeX σ dL : ℚ) := by
    simpa [removeX, Nat.cast_mul, mul_assoc, mul_comm, mul_left_comm] using
      (rat_div_sub_one_lt_nat_div (σ.reserveX * dL) σ.totalSupply hL_nat_pos)
  have hfloor_y_gt :
      (σ.reserveY : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ) - 1 < (removeY σ dL : ℚ) := by
    simpa [removeY, Nat.cast_mul, mul_assoc, mul_comm, mul_left_comm] using
      (rat_div_sub_one_lt_nat_div (σ.reserveY * dL) σ.totalSupply hL_nat_pos)
  have hdL_q_lt : (dL : ℚ) < (σ.totalSupply : ℚ) := by exact_mod_cast hdL_lt_supply
  have hratio_lt_one : (dL : ℚ) / (σ.totalSupply : ℚ) < 1 := by
    have : (dL : ℚ) < 1 * (σ.totalSupply : ℚ) := by simpa using hdL_q_lt
    exact (div_lt_iff₀ hL_q_pos).2 this
  have hexact_x_lt :
      (σ.reserveX : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ) < (σ.reserveX : ℚ) := by
    have hmul : (σ.reserveX : ℚ) * ((dL : ℚ) / (σ.totalSupply : ℚ)) < (σ.reserveX : ℚ) * 1 :=
      mul_lt_mul_of_pos_left hratio_lt_one hx
    calc
      (σ.reserveX : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ)
          = (σ.reserveX : ℚ) * ((dL : ℚ) / (σ.totalSupply : ℚ)) := by ring
      _ < (σ.reserveX : ℚ) * 1 := hmul
      _ = (σ.reserveX : ℚ) := by ring
  have hexact_y_lt :
      (σ.reserveY : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ) < (σ.reserveY : ℚ) := by
    have hmul : (σ.reserveY : ℚ) * ((dL : ℚ) / (σ.totalSupply : ℚ)) < (σ.reserveY : ℚ) * 1 :=
      mul_lt_mul_of_pos_left hratio_lt_one hy
    calc
      (σ.reserveY : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ)
          = (σ.reserveY : ℚ) * ((dL : ℚ) / (σ.totalSupply : ℚ)) := by ring
      _ < (σ.reserveY : ℚ) * 1 := hmul
      _ = (σ.reserveY : ℚ) := by ring
  have hOutX_cast_lt : (removeX σ dL : ℚ) < (σ.reserveX : ℚ) :=
    lt_of_le_of_lt hfloor_x_le hexact_x_lt
  have hOutY_cast_lt : (removeY σ dL : ℚ) < (σ.reserveY : ℚ) :=
    lt_of_le_of_lt hfloor_y_le hexact_y_lt
  have hOutX_nat_lt : removeX σ dL < σ.reserveX := by exact_mod_cast hOutX_cast_lt
  have hOutY_nat_lt : removeY σ dL < σ.reserveY := by exact_mod_cast hOutY_cast_lt
  refine ⟨(dL : ℚ), ?_⟩
  unfold RemoveLiquidityFloor
  refine ⟨?_, ?_, ?_, removeX σ dL, removeY σ dL, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact_mod_cast hdL_pos
  · change (dL : ℚ) ≤ (σ.balanceOf addr : ℚ)
    exact_mod_cast hdL_le_bal
  · change (dL : ℚ) < (σ.totalSupply : ℚ)
    exact_mod_cast hdL_lt_supply
  · exact hfloor_x_le
  · exact hfloor_x_gt
  · exact hfloor_y_le
  · exact hfloor_y_gt
  · change (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) - (removeX σ dL : ℚ)
    rw [hresX, Nat.cast_sub (Nat.le_of_lt hOutX_nat_lt)]
  · change (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) - (removeY σ dL : ℚ)
    rw [hresY, Nat.cast_sub (Nat.le_of_lt hOutY_nat_lt)]
  · have hx_nat : 0 < σ'.reserveX := by
      rw [hresX]
      exact Nat.sub_pos_of_lt hOutX_nat_lt
    change (σ'.reserveX : ℚ) > 0
    exact_mod_cast hx_nat
  · have hy_nat : 0 < σ'.reserveY := by
      rw [hresY]
      exact Nat.sub_pos_of_lt hOutY_nat_lt
    change (σ'.reserveY : ℚ) > 0
    exact_mod_cast hy_nat
  · change (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ) - (dL : ℚ)
    rw [hL', Nat.cast_sub (Nat.le_of_lt hdL_lt_supply)]
  · change (σ'.balanceOf addr : ℚ) = (σ.balanceOf addr : ℚ) - (dL : ℚ)
    rw [hbal_addr', Nat.cast_sub hdL_le_bal]
  · refine ⟨?_, ?_⟩
    · intro a ha
      change (σ'.balanceOf a : ℚ) = (σ.balanceOf a : ℚ)
      exact_mod_cast (hbal_other' a ha)
    · simp [alpha, solidityFee, hnum', hden']
