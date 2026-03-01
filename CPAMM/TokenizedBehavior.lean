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
