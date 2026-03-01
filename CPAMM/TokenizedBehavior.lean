import CPAMM.TokenizedRefinement

/-!
  CPAMM-1 Tokenized Behavior Taxonomy

  This module makes the token-behavior assumption surface explicit in Lean.
  It classifies token behavior classes and proves that several adversarial
  classes violate the exact-transfer deltas required by
  `CPAMM/TokenizedRefinement.lean`.
-/

/-- Token behavior classes relevant to the tokenized AMM assumption surface. -/
inductive TokenClass where
  | standardExact
  | feeOnTransfer
  | inflationary
  | noOpTransferFrom
  | externalBalanceDrift
  deriving DecidableEq, Repr

/-- Classes accepted by `CPAMMTokenized`'s strict reserve/balance checks. -/
def SupportedTokenClass : TokenClass → Prop
  | .standardExact => True
  | _ => False

theorem supportedTokenClass_iff_standardExact (c : TokenClass) :
    SupportedTokenClass c ↔ c = .standardExact := by
  cases c <;> simp [SupportedTokenClass]

/-- Exact pull-transfer delta required by the tokenized refinement model. -/
def ExactPullDelta (before after amount : ℕ) : Prop :=
  after = before + amount

/-- Exact push-transfer delta required by the tokenized refinement model. -/
def ExactPushDelta (before after amount : ℕ) : Prop :=
  before = after + amount

/-- Deflationary/fee-on-transfer pull behavior. -/
def FeeOnTransferPull (before after amount fee : ℕ) : Prop :=
  amount > 0 ∧
  fee > 0 ∧
  fee < amount ∧
  after = before + (amount - fee)

/-- Inflationary/mint-on-transfer pull behavior. -/
def InflationaryPull (before after amount bonus : ℕ) : Prop :=
  amount > 0 ∧
  bonus > 0 ∧
  after = before + amount + bonus

/-- No-op `transferFrom`: allowance may move, balances do not. -/
def NoOpPull (before after amount : ℕ) : Prop :=
  amount > 0 ∧
  after = before

/-- External drift (rebase/airdrop/manual transfer) of observed pool balance. -/
def ExternalBalanceDrift (before after drift : ℕ) : Prop :=
  drift > 0 ∧
  after = before + drift

theorem feeOnTransferPull_not_exact
    {before after amount fee : ℕ}
    (h : FeeOnTransferPull before after amount fee) :
    ¬ ExactPullDelta before after amount := by
  rcases h with ⟨hamount_pos, hfee_pos, _hfee_lt_amount, hafter⟩
  intro hexact
  have hlt : amount - fee < amount := Nat.sub_lt hamount_pos hfee_pos
  have hlt' : before + (amount - fee) < before + amount := Nat.add_lt_add_left hlt before
  have hneq : before + (amount - fee) ≠ before + amount := ne_of_lt hlt'
  apply hneq
  calc
    before + (amount - fee) = after := hafter.symm
    _ = before + amount := hexact

theorem inflationaryPull_not_exact
    {before after amount bonus : ℕ}
    (h : InflationaryPull before after amount bonus) :
    ¬ ExactPullDelta before after amount := by
  rcases h with ⟨_hamount_pos, hbonus_pos, hafter⟩
  intro hexact
  have hlt : before + amount < before + amount + bonus := Nat.lt_add_of_pos_right hbonus_pos
  have hneq : before + amount + bonus ≠ before + amount := ne_of_gt hlt
  apply hneq
  calc
    before + amount + bonus = after := hafter.symm
    _ = before + amount := hexact

theorem noOpPull_not_exact
    {before after amount : ℕ}
    (h : NoOpPull before after amount) :
    ¬ ExactPullDelta before after amount := by
  rcases h with ⟨hamount_pos, hafter⟩
  intro hexact
  have hlt : before < before + amount := Nat.lt_add_of_pos_right hamount_pos
  have hneq : before ≠ before + amount := ne_of_lt hlt
  apply hneq
  calc
    before = after := hafter.symm
    _ = before + amount := hexact

