# CPAMM-1 Implementation Plan
## Handoff Document for Codex

This document is the single source of truth for completing the CPAMM-1 project.
Read it fully before touching any file. Execute phases in order. Do not skip ahead.

---

## What Is This Project

A formally verified constant-product AMM (like Uniswap v2) with:
- A Lean 4 abstract model over ℚ (rationals) with proved invariants
- A Solidity implementation with Foundry tests
- A refinement layer proving the Solidity corresponds to the Lean model
- A verification dossier

**Why it matters:** DeFi protocols get hacked for hundreds of millions. This artifact
demonstrates Lean 4 theorem-proving discipline applied to AMM invariants — almost
nobody in the DeFi security space is doing this. It is a commercial portfolio piece.

---

## Repo

Local path: `/Users/codymitchell/documents/code/cpamm-lean`
GitHub: https://github.com/SproutSeeds/cpamm-lean
Lean version: `leanprover/lean4:v4.26.0`
Mathlib version: `v4.26.0`

Build command: `~/.elan/bin/lake build`
Cache command: `~/.elan/bin/lake exe cache get`

---

## What Is Already Done

### `CPAMM/State.lean` ✅ COMPLETE — DO NOT MODIFY

Defines:
- `CpammState α` — abstract state struct over ℚ, parameterized by address type `α`
- `Valid` — predicate: x > 0, y > 0, L ≥ 0, all balances ≥ 0, 0 ≤ f < 1
- `product` — x * y
- `product_pos` — proved theorem: valid state has positive product

### `CPAMM.lean` — root imports file

Currently contains only `import CPAMM.State`.
Add each new file here as it is created.

### Build

Passes clean. 7745 jobs. No errors. No sorry.

---

## Execution Order

Do not reorder. Each phase depends on the previous.

```
Phase 1: Transitions.lean         ← start here
Phase 2: Invariants.lean          ← after Phase 1 builds clean
Phase 3: Economics.lean           ← after Phase 2 builds clean
Phase 4: Solidity + Foundry       ← after Phase 3 builds clean
Phase 5: Rounding.lean            ← after Phase 4
Phase 6: Refinement.lean          ← after Phase 5
Phase 7: VERIFICATION.md + CI     ← last
                                  ← DeFi outreach begins here
```

After each phase: run `lake build`, confirm clean, then commit and push.

---

## PHASE 1 — Transitions

**File:** `CPAMM/Transitions.lean`
**Import:** `import CPAMM.State`

Define each AMM operation as a **relation** (a `Prop`, not a function).
Relations are the right abstraction — precondition failure simply means
no valid transition exists, which is exactly what we want for proofs.

---

### Helper: `dy_of_swap`

Define this first. It computes the output amount for a swap.

```lean
/-- Output amount for a swap of dx input tokens, given reserves x, y and fee f. -/
def dy_of_swap (x y f dx : ℚ) : ℚ :=
  let dx_eff := dx * (1 - f)
  y * dx_eff / (x + dx_eff)
```

---

### `AddLiquidity`

```lean
/-- Relation describing a valid addLiquidity transition. -/
def AddLiquidity {α : Type*} [DecidableEq α]
    (s s' : CpammState α) (addr : α) (dx dy : ℚ) : Prop :=
  -- Preconditions
  dx > 0 ∧
  dy > 0 ∧
  (s.L > 0 → dx * s.y = dy * s.x) ∧  -- proportionality if pool initialized
  -- Postconditions
  s'.x = s.x + dx ∧
  s'.y = s.y + dy ∧
  s'.L = if s.L = 0 then dx
         else s.L + s.L * dx / s.x ∧
  s'.balances addr = s.balances addr + (s'.L - s.L) ∧
  (∀ a : α, a ≠ addr → s'.balances a = s.balances a) ∧
  s'.f = s.f
```

---

### `RemoveLiquidity`

```lean
/-- Relation describing a valid removeLiquidity transition. -/
def RemoveLiquidity {α : Type*} [DecidableEq α]
    (s s' : CpammState α) (addr : α) (dL : ℚ) : Prop :=
  -- Preconditions
  0 < dL ∧
  dL ≤ s.balances addr ∧
  dL < s.L ∧  -- strictly less: ensures x', y' stay positive after withdrawal
  -- Postconditions
  s'.x = s.x - s.x * dL / s.L ∧
  s'.y = s.y - s.y * dL / s.L ∧
  s'.L = s.L - dL ∧
  s'.balances addr = s.balances addr - dL ∧
  (∀ a : α, a ≠ addr → s'.balances a = s.balances a) ∧
  s'.f = s.f
```

