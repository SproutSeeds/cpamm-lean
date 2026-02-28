# Changelog

All notable changes to this project are documented in this file.

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

## v1.2 - 2026-02-28

### Added
- Compiler/security hardening to remove `solc-version` warning via Solidity `0.8.30`.
- Stateful invariant campaign and CI artifact/report pipeline.
- External reviewer guide: `security/AUDIT_README.md`.