/-- Tokenized add-liquidity enforces an exact pull delta on token X. -/
theorem exactPullDelta_of_tokenizedAddLiquidityX
    {τ τ' : TokenizedStorage} {addr : SolAddress} {dx dy : ℕ}
    (hstep : TokenizedAddLiquidity τ τ' addr dx dy) :
    ExactPullDelta τ.tokenBalX τ'.tokenBalX dx := by
  rcases hstep with ⟨_hsol, hbalX, _hbalY⟩
  simpa [ExactPullDelta] using hbalX

/-- Tokenized add-liquidity enforces an exact pull delta on token Y. -/
theorem exactPullDelta_of_tokenizedAddLiquidityY
    {τ τ' : TokenizedStorage} {addr : SolAddress} {dx dy : ℕ}
    (hstep : TokenizedAddLiquidity τ τ' addr dx dy) :
    ExactPullDelta τ.tokenBalY τ'.tokenBalY dy := by
  rcases hstep with ⟨_hsol, _hbalX, hbalY⟩
  simpa [ExactPullDelta] using hbalY

/-- Tokenized swapXforY enforces an exact pull delta on input token X. -/
theorem exactPullDelta_of_tokenizedSwapXforY
    {τ τ' : TokenizedStorage} {dx : ℕ}
    (hstep : TokenizedSwapXforY τ τ' dx) :
    ExactPullDelta τ.tokenBalX τ'.tokenBalX dx := by
  rcases hstep with ⟨_hsol, hbalX, _hbalY⟩
  simpa [ExactPullDelta] using hbalX

/-- Tokenized swapYforX enforces an exact pull delta on input token Y. -/
theorem exactPullDelta_of_tokenizedSwapYforX
    {τ τ' : TokenizedStorage} {dy : ℕ}
    (hstep : TokenizedSwapYforX τ τ' dy) :
    ExactPullDelta τ.tokenBalY τ'.tokenBalY dy := by
  rcases hstep with ⟨_hsol, hbalY, _hbalX⟩
  simpa [ExactPullDelta] using hbalY

/-- Any non-exact pull delta on token X is incompatible with tokenized add-liquidity. -/
theorem notExactPull_incompatible_tokenizedAddLiquidityX
    {τ τ' : TokenizedStorage} {addr : SolAddress} {dx dy : ℕ}
    (hnot : ¬ ExactPullDelta τ.tokenBalX τ'.tokenBalX dx) :
    ¬ TokenizedAddLiquidity τ τ' addr dx dy := by
  intro hstep
  exact hnot (exactPullDelta_of_tokenizedAddLiquidityX hstep)

/-- Any non-exact pull delta on token Y is incompatible with tokenized add-liquidity. -/
theorem notExactPull_incompatible_tokenizedAddLiquidityY
    {τ τ' : TokenizedStorage} {addr : SolAddress} {dx dy : ℕ}
    (hnot : ¬ ExactPullDelta τ.tokenBalY τ'.tokenBalY dy) :
    ¬ TokenizedAddLiquidity τ τ' addr dx dy := by
  intro hstep
  exact hnot (exactPullDelta_of_tokenizedAddLiquidityY hstep)

/-- Any non-exact pull delta on input token X is incompatible with tokenized swapXforY. -/
theorem notExactPull_incompatible_tokenizedSwapXforY
    {τ τ' : TokenizedStorage} {dx : ℕ}
    (hnot : ¬ ExactPullDelta τ.tokenBalX τ'.tokenBalX dx) :
    ¬ TokenizedSwapXforY τ τ' dx := by
  intro hstep
  exact hnot (exactPullDelta_of_tokenizedSwapXforY hstep)

/-- Any non-exact pull delta on input token Y is incompatible with tokenized swapYforX. -/
theorem notExactPull_incompatible_tokenizedSwapYforX
    {τ τ' : TokenizedStorage} {dy : ℕ}
    (hnot : ¬ ExactPullDelta τ.tokenBalY τ'.tokenBalY dy) :
    ¬ TokenizedSwapYforX τ τ' dy := by
  intro hstep
  exact hnot (exactPullDelta_of_tokenizedSwapYforX hstep)

/-- Fee-on-transfer pull cannot satisfy tokenized add-liquidity on token X input. -/
theorem feeOnTransferPull_incompatible_tokenizedAddLiquidityX
    {τ τ' : TokenizedStorage} {addr : SolAddress} {dx dy fee : ℕ}
    (hfee : FeeOnTransferPull τ.tokenBalX τ'.tokenBalX dx fee) :
    ¬ TokenizedAddLiquidity τ τ' addr dx dy := by
  exact notExactPull_incompatible_tokenizedAddLiquidityX
    (hnot := feeOnTransferPull_not_exact hfee)

/-- Fee-on-transfer pull cannot satisfy tokenized add-liquidity on token Y input. -/
theorem feeOnTransferPull_incompatible_tokenizedAddLiquidityY
    {τ τ' : TokenizedStorage} {addr : SolAddress} {dx dy fee : ℕ}
    (hfee : FeeOnTransferPull τ.tokenBalY τ'.tokenBalY dy fee) :
    ¬ TokenizedAddLiquidity τ τ' addr dx dy := by
  exact notExactPull_incompatible_tokenizedAddLiquidityY
    (hnot := feeOnTransferPull_not_exact hfee)

/-- Inflationary pull cannot satisfy tokenized swapXforY on token X input. -/
theorem inflationaryPull_incompatible_tokenizedSwapXforY
    {τ τ' : TokenizedStorage} {dx bonus : ℕ}
    (hinf : InflationaryPull τ.tokenBalX τ'.tokenBalX dx bonus) :
    ¬ TokenizedSwapXforY τ τ' dx := by
  exact notExactPull_incompatible_tokenizedSwapXforY
    (hnot := inflationaryPull_not_exact hinf)

/-- No-op transferFrom cannot satisfy tokenized swapYforX on token Y input. -/
theorem noOpPull_incompatible_tokenizedSwapYforX
    {τ τ' : TokenizedStorage} {dy : ℕ}
    (hnoop : NoOpPull τ.tokenBalY τ'.tokenBalY dy) :
    ¬ TokenizedSwapYforX τ τ' dy := by
  exact notExactPull_incompatible_tokenizedSwapYforX
    (hnot := noOpPull_not_exact hnoop)

theorem externalBalanceDrift_not_exactSync
    {before after drift : ℕ}
    (h : ExternalBalanceDrift before after drift) :
    after ≠ before := by
  rcases h with ⟨hdrift_pos, hafter⟩
  have hlt : before < before + drift := Nat.lt_add_of_pos_right hdrift_pos
  have hneq : before + drift ≠ before := ne_of_gt hlt
  intro hEq
  apply hneq
  calc
    before + drift = after := hafter.symm
    _ = before := hEq

/-- External drift on token X with unchanged reserves breaks reserve-sync. -/
theorem reserveSync_not_preserved_by_externalDriftX
    {τ τ' : TokenizedStorage} {drift : ℕ}
    (hsync : ReserveSync τ)
    (hcore : τ'.core = τ.core)
    (hdrift : ExternalBalanceDrift τ.tokenBalX τ'.tokenBalX drift) :
    ¬ ReserveSync τ' := by
  intro hsync'
  rcases hsync with ⟨hXsync, _hYsync⟩
  rcases hsync' with ⟨hXsync', _hYsync'⟩
  have hneq : τ'.tokenBalX ≠ τ.tokenBalX := externalBalanceDrift_not_exactSync hdrift
  apply hneq
  calc
    τ'.tokenBalX = τ'.core.reserveX := hXsync'.symm
    _ = τ.core.reserveX := by simp [hcore]
    _ = τ.tokenBalX := hXsync

/-- External drift on token Y with unchanged reserves breaks reserve-sync. -/
theorem reserveSync_not_preserved_by_externalDriftY
    {τ τ' : TokenizedStorage} {drift : ℕ}
    (hsync : ReserveSync τ)
    (hcore : τ'.core = τ.core)
    (hdrift : ExternalBalanceDrift τ.tokenBalY τ'.tokenBalY drift) :
    ¬ ReserveSync τ' := by
  intro hsync'
  rcases hsync with ⟨_hXsync, hYsync⟩
  rcases hsync' with ⟨_hXsync', hYsync'⟩
  have hneq : τ'.tokenBalY ≠ τ.tokenBalY := externalBalanceDrift_not_exactSync hdrift
  apply hneq
  calc
    τ'.tokenBalY = τ'.core.reserveY := hYsync'.symm
    _ = τ.core.reserveY := by simp [hcore]
    _ = τ.tokenBalY := hYsync

/-- Concrete witness that reserve-sync can be broken by external balance drift. -/
theorem exists_reserveSync_break_by_externalDrift :
    ∃ τ τ' : TokenizedStorage,
      ReserveSync τ ∧
      τ'.core = τ.core ∧
      τ'.tokenBalX = τ.tokenBalX + 1 ∧
      τ'.tokenBalY = τ.tokenBalY ∧
      ¬ ReserveSync τ' := by
  let core : SolidityStorage :=
    { reserveX := 1
      reserveY := 1
      totalSupply := 1
      balanceOf := fun _ => 0
      feeNumerator := 3
      feeDenominator := 1000
      h_denom_pos := by decide }
  let τ : TokenizedStorage :=
    { core := core
      tokenBalX := 1
      tokenBalY := 1 }
  let τ' : TokenizedStorage :=
    { core := core
      tokenBalX := 2
      tokenBalY := 1 }
  refine ⟨τ, τ', ?_, ?_, ?_, ?_, ?_⟩
  · simp [τ, core, ReserveSync]
  · simp [τ, τ']
  · simp [τ, τ']
  · simp [τ, τ']
  · simp [τ', core, ReserveSync]