---

### `SwapXforY`

```lean
/-- Relation describing a valid swapXforY transition. -/
def SwapXforY {α : Type*}
    (s s' : CpammState α) (dx : ℚ) : Prop :=
  -- Preconditions
  dx > 0 ∧
  -- The output amount is determined by dy_of_swap
  let dy := dy_of_swap s.x s.y s.f dx
  -- Postconditions
  dy > 0 ∧
  s'.x = s.x + dx ∧
  s'.y = s.y - dy ∧
  s'.y > 0 ∧
  s'.L = s.L ∧
  s'.balances = s.balances ∧
  s'.f = s.f
```

Note: `addr` is not needed for swaps in the abstract model — the swap
just changes reserves. Balances track LP tokens only, not token holdings.

**Lean `let` formatting note:** Inside `Prop` definitions, use `let dx_eff := ...; ...`
(semicolon-separated) not `let dx_eff := ...\n ...` to avoid parser issues. Example:
```lean
let dx_eff := dx * (1 - s.f); let dy := s.y * dx_eff / (s.x + dx_eff); dy > 0 ∧ ...
```
Or define `dy_of_swap` as a separate `def` and reference it directly — which is cleaner.

---

### `SwapYforX`

Symmetric to `SwapXforY`. Swap the roles of x and y throughout.

```lean
/-- Relation describing a valid swapYforX transition. -/
def SwapYforX {α : Type*}
    (s s' : CpammState α) (dy : ℚ) : Prop :=
  -- Preconditions
  dy > 0 ∧
  -- Output amount: dx = x * dy_eff / (y + dy_eff)
  let dx := dy_of_swap s.y s.x s.f dy
  -- Postconditions
  dx > 0 ∧
  s'.y = s.y + dy ∧
  s'.x = s.x - dx ∧
  s'.x > 0 ∧
  s'.L = s.L ∧
  s'.balances = s.balances ∧
  s'.f = s.f
```

---

### `Consistent` predicate

Also define this in `Transitions.lean`. It will be needed for invariant proofs.

```lean
/-- A state is consistent if LP supply equals the sum of all LP balances. -/
def Consistent {α : Type*} [DecidableEq α] [Fintype α] (s : CpammState α) : Prop :=
  s.L = Finset.univ.sum s.balances
```

---

### After Phase 1

Add to `CPAMM.lean`:
```lean
import CPAMM.Transitions
```

Run `lake build`. Must succeed. Commit and push.

---

## PHASE 2 — Safety Invariants

**File:** `CPAMM/Invariants.lean`
**Import:** `import CPAMM.Transitions`

Prove the following theorems. All must be **sorry-free**.

---

### 2.1 `valid_preserved_addLiquidity`

```lean
theorem valid_preserved_addLiquidity
    {α : Type*} [DecidableEq α] (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (ht : AddLiquidity s s' addr dx dy) :
    Valid s'
```

---

### 2.2 `valid_preserved_removeLiquidity`

```lean
theorem valid_preserved_removeLiquidity
    {α : Type*} [DecidableEq α] (s s' : CpammState α) (addr : α) (dL : ℚ)
    (hv : Valid s)
    (ht : RemoveLiquidity s s' addr dL) :
    Valid s'
```

---

### 2.3 `valid_preserved_swapXforY`

```lean
theorem valid_preserved_swapXforY
    {α : Type*} (s s' : CpammState α) (dx : ℚ)
    (hv : Valid s)
    (ht : SwapXforY s s' dx) :
    Valid s'
```

---

### 2.4 `valid_preserved_swapYforX`

```lean
theorem valid_preserved_swapYforX
    {α : Type*} (s s' : CpammState α) (dy : ℚ)
    (hv : Valid s)
    (ht : SwapYforX s s' dy) :
    Valid s'
```

---

### 2.5 `consistent_preserved_addLiquidity`

LP accounting is preserved: if the state is consistent before, it is after.

```lean
theorem consistent_preserved_addLiquidity
    {α : Type*} [DecidableEq α] [Fintype α]
    (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (hc : Consistent s)
    (ht : AddLiquidity s s' addr dx dy) :
    Consistent s'
```

