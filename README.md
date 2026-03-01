# CPAMM Lean

[![CI](https://github.com/SproutSeeds/cpamm-lean/actions/workflows/ci.yml/badge.svg)](https://github.com/SproutSeeds/cpamm-lean/actions/workflows/ci.yml)

Formally verified constant-product AMM artifact:
- Lean 4 model and proofs over rationals (`CPAMM/*.lean`)
- Solidity implementation (`solidity/src/CPAMM.sol`)
- ERC20-backed Solidity extension (`solidity/src/CPAMMTokenized.sol`)
- Foundry tests (`solidity/test/CPAMM.t.sol`)
- Refinement layer from Solidity storage relations to Lean transitions

## Pinned Toolchain

- Lean: `leanprover/lean4:v4.26.0` (`lean-toolchain`)
- Solidity compiler: `0.8.30` (exact pragma + `foundry.toml`)
- Foundry (CI): `1.5.1`
- Slither: `0.11.4` (`scripts/security/slither.sh`)

## Quick Start

Run full reproduction (Lean + Solidity):

```bash
./scripts/repro.sh
```

## Security Validation

Run differential fuzzing + baseline test suite:

```bash
cd solidity
~/.foundry/bin/forge test
```

Differential coverage includes swap/add/remove checks plus a mixed-operation stateful shadow-model fuzz test.
The suite also includes a Foundry invariant campaign (`CPAMM.Invariant.t.sol`) with a two-actor stateful handler.
An ERC20-backed integration suite (`CPAMM.Tokenized.t.sol`) checks reserve/token-balance consistency and fee-on-transfer rejection.

Run Slither static analysis:

```bash
./scripts/security/slither.sh
```

See triaged findings in [`security/SECURITY_VALIDATION.md`](security/SECURITY_VALIDATION.md).
External reviewer assumptions and scope boundaries are summarized in [`security/AUDIT_README.md`](security/AUDIT_README.md).
CI runs this gate and fails on any non-triaged detector findings.

Each CI run also publishes artifacts for review:
- Lean cache/build logs
- Forge test log + JSON report + coverage output (`lcov.info`)
- Slither log + SARIF report

CI enforcement now includes:
- pinned Lean action SHA (`leanprover/lean-action@c544e896...`)
- coverage threshold gate for `src/CPAMM.sol` (lines/statements must remain `100%`; branch coverage has a floor gate)
- SARIF upload to GitHub Security for Slither findings
- cached/retried Slither toolchain setup in CI for stability

## What Is Proved

- State validity invariants are preserved across add/remove/swap relations
- LP accounting consistency is preserved for add/remove liquidity
- Constant product is preserved at zero fee and nondecreasing with positive fee
- Output is bounded by reserves
- Integer floor-division bounds and reserve-positivity rounding safety
- Full-withdrawal terminal boundary at abstract level:
  - `terminal_preserved_removeLiquidityTerminal`
  - `validOrTerminal_preserved_removeLiquidityBoundary`
- Refinement simulation theorems for:
  - `sim_swapXforY`
  - `sim_swapYforX`
  - `sim_addLiquidity`
  - `sim_addLiquidity_bootstrap`
  - `sim_removeLiquidity`
- Trace-level Solidity validity preservation for arbitrary finite step sequences

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
  src/CPAMMTokenized.sol
  test/CPAMM.t.sol
  test/CPAMM.Tokenized.t.sol
.github/workflows/ci.yml
VERIFICATION.md
scripts/repro.sh
```

## Notes On Scope

This is a minimal verifiable AMM core artifact (no oracle/TWAP/governance/upgrade logic).
Refinement for swaps and liquidity operations is modeled with integer-floor arithmetic and explicit ±1 bounds against exact rational quantities, documented in [`VERIFICATION.md`](VERIFICATION.md).
The Solidity contract intentionally enforces `shares < totalSupply` on `removeLiquidity`; the `dL = L` full-withdrawal case is modeled and proved only at the abstract Lean boundary layer.
`CPAMMTokenized.sol` extends this with real ERC20 transfers and reserve/balance checks; it is currently test-validated (not yet part of the Lean refinement proof chain).
