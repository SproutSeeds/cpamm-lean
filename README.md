# CPAMM Lean

[![CI](https://github.com/SproutSeeds/cpamm-lean/actions/workflows/ci.yml/badge.svg)](https://github.com/SproutSeeds/cpamm-lean/actions/workflows/ci.yml)

Formally verified constant-product AMM artifact:
- Lean 4 model and proofs over rationals (`CPAMM/*.lean`)
- Solidity implementation (`solidity/src/CPAMM.sol`)
- Foundry tests (`solidity/test/CPAMM.t.sol`)
- Refinement layer from Solidity storage relations to Lean transitions

## Quick Start

Run full reproduction (Lean + Solidity):

```bash
./scripts/repro.sh
```

## What Is Proved

- State validity invariants are preserved across add/remove/swap relations
- LP accounting consistency is preserved for add/remove liquidity
- Constant product is preserved at zero fee and nondecreasing with positive fee
- Output is bounded by reserves
- Integer floor-division bounds and reserve-positivity rounding safety
- Refinement simulation theorems for:
  - `sim_swapXforY`
  - `sim_swapYforX`
  - `sim_addLiquidity`
  - `sim_removeLiquidity`

Full theorem inventory and assumptions are in [`VERIFICATION.md`](VERIFICATION.md).

## Repository Layout

```text
CPAMM/
  State.lean
  Transitions.lean
  Invariants.lean
  Economics.lean
  Rounding.lean
  Refinement.lean
solidity/
  src/CPAMM.sol
  test/CPAMM.t.sol
.github/workflows/ci.yml
VERIFICATION.md
scripts/repro.sh
```

## Notes On Scope

This is a minimal verifiable AMM core artifact (no oracle/TWAP/governance/upgrade logic).
Swap refinement is floor-rounded with explicit output bounds; add/remove refinement currently uses explicit exactness side conditions, documented in [`VERIFICATION.md`](VERIFICATION.md).