---

### 2.6 `consistent_preserved_removeLiquidity`

```lean
theorem consistent_preserved_removeLiquidity
    {α : Type*} [DecidableEq α] [Fintype α]
    (s s' : CpammState α) (addr : α) (dL : ℚ)
    (hv : Valid s)
    (hc : Consistent s)
    (ht : RemoveLiquidity s s' addr dL) :
    Consistent s'
```

---

### After Phase 2

Add to `CPAMM.lean`:
```lean
import CPAMM.Invariants
```

Run `lake build`. Must succeed. Commit and push.

---

## PHASE 3 — Economic Theorems

**File:** `CPAMM/Economics.lean`
**Import:** `import CPAMM.Invariants`

Prove the following theorems. All must be **sorry-free**.

---

### 3.1 `product_preserved_swap_no_fee`

Without fee: constant product is exactly preserved.

```lean
theorem product_preserved_swap_no_fee
    {α : Type*} (s s' : CpammState α) (dx : ℚ)
    (hv : Valid s)
    (hf : s.f = 0)
    (ht : SwapXforY s s' dx) :
    product s' = product s
```

---

### 3.2 `product_nondecreasing_swap_with_fee`

With fee: product is monotonically non-decreasing.

```lean
theorem product_nondecreasing_swap_with_fee
    {α : Type*} (s s' : CpammState α) (dx : ℚ)
    (hv : Valid s)
    (hf : s.f > 0)
    (ht : SwapXforY s s' dx) :
    product s' ≥ product s
```

---

### 3.3 `output_bounded_by_reserve`

Swap output cannot exceed or equal the available reserve.

```lean
theorem output_bounded_by_reserve
    {α : Type*} (s s' : CpammState α) (dx : ℚ)
    (hv : Valid s)
    (ht : SwapXforY s s' dx) :
    s.y - s'.y < s.y
```

---

### 3.4 `remove_liquidity_proportional`

Liquidity removal returns exactly proportional share of each reserve.

```lean
theorem remove_liquidity_proportional
    {α : Type*} [DecidableEq α] (s s' : CpammState α) (addr : α) (dL : ℚ)
    (hv : Valid s)
    (ht : RemoveLiquidity s s' addr dL) :
    (s.x - s'.x) / s.x = (s.y - s'.y) / s.y
```

---

### After Phase 3

Add to `CPAMM.lean`:
```lean
import CPAMM.Economics
```

Run `lake build`. Must succeed. Commit and push.

---

## PHASE 4 — Solidity Implementation

**Directory structure to create:**

```
cpamm-lean/
  solidity/
    src/
      CPAMM.sol
    test/
      CPAMM.t.sol
    foundry.toml
```

**Setup:**
```bash
cd /Users/codymitchell/documents/code/cpamm-lean
mkdir -p solidity/src solidity/test
cd solidity
forge init --no-git --force .
```

---

### `solidity/src/CPAMM.sol`

Implement a minimal two-token constant-product AMM.

Requirements:
- Solidity ^0.8.20 (checked arithmetic built-in)
- No flash loans, no oracle, no TWAP, no upgrades, no governance
- Fee stored as `feeNumerator / feeDenominator` (e.g. 3/1000)
- Integer division with floor rounding throughout
- All arithmetic uses checked overflow (default in 0.8.x)

State variables:
```solidity
uint256 public reserveX;
uint256 public reserveY;
uint256 public totalSupply;
mapping(address => uint256) public balanceOf;
uint256 public immutable feeNumerator;
uint256 public immutable feeDenominator;
```

Functions:
```solidity
constructor(uint256 _feeNumerator, uint256 _feeDenominator)
function addLiquidity(uint256 dx, uint256 dy) external returns (uint256 shares)
function removeLiquidity(uint256 shares) external returns (uint256 dx, uint256 dy)
function swapXforY(uint256 dx) external returns (uint256 dy)
function swapYforX(uint256 dy) external returns (uint256 dx)
```

Swap formula (fee on input):
```
dx_eff = dx * (feeDenominator - feeNumerator) / feeDenominator
dy = reserveY * dx_eff / (reserveX + dx_eff)
```

---

### `solidity/test/CPAMM.t.sol`

Foundry tests. Use `forge-std`.

