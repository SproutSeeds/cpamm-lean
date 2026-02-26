# CPAMM-1 Implementation Plan
## Handoff Document for Co-Worker

This document is the single source of truth for completing the CPAMM-1 project.
Read it fully before touching any file.

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

`/Users/codymitchell/documents/code/cpamm-lean`
GitHub: https://github.com/SproutSeeds/cpamm-lean

---

## What Is Already Done

### `CPAMM/State.lean` ✅ COMPLETE

Defines:
- `CpammState α` — abstract state struct over ℚ
  - `x y L : ℚ` (reserves, LP supply)
  - `balances : α → ℚ` (per-address LP balances)
  - `f : ℚ` (fee fraction)
- `Valid` — predicate: x > 0, y > 0, L ≥ 0, balances ≥ 0, 0 ≤ f < 1
- `product` — x * y
- `product_pos` — proved theorem: valid state has positive product

**Builds clean. No sorry. Do not modify.**

---

## What Needs To Be Built

---

### PHASE 1 — Transitions (next file)

**File:** `CPAMM/Transitions.lean`

Define each AMM operation as a **relation** (not a function).
Relations are the right abstraction — they allow precondition failure
to simply mean no valid transition exists.

Import: `import CPAMM.State`

#### 1.1 `AddLiquidity`

```
AddLiquidity (s s' : CpammState α) (addr : α) (dx dy : ℚ) : Prop
```

Preconditions:
- `dx > 0`
- `dy > 0`
- If `s.L > 0`: proportionality must hold: `dx / s.x = dy / s.y`
  (equivalently: `dx * s.y = dy * s.x`)

Postconditions:
- `s'.x = s.x + dx`
- `s'.y = s.y + dy`
- If `s.L = 0`: `s'.L = dx` (initial mint, arbitrary convention)
- If `s.L > 0`: `s'.L = s.L * (1 + dx / s.x)`
  (equivalently: `s'.L = s.L + s.L * dx / s.x`)
- LP minted to addr: `s'.balances addr = s.balances addr + (s'.L - s.L)`
- All other balances unchanged: `∀ a ≠ addr, s'.balances a = s.balances a`
- `s'.f = s.f`

#### 1.2 `RemoveLiquidity`

```
RemoveLiquidity (s s' : CpammState α) (addr : α) (dL : ℚ) : Prop
```

Preconditions:
- `0 < dL`
- `dL ≤ s.balances addr`
- `s.L > 0`

Postconditions (proportional share):
- `s'.x = s.x - s.x * dL / s.L`
- `s'.y = s.y - s.y * dL / s.L`
- `s'.L = s.L - dL`
- `s'.balances addr = s.balances addr - dL`
- All other balances unchanged
- `s'.f = s.f`

#### 1.3 `SwapXforY`

```
SwapXforY (s s' : CpammState α) (addr : α) (dx dy : ℚ) : Prop
```

Preconditions:
- `dx > 0`

Effective input (fee applied to input):
- `dx_eff = dx * (1 - s.f)`

Constant-product equation determines `dy`:
- `(s.x + dx_eff) * (s.y - dy) = s.x * s.y`
- Solving: `dy = s.y * dx_eff / (s.x + dx_eff)`

Postconditions:
- `s'.x = s.x + dx`
- `s'.y = s.y - dy`
- `dy > 0`
- `s'.y > 0`
- Balances and L unchanged
- `s'.f = s.f`

#### 1.4 `SwapYforX`

Symmetric to `SwapXforY`. Swap x and y throughout.

#### Helper: `dy_of_swap`

Define a helper function computing the output amount:
```
dy_of_swap (x y f dx : ℚ) : ℚ :=
  let dx_eff := dx * (1 - f)
  y * dx_eff / (x + dx_eff)
```

This makes the transition definition and later proofs cleaner.

#### Verification

After writing `Transitions.lean`, add it to `CPAMM.lean`:
```
import CPAMM.Transitions
```

Run `lake build`. Must succeed with no errors.

---

### PHASE 2 — Safety Invariants

**File:** `CPAMM/Invariants.lean`

Import: `import CPAMM.Transitions`

Prove these five theorems. All must be sorry-free.

