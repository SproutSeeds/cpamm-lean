import CPAMM.Rounding

/-!
  CPAMM-1 Phase 6: Refinement Layer

  The Solidity relations below model integer arithmetic and include explicit
  exactness side conditions where needed to connect floor arithmetic to the
  exact rational model.
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

/-- Solidity swapXforY relation (integer arithmetic plus exactness side condition). -/
def SoliditySwapXforY (σ σ' : SolidityStorage) (dx : ℕ) : Prop :=
  dx > 0 ∧
  inputEff σ dx > 0 ∧
  dyOutX σ dx > 0 ∧
  dyOutX σ dx < σ.reserveY ∧
  ((dyOutX σ dx : ℚ) =
    dy_of_swap (σ.reserveX : ℚ) (σ.reserveY : ℚ) (solidityFee σ) (dx : ℚ)) ∧
  σ'.reserveX = σ.reserveX + dx ∧
  σ'.reserveY = σ.reserveY - dyOutX σ dx ∧
  σ'.totalSupply = σ.totalSupply ∧
  σ'.balanceOf = σ.balanceOf ∧
  σ'.feeNumerator = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator

/-- Solidity swapYforX relation (integer arithmetic plus exactness side condition). -/
def SoliditySwapYforX (σ σ' : SolidityStorage) (dy : ℕ) : Prop :=
  dy > 0 ∧
  inputEff σ dy > 0 ∧
  dxOutY σ dy > 0 ∧
  dxOutY σ dy < σ.reserveX ∧
  ((dxOutY σ dy : ℚ) =
    dy_of_swap (σ.reserveY : ℚ) (σ.reserveX : ℚ) (solidityFee σ) (dy : ℚ)) ∧
  σ'.reserveY = σ.reserveY + dy ∧
  σ'.reserveX = σ.reserveX - dxOutY σ dy ∧
  σ'.totalSupply = σ.totalSupply ∧
  σ'.balanceOf = σ.balanceOf ∧
  σ'.feeNumerator = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator

/-- Solidity addLiquidity relation with explicit share exactness side condition. -/
def SolidityAddLiquidity (σ σ' : SolidityStorage) (addr : SolAddress) (dx dy : ℕ) : Prop :=
  dx > 0 ∧
  dy > 0 ∧
  (σ.totalSupply > 0 → dx * σ.reserveY = dy * σ.reserveX) ∧
  (σ.totalSupply = 0 ∨
    ((mintedShares σ dx : ℚ) =
      (σ.totalSupply : ℚ) * (dx : ℚ) / (σ.reserveX : ℚ))) ∧
  mintedShares σ dx > 0 ∧
  σ'.reserveX = σ.reserveX + dx ∧
  σ'.reserveY = σ.reserveY + dy ∧
  σ'.totalSupply = σ.totalSupply + mintedShares σ dx ∧
  σ'.balanceOf addr = σ.balanceOf addr + mintedShares σ dx ∧
  (∀ a : SolAddress, a ≠ addr → σ'.balanceOf a = σ.balanceOf a) ∧
  σ'.feeNumerator = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator

/-- Solidity removeLiquidity relation with explicit exactness side conditions. -/
def SolidityRemoveLiquidity (σ σ' : SolidityStorage) (addr : SolAddress) (shares : ℕ) : Prop :=
  0 < shares ∧
  shares ≤ σ.balanceOf addr ∧
  shares < σ.totalSupply ∧
  removeX σ shares ≤ σ.reserveX ∧
  removeY σ shares ≤ σ.reserveY ∧
  ((removeX σ shares : ℚ) =
    (σ.reserveX : ℚ) * (shares : ℚ) / (σ.totalSupply : ℚ)) ∧
  ((removeY σ shares : ℚ) =
    (σ.reserveY : ℚ) * (shares : ℚ) / (σ.totalSupply : ℚ)) ∧
  σ'.reserveX = σ.reserveX - removeX σ shares ∧
  σ'.reserveY = σ.reserveY - removeY σ shares ∧
  σ'.totalSupply = σ.totalSupply - shares ∧
  σ'.balanceOf addr = σ.balanceOf addr - shares ∧
  (∀ a : SolAddress, a ≠ addr → σ'.balanceOf a = σ.balanceOf a) ∧
  σ'.feeNumerator = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator

theorem sim_swapXforY
    (σ σ' : SolidityStorage) (dx : ℕ)
    (_hv : Valid (alpha σ))
    (hstep : SoliditySwapXforY σ σ' dx) :
    SwapXforY (alpha σ) (alpha σ') (dx : ℚ) := by
  rcases hstep with
    ⟨hdx_pos, _, hdy_pos, hdy_lt_reserve, hdy_exact, hresX, hresY, hL', hbal',
      hnum', hden'⟩
  unfold SwapXforY
  refine ⟨by exact_mod_cast hdx_pos, ?_⟩
  dsimp
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · have hdy_pos_q : (0 : ℚ) < (dyOutX σ dx : ℚ) := by exact_mod_cast hdy_pos
    simpa [hdy_exact] using hdy_pos_q
  · change (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) + (dx : ℚ)
    exact_mod_cast hresX
  · change (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) -
      dy_of_swap (σ.reserveX : ℚ) (σ.reserveY : ℚ) (solidityFee σ) (dx : ℚ)
    have hy_cast :
        (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) - (dyOutX σ dx : ℚ) := by
      rw [hresY, Nat.cast_sub (Nat.le_of_lt hdy_lt_reserve)]
    simpa [hdy_exact] using hy_cast
  · have hy_nat : 0 < σ'.reserveY := by
      rw [hresY]
      exact Nat.sub_pos_of_lt hdy_lt_reserve
    change (σ'.reserveY : ℚ) > 0
    exact_mod_cast hy_nat
  · change (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ)
    exact_mod_cast hL'
  · ext a
    change (σ'.balanceOf a : ℚ) = (σ.balanceOf a : ℚ)
    simp [hbal']
  · simp [alpha, solidityFee, hnum', hden']

theorem sim_swapYforX
    (σ σ' : SolidityStorage) (dy : ℕ)
    (_hv : Valid (alpha σ))
    (hstep : SoliditySwapYforX σ σ' dy) :
    SwapYforX (alpha σ) (alpha σ') (dy : ℚ) := by
  rcases hstep with
    ⟨hdy_pos, _, hdx_pos, hdx_lt_reserve, hdx_exact, hresY, hresX, hL', hbal',
      hnum', hden'⟩
  unfold SwapYforX
  refine ⟨by exact_mod_cast hdy_pos, ?_⟩
  dsimp
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · have hdx_pos_q : (0 : ℚ) < (dxOutY σ dy : ℚ) := by exact_mod_cast hdx_pos
    simpa [hdx_exact] using hdx_pos_q
  · change (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) + (dy : ℚ)
    exact_mod_cast hresY
  · change (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) -
      dy_of_swap (σ.reserveY : ℚ) (σ.reserveX : ℚ) (solidityFee σ) (dy : ℚ)
    have hx_cast :
        (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) - (dxOutY σ dy : ℚ) := by
      rw [hresX, Nat.cast_sub (Nat.le_of_lt hdx_lt_reserve)]
    simpa [hdx_exact] using hx_cast
  · have hx_nat : 0 < σ'.reserveX := by
      rw [hresX]
      exact Nat.sub_pos_of_lt hdx_lt_reserve
    change (σ'.reserveX : ℚ) > 0
    exact_mod_cast hx_nat
  · change (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ)
    exact_mod_cast hL'
  · ext a
    change (σ'.balanceOf a : ℚ) = (σ.balanceOf a : ℚ)
    simp [hbal']
  · simp [alpha, solidityFee, hnum', hden']

theorem sim_addLiquidity
    (σ σ' : SolidityStorage) (addr : SolAddress) (dx dy : ℕ)
    (_hv : Valid (alpha σ))
    (hstep : SolidityAddLiquidity σ σ' addr dx dy) :
    ∃ dx' dy' : ℚ, AddLiquidity (alpha σ) (alpha σ') addr dx' dy' := by
  rcases hstep with
    ⟨hdx_pos, hdy_pos, hprop, hshares_exact, _, hresX, hresY, hL', hbal_addr',
      hbal_other', hnum', hden'⟩
  refine ⟨(dx : ℚ), (dy : ℚ), ?_⟩
  unfold AddLiquidity
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
  · change (σ'.totalSupply : ℚ) =
      if (σ.totalSupply : ℚ) = 0 then (dx : ℚ)
      else (σ.totalSupply : ℚ) + (σ.totalSupply : ℚ) * (dx : ℚ) / (σ.reserveX : ℚ)
    by_cases hL0 : σ.totalSupply = 0
    · have htotal0 : σ'.totalSupply = dx := by
        simpa [mintedShares, hL0] using hL'
      have hcast0 : (σ'.totalSupply : ℚ) = (dx : ℚ) := by exact_mod_cast htotal0
      simpa [hL0] using hcast0
    · have hshares_q :
          (mintedShares σ dx : ℚ) =
            (σ.totalSupply : ℚ) * (dx : ℚ) / (σ.reserveX : ℚ) := by
        rcases hshares_exact with hzero | hq
        · exact (hL0 hzero).elim
        · exact hq
      have htotal_q :
          (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ) + (mintedShares σ dx : ℚ) := by
        exact_mod_cast hL'
      have htarget :
          (σ'.totalSupply : ℚ) =
            (σ.totalSupply : ℚ) + (σ.totalSupply : ℚ) * (dx : ℚ) / (σ.reserveX : ℚ) := by
        linarith [htotal_q, hshares_q]
      simpa [hL0] using htarget
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
    (_hv : Valid (alpha σ))
    (hstep : SolidityRemoveLiquidity σ σ' addr dL) :
    ∃ dL' : ℚ, RemoveLiquidity (alpha σ) (alpha σ') addr dL' := by
  rcases hstep with
    ⟨hdL_pos, hdL_le_bal, hdL_lt_supply, hdx_le, hdy_le, hdx_exact, hdy_exact,
      hresX, hresY, hL', hbal_addr', hbal_other', hnum', hden'⟩
  refine ⟨(dL : ℚ), ?_⟩
  unfold RemoveLiquidity
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact_mod_cast hdL_pos
  · change (dL : ℚ) ≤ (σ.balanceOf addr : ℚ)
    exact_mod_cast hdL_le_bal
  · change (dL : ℚ) < (σ.totalSupply : ℚ)
    exact_mod_cast hdL_lt_supply
  · change (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) -
      (σ.reserveX : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ)
    have hx_cast :
        (σ'.reserveX : ℚ) = (σ.reserveX : ℚ) - (removeX σ dL : ℚ) := by
      rw [hresX, Nat.cast_sub hdx_le]
    linarith [hx_cast, hdx_exact]
  · change (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) -
      (σ.reserveY : ℚ) * (dL : ℚ) / (σ.totalSupply : ℚ)
    have hy_cast :
        (σ'.reserveY : ℚ) = (σ.reserveY : ℚ) - (removeY σ dL : ℚ) := by
      rw [hresY, Nat.cast_sub hdy_le]
    linarith [hy_cast, hdy_exact]
  · change (σ'.totalSupply : ℚ) = (σ.totalSupply : ℚ) - (dL : ℚ)
    rw [hL', Nat.cast_sub (Nat.le_of_lt hdL_lt_supply)]
  · change (σ'.balanceOf addr : ℚ) = (σ.balanceOf addr : ℚ) - (dL : ℚ)
    rw [hbal_addr', Nat.cast_sub hdL_le_bal]
  · intro a ha
    change (σ'.balanceOf a : ℚ) = (σ.balanceOf a : ℚ)
    exact_mod_cast (hbal_other' a ha)
  · simp [alpha, solidityFee, hnum', hden']