Required tests:
1. `test_addLiquidity_increases_reserves` — basic sanity
2. `test_removeLiquidity_proportional` — mirrors theorem 3.4
3. `test_swap_product_nondecreasing` — mirrors theorem 3.2
4. `test_swap_output_bounded` — mirrors theorem 3.3
5. `testFuzz_swap_sequence` — fuzz: arbitrary sequence of swaps, reserves always positive
6. `testFuzz_add_remove_roundtrip` — fuzz: add then remove, get back proportional amounts
7. `test_edge_tiny_reserves` — swap with reserve = 1
8. `test_edge_large_values` — values near uint256 max / 2

Run tests:
```bash
cd solidity && forge test
```

---

## PHASE 5 — Rounding Bounds

**File:** `CPAMM/Rounding.lean`
**Import:** `import CPAMM.Economics`

Prove that integer floor division used in Solidity cannot violate safety invariants.

---

### 5.1 Floor division bounds

```lean
/-- Floor division underestimates the exact rational result. -/
theorem nat_div_le_rat_div (a b : ℕ) (hb : 0 < b) :
    (a / b : ℕ) ≤ (a : ℚ) / (b : ℚ)

/-- Floor division is within 1 of the exact rational result. -/
theorem rat_div_sub_one_lt_nat_div (a b : ℕ) (hb : 0 < b) :
    (a : ℚ) / (b : ℚ) - 1 < (a / b : ℕ)
```

---

### 5.2 Safety under rounding

```lean
/-- Floor rounding on output preserves positive reserves:
    if dy_floor = dy_of_swap rounded down, then reserveY - dy_floor > 0. -/
theorem reserves_positive_under_rounding
    (x y f dx : ℚ) (hx : x > 0) (hy : y > 0) (hf : 0 ≤ f) (hf1 : f < 1)
    (hdx : dx > 0)
    (dy_floor : ℕ)
    (h_floor : (dy_floor : ℚ) ≤ dy_of_swap x y f dx) :
    y - dy_floor > 0
```

---

### After Phase 5

Add to `CPAMM.lean`:
```lean
import CPAMM.Rounding
```

Run `lake build`. Commit and push.

---

## PHASE 6 — Refinement Layer

**File:** `CPAMM/Refinement.lean`
**Import:** `import CPAMM.Rounding`

This is the hardest phase. Connect the Lean abstract model to the Solidity implementation.

---

### 6.1 Solidity storage model

Model the Solidity contract state in Lean:

```lean
/-- A concrete address type for the Solidity refinement. -/
abbrev SolAddress := ℕ  -- use ℕ as a stand-in for Ethereum addresses

/-- Lean model of the Solidity contract storage. -/
structure SolidityStorage where
  reserveX      : ℕ
  reserveY      : ℕ
  totalSupply   : ℕ
  balanceOf     : SolAddress → ℕ
  feeNumerator  : ℕ
  feeDenominator : ℕ
  h_denom_pos   : 0 < feeDenominator  -- denominator must be positive
```

---

### 6.2 Abstraction map

```lean
/-- Map Solidity storage to the abstract Lean state. -/
def alpha (σ : SolidityStorage) : CpammState SolAddress :=
  { x        := (σ.reserveX : ℚ)
    y        := (σ.reserveY : ℚ)
    L        := (σ.totalSupply : ℚ)
    balances := fun a => (σ.balanceOf a : ℚ)
    f        := (σ.feeNumerator : ℚ) / (σ.feeDenominator : ℚ) }
```

---

### 6.3 Solidity transition relations

Model each Solidity function as a relation on `SolidityStorage`.
These model the exact integer arithmetic the Solidity contract performs.

```lean
/-- Solidity swapXforY: integer arithmetic with floor rounding. -/
def SoliditySwapXforY (σ σ' : SolidityStorage) (dx : ℕ) : Prop :=
  let dx_eff := dx * (σ.feeDenominator - σ.feeNumerator) / σ.feeDenominator
  let dy     := σ.reserveY * dx_eff / (σ.reserveX + dx_eff)
  dy > 0 ∧
  σ'.reserveX      = σ.reserveX + dx ∧
  σ'.reserveY      = σ.reserveY - dy ∧
  σ'.totalSupply   = σ.totalSupply ∧
  σ'.balanceOf     = σ.balanceOf ∧
  σ'.feeNumerator  = σ.feeNumerator ∧
  σ'.feeDenominator = σ.feeDenominator ∧
  σ'.h_denom_pos   = σ.h_denom_pos
```

