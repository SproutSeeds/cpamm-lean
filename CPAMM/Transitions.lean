import CPAMM.State

/-!
  CPAMM-1 Phase 1: Transition Relations

  Each operation is modeled as a relation (`Prop`) between pre-state and post-state.
  Preconditions are conjuncts in the relation.
-/

/-- Output amount for a swap of `dx` input tokens, given reserves `x`, `y` and fee `f`. -/
def dy_of_swap (x y f dx : ℚ) : ℚ :=
  let dx_eff := dx * (1 - f)
  y * dx_eff / (x + dx_eff)

/-- Relation describing a valid addLiquidity transition. -/
def AddLiquidity {α : Type*} [DecidableEq α]
    (s s' : CpammState α) (addr : α) (dx dy : ℚ) : Prop :=
  dx > 0 ∧
  dy > 0 ∧
  (s.L > 0 → dx * s.y = dy * s.x) ∧
  s'.x = s.x + dx ∧
  s'.y = s.y + dy ∧
  s'.L = (if s.L = 0 then dx else s.L + s.L * dx / s.x) ∧
  s'.balances addr = s.balances addr + (s'.L - s.L) ∧
  (∀ a : α, a ≠ addr → s'.balances a = s.balances a) ∧
  s'.f = s.f

/-- Relation describing a valid removeLiquidity transition. -/
def RemoveLiquidity {α : Type*} [DecidableEq α]
    (s s' : CpammState α) (addr : α) (dL : ℚ) : Prop :=
  0 < dL ∧
  dL ≤ s.balances addr ∧
  dL < s.L ∧
  s'.x = s.x - s.x * dL / s.L ∧
  s'.y = s.y - s.y * dL / s.L ∧
  s'.L = s.L - dL ∧
  s'.balances addr = s.balances addr - dL ∧
  (∀ a : α, a ≠ addr → s'.balances a = s.balances a) ∧
  s'.f = s.f

/-- Relation describing a valid swapXforY transition. -/
def SwapXforY {α : Type*}
    (s s' : CpammState α) (dx : ℚ) : Prop :=
  dx > 0 ∧
  let dy := dy_of_swap s.x s.y s.f dx
  dy > 0 ∧
  s'.x = s.x + dx ∧
  s'.y = s.y - dy ∧
  s'.y > 0 ∧
  s'.L = s.L ∧
  s'.balances = s.balances ∧
  s'.f = s.f

/-- Relation describing a valid swapYforX transition. -/
def SwapYforX {α : Type*}
    (s s' : CpammState α) (dy : ℚ) : Prop :=
  dy > 0 ∧
  let dx := dy_of_swap s.y s.x s.f dy
  dx > 0 ∧
  s'.y = s.y + dy ∧
  s'.x = s.x - dx ∧
  s'.x > 0 ∧
  s'.L = s.L ∧
  s'.balances = s.balances ∧
  s'.f = s.f

/-- A state is consistent if LP supply equals the sum of all LP balances. -/
def Consistent {α : Type*} [Fintype α] [DecidableEq α] (s : CpammState α) : Prop :=
  s.L = Finset.univ.sum s.balances