#### 2.1 `valid_preserved_addLiquidity`
```
theorem valid_preserved_addLiquidity
    {α : Type*} (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (ht : AddLiquidity s s' addr dx dy) :
    Valid s'
```

#### 2.2 `valid_preserved_removeLiquidity`
```
theorem valid_preserved_removeLiquidity
    {α : Type*} (s s' : CpammState α) (addr : α) (dL : ℚ)
    (hv : Valid s)
    (ht : RemoveLiquidity s s' addr dL) :
    Valid s'
```

#### 2.3 `valid_preserved_swapXforY`
```
theorem valid_preserved_swapXforY
    {α : Type*} (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (ht : SwapXforY s s' addr dx dy) :
    Valid s'
```

#### 2.4 `valid_preserved_swapYforX`
```
theorem valid_preserved_swapYforX
    {α : Type*} (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (ht : SwapYforX s s' addr dx dy) :
    Valid s'
```

#### 2.5 `lp_supply_eq_sum_balances`
Accounting consistency: LP supply equals sum of all balances.
This requires a `Fintype` constraint on the address type.
```
theorem lp_supply_eq_sum_balances
    {α : Type*} [Fintype α] (s : CpammState α)
    (hv : Valid s)
    (hc : s.L = Finset.univ.sum s.balances) :
    s.L ≥ 0
```
Note: the full accounting consistency is a precondition/invariant of the
system, not derivable from Valid alone. State it as a separate predicate
`Consistent` if needed.

---

### PHASE 3 — Economic Theorems

**File:** `CPAMM/Economics.lean`

Import: `import CPAMM.Invariants`

Prove these theorems. All must be sorry-free.

#### 3.1 `product_preserved_swap_no_fee`
Without fee (f = 0): constant product is exactly preserved.
```
theorem product_preserved_swap_no_fee
    {α : Type*} (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (hf : s.f = 0)
    (ht : SwapXforY s s' addr dx dy) :
    product s' = product s
```

#### 3.2 `product_nondecreasing_swap_with_fee`
With fee (f > 0): product is monotonically non-decreasing.
```
theorem product_nondecreasing_swap_with_fee
    {α : Type*} (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (hf : s.f > 0)
    (ht : SwapXforY s s' addr dx dy) :
    product s' ≥ product s
```

#### 3.3 `output_bounded_by_reserve`
Swap output cannot exceed available reserve.
```
theorem output_bounded_by_reserve
    {α : Type*} (s s' : CpammState α) (addr : α) (dx dy : ℚ)
    (hv : Valid s)
    (ht : SwapXforY s s' addr dx dy) :
    dy < s.y
```

#### 3.4 `remove_liquidity_proportional`
Liquidity removal returns exactly proportional share.
```
theorem remove_liquidity_proportional
    {α : Type*} (s s' : CpammState α) (addr : α) (dL : ℚ)
    (hv : Valid s)
    (ht : RemoveLiquidity s s' addr dL) :
    s'.x / s.x = s'.y / s.y
```

Complete this phase before moving to Solidity.

---

### PHASE 4 — Solidity Implementation

**Directory:** `solidity/`

**File:** `solidity/src/CPAMM.sol`

Implement a minimal two-token constant-product AMM in Solidity.

Requirements from spec:
- Single pool, two tokens, constant-product, fee on input
- No flash loans, no oracle, no TWAP, no upgrades, no governance
- `uint256` arithmetic with checked overflow
- Fee stored as numerator/denominator pair (e.g. 3/1000 for 0.3%)
- Integer division with floor rounding throughout

Functions to implement:
- `addLiquidity(uint256 dx, uint256 dy) external`
- `removeLiquidity(uint256 dL) external`
- `swapXforY(uint256 dx) external returns (uint256 dy)`
- `swapYforX(uint256 dy) external returns (uint256 dx)`

State variables:
- `uint256 public reserveX`
- `uint256 public reserveY`
- `uint256 public totalSupply`
- `mapping(address => uint256) public balanceOf`
- `uint256 public feeNumerator` (e.g. 3)
- `uint256 public feeDenominator` (e.g. 1000)

**File:** `solidity/test/CPAMM.t.sol` (Foundry tests)

