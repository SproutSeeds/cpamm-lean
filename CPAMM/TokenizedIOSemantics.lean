import CPAMM.TokenizedRefinement

/-!
  Tokenized IO Semantics

  This module centralizes transfer-delta and recipient-observed output relations
  used by tokenized refinement and behavior proofs.
-/

/-- Exact pull-transfer delta required by the tokenized refinement model. -/
def ExactPullDelta (before after amount : ℕ) : Prop :=
  after = before + amount

/-- Exact push-transfer delta required by the tokenized refinement model. -/
def ExactPushDelta (before after amount : ℕ) : Prop :=
  before = after + amount

/-- Exact recipient-observed output relation for quoted output amounts. -/
def RecipientObservedOutputExact (recipientBefore recipientAfter quotedOut : ℕ) : Prop :=
  recipientAfter = recipientBefore + quotedOut

theorem recipientObservedOutputExact_iff_exactPullDelta
    (recipientBefore recipientAfter quotedOut : ℕ) :
    RecipientObservedOutputExact recipientBefore recipientAfter quotedOut
      ↔ ExactPullDelta recipientBefore recipientAfter quotedOut := by
  rfl

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