Define `SolidityAddLiquidity`, `SolidityRemoveLiquidity`, `SoliditySwapYforX` analogously.

---

### 6.4 Forward simulation theorems

For each function, prove that Solidity transitions correspond to valid Lean transitions.

```lean
theorem sim_swapXforY
    (σ σ' : SolidityStorage) (dx : ℕ)
    (hv : Valid (alpha σ))
    (hstep : SoliditySwapXforY σ σ' dx) :
    SwapXforY (alpha σ) (alpha σ') (dx : ℚ)
```

```lean
theorem sim_addLiquidity
    (σ σ' : SolidityStorage) (addr : SolAddress) (dx dy : ℕ)
    (hv : Valid (alpha σ))
    (hstep : SolidityAddLiquidity σ σ' addr dx dy) :
    ∃ dx' dy' : ℚ, AddLiquidity (alpha σ) (alpha σ') addr dx' dy'
```

```lean
theorem sim_removeLiquidity
    (σ σ' : SolidityStorage) (addr : SolAddress) (dL : ℕ)
    (hv : Valid (alpha σ))
    (hstep : SolidityRemoveLiquidity σ σ' addr dL) :
    ∃ dL' : ℚ, RemoveLiquidity (alpha σ) (alpha σ') addr dL'
```

**If full forward simulation is too complex:** bounded simulation is acceptable.
Document the explicit integer bounds and prove safety holds within them.
Use `sorry` only as a last resort and document it explicitly in `VERIFICATION.md`.

---

### After Phase 6

Add to `CPAMM.lean`:
```lean
import CPAMM.Refinement
```

Run `lake build`. Must succeed. Commit and push.

---

## PHASE 7 — Verification Dossier + CI

### `VERIFICATION.md`

Must contain:
- List of every proved theorem with file name and theorem name
- Exact scope of refinement (what is proved, what is not)
- Explicit rounding bounds (from `Rounding.lean`)
- Assumptions (e.g. `SolAddress = ℕ`, `Fintype` constraint for accounting)
- Non-goals: flash loan protection, reentrancy, gas optimization, upgrades
- Any remaining `sorry` with explanation
- Reproduction instructions:
  ```bash
  ~/.elan/bin/lake exe cache get
  ~/.elan/bin/lake build
  cd solidity && forge test
  ```

### `.github/workflows/ci.yml`

```yaml
name: CI
on: [push, pull_request]
jobs:
  lean:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: leanprover/lean4-action@v1
      - run: lake exe cache get
      - run: lake build
  solidity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: foundry-rs/foundry-toolchain@v1
      - run: cd solidity && forge test
```

---

## Hard Constraints

- **No sorry in Phases 1–3.** Every theorem must be machine-checked.
- **Phases 5–6 may use sorry only for bounded simulation gaps.** Document each one.
- **No scope expansion.** No flash loans, no TWAP, no oracle, no governance, no upgrades.
- **No feature creep.** Minimal provable core only.
- **`lake build` must pass** after every file addition before moving to the next phase.
- **`forge test` must pass** before moving to Phase 5.
- **Commit and push after each phase.**
- Never commit `.lake/` — it is already in `.gitignore`.

---

## Definition of Done

DONE means:
- `lake build` succeeds with zero errors
- `forge test` passes with fuzzing enabled
- `VERIFICATION.md` is complete
- No unacknowledged sorry in any claimed theorem
- Scope respected exactly as specified

---

## Repo Structure When Complete

```
cpamm-lean/
  CPAMM/
    State.lean          ✅ done
    Transitions.lean
    Invariants.lean
    Economics.lean
    Rounding.lean
    Refinement.lean
  solidity/
    src/CPAMM.sol
    test/CPAMM.t.sol
    foundry.toml
  CPAMM.lean
  VERIFICATION.md
  lakefile.toml
  lean-toolchain
  .gitignore
  .github/workflows/ci.yml
```

---

## Current State

- `lake build` passes. 7745 jobs. No errors. No sorry.
- `CPAMM/State.lean` is the only file.
- `CPAMM.lean` imports only `CPAMM.State`.

**Start now: write `CPAMM/Transitions.lean`.**