Tests required:
1. Property tests mirroring each invariant
2. Fuzz tests with randomized sequences of operations
3. Invariant: reserves always positive after any sequence
4. Invariant: product non-decreasing after swaps
5. Edge cases: tiny reserves, large values near uint256 max

Setup:
```bash
cd solidity
forge init --no-git
```

---

### PHASE 5 — Refinement Layer

**File:** `CPAMM/Refinement.lean`

Import: `import CPAMM.Economics`

This is the hardest part. Define the abstraction mapping and prove
forward simulation for each function.

#### 5.1 Abstraction Map

Define a function that maps a Solidity storage snapshot to a Lean state:
```
structure SolidityStorage where
  reserveX : ℕ
  reserveY : ℕ
  totalSupply : ℕ
  balanceOf : Address → ℕ
  feeNumerator : ℕ
  feeDenominator : ℕ

def alpha (σ : SolidityStorage) : CpammState Address :=
  { x := σ.reserveX
    y := σ.reserveY
    L := σ.totalSupply
    balances := fun a => σ.balanceOf a
    f := σ.feeNumerator / σ.feeDenominator }
```

Where all ℕ → ℚ coercions are explicit.

#### 5.2 Rounding Bounds

**File:** `CPAMM/Rounding.lean`

Prove integer division bounds:
```
theorem floor_div_le (a b : ℕ) (hb : b > 0) :
    (a / b : ℕ) ≤ (a : ℚ) / b

theorem floor_div_ge (a b : ℕ) (hb : b > 0) :
    (a : ℚ) / b - 1 < (a / b : ℕ)
```

Prove rounding cannot violate safety invariants:
- Even with floor rounding, reserves stay positive
- Product monotonicity holds up to rounding error ε

#### 5.3 Forward Simulation

For each function, prove:
> If Solidity moves from σ to σ', then a valid Lean transition exists from α(σ) to α(σ').

```
theorem sim_swapXforY (σ σ' : SolidityStorage) (addr : Address) (dx : ℕ)
    (hv : Valid (alpha σ))
    (hstep : SoliditySwapXforY σ σ' addr dx) :
    ∃ dy : ℚ, SwapXforY (alpha σ) (alpha σ') addr dx dy
```

If full simulation is too complex, bounded simulation is acceptable:
document the explicit bounds and prove safety holds within them.

---

### PHASE 6 — Verification Dossier + CI

**File:** `VERIFICATION.md`

Must contain:
- List of all proved theorems with file and line references
- Exact scope of refinement (what is proved, what is not)
- Rounding bounds and their proofs
- Assumptions (Fintype on address type, etc.)
- Non-goals (no flash loan protection, no reentrancy, etc.)
- Reproduction instructions (`lake build`, `forge test`)

**File:** `.github/workflows/ci.yml`

CI must:
- Run `lake build` on push
- Run `forge test` on push
- Report pass/fail on both

---

## Execution Order

Do not reorder. Each phase depends on the previous.

```
Phase 1: Transitions.lean         ← write now
Phase 2: Invariants.lean          ← after Phase 1 builds
Phase 3: Economics.lean           ← after Phase 2 builds
Phase 4: Solidity + Foundry       ← after Phase 3 builds
Phase 5: Refinement.lean          ← after Phases 3 and 4
Phase 6: VERIFICATION.md + CI     ← last
                                  ← START DEFI OUTREACH HERE
```

---

## Hard Constraints

- **No sorry in Phases 1-3.** Every theorem must be machine-checked.
- **No scope expansion.** No flash loans, no TWAP, no oracle, no governance.
- **No feature creep.** The minimal provable core is the goal.
- **lake build must pass** after every file addition.
- **Commit after each phase completes.**
- The `.gitignore` already excludes `.lake/`. Never commit build artifacts.

---

## Definition of Done

DONE means:
- `lake build` succeeds with no errors
- `forge test` passes with fuzzing enabled
- `VERIFICATION.md` complete
- No sorry in any claimed theorem
- Scope respected exactly

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
  CPAMM.lean
  VERIFICATION.md
  lakefile.toml
  lean-toolchain
  .gitignore
  .github/workflows/ci.yml
```

---

## Current Build Status

`lake build` passes. 7745 jobs. `CPAMM/State.lean` is the only file so far.

Start with `CPAMM/Transitions.lean`.
