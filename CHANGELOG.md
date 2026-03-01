# Changelog

All notable changes to this project are documented in this file.

## Unreleased

### Added
- Abstract full-withdrawal boundary model in Lean:
  - `RemoveLiquidityTerminal`
  - `Terminal`
  - `ValidOrTerminal`
- Boundary preservation theorems:
  - `terminal_preserved_removeLiquidityTerminal`
  - `validOrTerminal_preserved_removeLiquidityBoundary`
- Solidity unit test `test_removeLiquidity_fullWithdraw_reverts` to lock current contract behavior (`shares < totalSupply`).
- ERC20-backed CPAMM extension contract: `solidity/src/CPAMMTokenized.sol`.
- ERC20-backed integration suite: `solidity/test/CPAMM.Tokenized.t.sol`:
  - reserve/token-balance sync checks across add/remove/swaps
  - fee-on-transfer rejection path
  - multi-step fuzzed sequence with proportional add step generation
- Tokenized verification-track document: `VERIFICATION_TOKENIZED.md`.
- Tokenized Lean refinement module: `CPAMM/TokenizedRefinement.lean` with:
  - tokenized step relations (`TokenizedSwap*`, `TokenizedAddLiquidity`, `TokenizedRemoveLiquidity`)
  - reserve/token-balance sync invariant (`ReserveSync`) and per-step preservation theorems
  - projection/simulation into arithmetic `Solidity*` relations
  - trace-level `validAndSync_preserved_tokenizedReachable`

### Changed
- Verification and audit docs now explicitly distinguish:
  - Solidity/refinement path (`dL < totalSupply`)
  - Abstract terminal-close boundary (`dL = L`)
- Verification docs now include the tokenized refinement theorem inventory and exact-transfer assumption boundary.
- Security validation report now records `25/25` passing tests (including tokenized integration coverage).
- Slither gate scope extended from `solidity/src/CPAMM.sol` to `solidity/src` (core + tokenized extension).
- CI coverage gate now checks both:
  - `src/CPAMM.sol`
  - `src/CPAMMTokenized.sol`

## v1.4.1 - 2026-03-01

### Changed
- CI moved Slither SARIF upload from `github/codeql-action/upload-sarif@v3` to `@v4`.
- CI workflow actions are now fully pinned to immutable commit SHAs (checkout, upload-artifact, setup-python, cache, foundry-toolchain, codeql upload) for stronger reproducibility and supply-chain hardening.

## v1.3 - 2026-02-28

### Added
- Multi-actor Foundry invariant harness for LP accounting correctness across two LP holders.
- Bootstrap add-liquidity simulation theorem (`sim_addLiquidity_bootstrap`) for the `L = 0`, zero-reserve initialization path.
- Abstract floor-preservation theorem for add-liquidity validity (`valid_preserved_addLiquidityFloor`).
- Solidity-layer validity preservation theorem chain for all core operations:
  - `valid_preserved_soliditySwapXforY`
  - `valid_preserved_soliditySwapYforX`
  - `valid_preserved_solidityAddLiquidity`
  - `valid_preserved_solidityRemoveLiquidity`
- Symmetric economic theorem `product_nondecreasing_swapYforX_with_fee`.

### Changed
- CI now pins Lean action by commit SHA for stronger reproducibility.
- CI uploads Slither SARIF into GitHub Security (Code Scanning).
- CI coverage gate now enforces:
  - `src/CPAMM.sol` line coverage = `100%`
  - `src/CPAMM.sol` statement coverage = `100%`
  - `src/CPAMM.sol` branch coverage floor gate
- Documentation updated for theorem inventory, refinement scope, and audit/security workflow.

## v1.4 - 2026-02-28

### Added
- Trace-level Solidity refinement closure in Lean:
  - `SolidityStep`
  - `SolidityReachable`
  - `valid_preserved_solidityStep`
  - `valid_preserved_solidityReachable`

### Changed
- CI security reliability improvements:
  - retry-wrapped pip/slither installs in `scripts/security/slither.sh`
  - `.venv-security` and pip cache reuse in CI security job
- CI SARIF upload made conditional on SARIF file presence to avoid secondary failure masking.

## v1.2 - 2026-02-28

### Added
- Compiler/security hardening to remove `solc-version` warning via Solidity `0.8.30`.
- Stateful invariant campaign and CI artifact/report pipeline.
- External reviewer guide: `security/AUDIT_README.md`.
