import CPAMM.Refinement

/-!
  CPAMM-1 Tokenized Refinement Layer

  This module extends the arithmetic Solidity storage model with explicit
  on-chain token balances at the AMM contract address.

  The tokenized step relations intentionally encode exact-balance-delta
  assumptions (no hidden mint/burn/rebase side effects and no fee-on-transfer)
  by construction. Under those assumptions, we prove:

  1. Reserve-sync preservation (`reserve = token balance`) for each step.
  2. Projection/simulation into the existing Solidity refinement relations.
  3. Validity preservation for projected abstract states.
-/

/-- Tokenized concrete storage: arithmetic core + observed on-chain balances. -/
structure TokenizedStorage where
  core : SolidityStorage
  tokenBalX : ℕ
  tokenBalY : ℕ

/-- Reserve sync invariant used by the tokenized extension. -/
def ReserveSync (τ : TokenizedStorage) : Prop :=
  τ.core.reserveX = τ.tokenBalX ∧
  τ.core.reserveY = τ.tokenBalY

/-- Abstraction of tokenized storage into the existing abstract CPAMM model. -/
def alphaTokenized (τ : TokenizedStorage) : CpammState SolAddress :=
  alpha τ.core

/-- Tokenized `swapXforY` with explicit exact token balance deltas. -/
def TokenizedSwapXforY (τ τ' : TokenizedStorage) (dx : ℕ) : Prop :=
  SoliditySwapXforY τ.core τ'.core dx ∧
  τ'.tokenBalX = τ.tokenBalX + dx ∧
  τ'.tokenBalY = τ.tokenBalY - dyOutX τ.core dx

/-- Tokenized `swapYforX` with explicit exact token balance deltas. -/
def TokenizedSwapYforX (τ τ' : TokenizedStorage) (dy : ℕ) : Prop :=
  SoliditySwapYforX τ.core τ'.core dy ∧
  τ'.tokenBalY = τ.tokenBalY + dy ∧
  τ'.tokenBalX = τ.tokenBalX - dxOutY τ.core dy

/-- Tokenized `addLiquidity` with exact incoming token balance deltas. -/
def TokenizedAddLiquidity (τ τ' : TokenizedStorage)
    (addr : SolAddress) (dx dy : ℕ) : Prop :=
  SolidityAddLiquidity τ.core τ'.core addr dx dy ∧
  τ'.tokenBalX = τ.tokenBalX + dx ∧
  τ'.tokenBalY = τ.tokenBalY + dy

/-- Tokenized `removeLiquidity` with exact outgoing token balance deltas. -/
def TokenizedRemoveLiquidity (τ τ' : TokenizedStorage)
    (addr : SolAddress) (shares : ℕ) : Prop :=
  SolidityRemoveLiquidity τ.core τ'.core addr shares ∧
  τ'.tokenBalX = τ.tokenBalX - removeX τ.core shares ∧
  τ'.tokenBalY = τ.tokenBalY - removeY τ.core shares

/-- Projection/simulation: tokenized swapXforY implies arithmetic Solidity swapXforY. -/
theorem sim_tokenizedSwapXforY
    (τ τ' : TokenizedStorage) (dx : ℕ)
    (hstep : TokenizedSwapXforY τ τ' dx) :
    SoliditySwapXforY τ.core τ'.core dx :=
  hstep.1

/-- Projection/simulation: tokenized swapYforX implies arithmetic Solidity swapYforX. -/
theorem sim_tokenizedSwapYforX
    (τ τ' : TokenizedStorage) (dy : ℕ)
    (hstep : TokenizedSwapYforX τ τ' dy) :
    SoliditySwapYforX τ.core τ'.core dy :=
  hstep.1

/-- Projection/simulation: tokenized addLiquidity implies arithmetic Solidity addLiquidity. -/
theorem sim_tokenizedAddLiquidity
    (τ τ' : TokenizedStorage) (addr : SolAddress) (dx dy : ℕ)
    (hstep : TokenizedAddLiquidity τ τ' addr dx dy) :
    SolidityAddLiquidity τ.core τ'.core addr dx dy :=
  hstep.1

/-- Projection/simulation: tokenized removeLiquidity implies arithmetic Solidity removeLiquidity. -/
theorem sim_tokenizedRemoveLiquidity
    (τ τ' : TokenizedStorage) (addr : SolAddress) (shares : ℕ)
    (hstep : TokenizedRemoveLiquidity τ τ' addr shares) :
    SolidityRemoveLiquidity τ.core τ'.core addr shares :=
  hstep.1

/-- Reserve-sync is preserved by tokenized swapXforY. -/
theorem reserveSync_preserved_tokenizedSwapXforY
    (τ τ' : TokenizedStorage) (dx : ℕ)
    (hsync : ReserveSync τ)
    (hstep : TokenizedSwapXforY τ τ' dx) :
    ReserveSync τ' := by
  rcases hsync with ⟨hXsync, hYsync⟩
  rcases hstep with ⟨hsol, hbalX, hbalY⟩
  rcases hsol with
    ⟨_hdx_pos, _heff_pos, _hdy_pos, _hdy_lt_reserve, hresX, hresY,
      _hL, _hbal, _hnum, _hden⟩
  refine ⟨?_, ?_⟩
  · calc
      τ'.core.reserveX = τ.core.reserveX + dx := hresX
      _ = τ.tokenBalX + dx := by simp [hXsync]
      _ = τ'.tokenBalX := by simp [hbalX]
  · calc
      τ'.core.reserveY = τ.core.reserveY - dyOutX τ.core dx := hresY
      _ = τ.tokenBalY - dyOutX τ.core dx := by simp [hYsync]
      _ = τ'.tokenBalY := by simp [hbalY]

/-- Reserve-sync is preserved by tokenized swapYforX. -/
theorem reserveSync_preserved_tokenizedSwapYforX
    (τ τ' : TokenizedStorage) (dy : ℕ)
    (hsync : ReserveSync τ)
    (hstep : TokenizedSwapYforX τ τ' dy) :
    ReserveSync τ' := by
  rcases hsync with ⟨hXsync, hYsync⟩
  rcases hstep with ⟨hsol, hbalY, hbalX⟩
  rcases hsol with
    ⟨_hdy_pos, _heff_pos, _hdx_pos, _hdx_lt_reserve, hresY, hresX,
      _hL, _hbal, _hnum, _hden⟩
  refine ⟨?_, ?_⟩
  · calc
      τ'.core.reserveX = τ.core.reserveX - dxOutY τ.core dy := hresX
      _ = τ.tokenBalX - dxOutY τ.core dy := by simp [hXsync]
      _ = τ'.tokenBalX := by simp [hbalX]
  · calc
      τ'.core.reserveY = τ.core.reserveY + dy := hresY
      _ = τ.tokenBalY + dy := by simp [hYsync]
      _ = τ'.tokenBalY := by simp [hbalY]

/-- Reserve-sync is preserved by tokenized addLiquidity. -/
theorem reserveSync_preserved_tokenizedAddLiquidity
    (τ τ' : TokenizedStorage) (addr : SolAddress) (dx dy : ℕ)
    (hsync : ReserveSync τ)
    (hstep : TokenizedAddLiquidity τ τ' addr dx dy) :
    ReserveSync τ' := by
  rcases hsync with ⟨hXsync, hYsync⟩
  rcases hstep with ⟨hsol, hbalX, hbalY⟩
  rcases hsol with
    ⟨_hdx_pos, _hdy_pos, _hprop, _hmint_pos, hresX, hresY,
      _hL, _hbalAddr, _hbalOther, _hnum, _hden⟩
  refine ⟨?_, ?_⟩
  · calc
      τ'.core.reserveX = τ.core.reserveX + dx := hresX
      _ = τ.tokenBalX + dx := by simp [hXsync]
      _ = τ'.tokenBalX := by simp [hbalX]
  · calc
      τ'.core.reserveY = τ.core.reserveY + dy := hresY
      _ = τ.tokenBalY + dy := by simp [hYsync]
      _ = τ'.tokenBalY := by simp [hbalY]

/-- Reserve-sync is preserved by tokenized removeLiquidity. -/
theorem reserveSync_preserved_tokenizedRemoveLiquidity
    (τ τ' : TokenizedStorage) (addr : SolAddress) (shares : ℕ)
    (hsync : ReserveSync τ)
    (hstep : TokenizedRemoveLiquidity τ τ' addr shares) :
    ReserveSync τ' := by
  rcases hsync with ⟨hXsync, hYsync⟩
  rcases hstep with ⟨hsol, hbalX, hbalY⟩
  rcases hsol with
    ⟨_hshares_pos, _hshares_le, _hshares_lt, _houtX_le, _houtY_le,
      hresX, hresY, _hL, _hbalAddr, _hbalOther, _hnum, _hden⟩
  refine ⟨?_, ?_⟩
  · calc
      τ'.core.reserveX = τ.core.reserveX - removeX τ.core shares := hresX
      _ = τ.tokenBalX - removeX τ.core shares := by simp [hXsync]
      _ = τ'.tokenBalX := by simp [hbalX]
  · calc
      τ'.core.reserveY = τ.core.reserveY - removeY τ.core shares := hresY
      _ = τ.tokenBalY - removeY τ.core shares := by simp [hYsync]
      _ = τ'.tokenBalY := by simp [hbalY]

/-- Abstract validity is preserved by tokenized swapXforY (via projection simulation). -/
theorem valid_preserved_tokenizedSwapXforY
    (τ τ' : TokenizedStorage) (dx : ℕ)
    (hv : Valid (alphaTokenized τ))
    (hstep : TokenizedSwapXforY τ τ' dx) :
    Valid (alphaTokenized τ') := by
  exact valid_preserved_soliditySwapXforY τ.core τ'.core dx hv hstep.1

/-- Abstract validity is preserved by tokenized swapYforX (via projection simulation). -/
theorem valid_preserved_tokenizedSwapYforX
    (τ τ' : TokenizedStorage) (dy : ℕ)
    (hv : Valid (alphaTokenized τ))
    (hstep : TokenizedSwapYforX τ τ' dy) :
    Valid (alphaTokenized τ') := by
  exact valid_preserved_soliditySwapYforX τ.core τ'.core dy hv hstep.1

/-- Abstract validity is preserved by tokenized addLiquidity (via projection simulation). -/
theorem valid_preserved_tokenizedAddLiquidity
    (τ τ' : TokenizedStorage) (addr : SolAddress) (dx dy : ℕ)
    (hv : Valid (alphaTokenized τ))
    (hstep : TokenizedAddLiquidity τ τ' addr dx dy) :
    Valid (alphaTokenized τ') := by
  exact valid_preserved_solidityAddLiquidity τ.core τ'.core addr dx dy hv hstep.1

/-- Abstract validity is preserved by tokenized removeLiquidity (via projection simulation). -/
theorem valid_preserved_tokenizedRemoveLiquidity
    (τ τ' : TokenizedStorage) (addr : SolAddress) (shares : ℕ)
    (hv : Valid (alphaTokenized τ))
    (hstep : TokenizedRemoveLiquidity τ τ' addr shares) :
    Valid (alphaTokenized τ') := by
  exact valid_preserved_solidityRemoveLiquidity τ.core τ'.core addr shares hv hstep.1

/-- One tokenized concrete transition step. -/
inductive TokenizedStep : TokenizedStorage → TokenizedStorage → Prop
  | swapXforY {τ τ' : TokenizedStorage} (dx : ℕ)
      (h : TokenizedSwapXforY τ τ' dx) :
      TokenizedStep τ τ'
  | swapYforX {τ τ' : TokenizedStorage} (dy : ℕ)
      (h : TokenizedSwapYforX τ τ' dy) :
      TokenizedStep τ τ'
  | addLiquidity {τ τ' : TokenizedStorage} (addr : SolAddress) (dx dy : ℕ)
      (h : TokenizedAddLiquidity τ τ' addr dx dy) :
      TokenizedStep τ τ'
  | removeLiquidity {τ τ' : TokenizedStorage} (addr : SolAddress) (shares : ℕ)
      (h : TokenizedRemoveLiquidity τ τ' addr shares) :
      TokenizedStep τ τ'

/-- Reserve-sync and abstract validity are jointly preserved by one tokenized step. -/
theorem validAndSync_preserved_tokenizedStep
    {τ τ' : TokenizedStorage}
    (hv : Valid (alphaTokenized τ))
    (hsync : ReserveSync τ)
    (hstep : TokenizedStep τ τ') :
    Valid (alphaTokenized τ') ∧ ReserveSync τ' := by
  cases hstep with
  | swapXforY dx h =>
      refine ⟨valid_preserved_tokenizedSwapXforY τ τ' dx hv h,
        reserveSync_preserved_tokenizedSwapXforY τ τ' dx hsync h⟩
  | swapYforX dy h =>
      refine ⟨valid_preserved_tokenizedSwapYforX τ τ' dy hv h,
        reserveSync_preserved_tokenizedSwapYforX τ τ' dy hsync h⟩
  | addLiquidity addr dx dy h =>
      refine ⟨valid_preserved_tokenizedAddLiquidity τ τ' addr dx dy hv h,
        reserveSync_preserved_tokenizedAddLiquidity τ τ' addr dx dy hsync h⟩
  | removeLiquidity addr shares h =>
      refine ⟨valid_preserved_tokenizedRemoveLiquidity τ τ' addr shares hv h,
        reserveSync_preserved_tokenizedRemoveLiquidity τ τ' addr shares hsync h⟩

/-- Reachability by finite sequences of tokenized steps. -/
inductive TokenizedReachable : TokenizedStorage → TokenizedStorage → Prop
  | refl (τ : TokenizedStorage) : TokenizedReachable τ τ
  | tail {τ₁ τ₂ τ₃ : TokenizedStorage}
      (h12 : TokenizedStep τ₁ τ₂)
      (h23 : TokenizedReachable τ₂ τ₃) :
      TokenizedReachable τ₁ τ₃

/-- Validity and reserve-sync are preserved along arbitrary tokenized traces. -/
theorem validAndSync_preserved_tokenizedReachable
    {τ τ' : TokenizedStorage}
    (hreach : TokenizedReachable τ τ')
    (hv : Valid (alphaTokenized τ))
    (hsync : ReserveSync τ) :
    Valid (alphaTokenized τ') ∧ ReserveSync τ' := by
  induction hreach with
  | refl _ =>
      exact ⟨hv, hsync⟩
  | tail h12 h23 ih =>
      rcases validAndSync_preserved_tokenizedStep hv hsync h12 with ⟨hv2, hsync2⟩
      exact ih hv2 hsync2
