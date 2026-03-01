# CPAMM-1 Verification Dossier

## Proven Theorems

### `CPAMM/State.lean`
- `product_pos`

### `CPAMM/Invariants.lean`
- `valid_preserved_addLiquidity`
- `valid_preserved_removeLiquidity`
- `terminal_preserved_removeLiquidityTerminal`
- `validOrTerminal_preserved_removeLiquidityBoundary`
- `valid_preserved_swapXforY`
- `valid_preserved_swapYforX`
- `consistent_preserved_addLiquidity`
- `consistent_preserved_removeLiquidity`

### `CPAMM/Economics.lean`
- `product_preserved_swap_no_fee`
- `product_nondecreasing_swap_with_fee`
- `product_nondecreasing_swapYforX_with_fee`
- `output_bounded_by_reserve`
- `remove_liquidity_proportional`

### `CPAMM/Rounding.lean`
- `nat_div_le_rat_div`
- `rat_div_sub_one_lt_nat_div`
- `reserves_positive_under_rounding`

### `CPAMM/Refinement.lean`
- `sim_swapXforY`
- `sim_swapYforX`
- `sim_addLiquidity`
- `sim_addLiquidity_bootstrap`
- `sim_removeLiquidity`
- `valid_preserved_swapXforYFloor`
- `valid_preserved_swapYforXFloor`
- `valid_preserved_addLiquidityFloor`
- `valid_preserved_removeLiquidityFloor`
- `valid_preserved_soliditySwapXforY`
- `valid_preserved_soliditySwapYforX`
- `valid_preserved_solidityAddLiquidity`
- `valid_preserved_solidityRemoveLiquidity`
- `valid_preserved_solidityStep`
- `valid_preserved_solidityReachable`

### `CPAMM/TokenizedRefinement.lean`
- `sim_tokenizedSwapXforY`
- `sim_tokenizedSwapYforX`
- `sim_tokenizedAddLiquidity`
- `sim_tokenizedRemoveLiquidity`
- `sim_tokenizedStep_to_solidityStep`
- `sim_tokenizedReachable_to_solidityReachable`
- `reserveSync_preserved_tokenizedSwapXforY`
- `reserveSync_preserved_tokenizedSwapYforX`
- `reserveSync_preserved_tokenizedAddLiquidity`
- `reserveSync_preserved_tokenizedRemoveLiquidity`
- `valid_preserved_tokenizedSwapXforY`
- `valid_preserved_tokenizedSwapYforX`
- `valid_preserved_tokenizedAddLiquidity`
- `valid_preserved_tokenizedRemoveLiquidity`
- `valid_preserved_tokenizedStep`
- `reserveSync_preserved_tokenizedStep`
- `validAndSync_preserved_tokenizedStep`
- `validAndSync_preserved_tokenizedReachable`

### `CPAMM/TokenizedBehavior.lean`
- `supportedTokenClass_iff_standardExact`
- `feeOnTransferPull_not_exact`
- `inflationaryPull_not_exact`
- `noOpPull_not_exact`
- `recipientFeePush_exactPushDelta`
- `recipientFeePush_receiver_not_exact`
- `exactPullDelta_of_tokenizedAddLiquidityX`
- `exactPullDelta_of_tokenizedAddLiquidityY`
- `exactPullDelta_of_tokenizedSwapXforY`
- `exactPullDelta_of_tokenizedSwapYforX`
- `notExactPull_incompatible_tokenizedAddLiquidityX`
- `notExactPull_incompatible_tokenizedAddLiquidityY`
- `notExactPull_incompatible_tokenizedSwapXforY`
- `notExactPull_incompatible_tokenizedSwapYforX`
- `feeOnTransferPull_incompatible_tokenizedAddLiquidityX`
- `feeOnTransferPull_incompatible_tokenizedAddLiquidityY`
- `inflationaryPull_incompatible_tokenizedSwapXforY`
- `noOpPull_incompatible_tokenizedSwapYforX`
- `externalBalanceDrift_not_exactSync`
- `reserveSync_not_preserved_by_externalDriftX`
- `reserveSync_not_preserved_by_externalDriftY`
- `reserveSync_preserved_by_recipientFeePushY`
- `reserveSync_and_outputDivergence_by_recipientFeePushY`
- `exists_reserveSync_break_by_externalDrift`

## Refinement Scope

The refinement layer models Solidity storage and transitions in Lean (`SolidityStorage`, `alpha`, and `Solidity*` relations) and proves simulation into the abstract CPAMM relations.
It now also includes a trace-level reachability relation (`SolidityReachable`) with theorem-level validity preservation across arbitrary finite step sequences.

Current scope is **bounded floor simulation** in the Solidity relations:
- `SoliditySwapXforY` and `SoliditySwapYforX` are modeled with pure integer floor arithmetic and are proved against bounded abstract swap relations (`SwapXforYFloor`, `SwapYforXFloor`), where floored outputs are bounded above by the exact `dy_of_swap`.
- `SolidityAddLiquidity` is proved against `AddLiquidityFloor`, where minted shares are exact at initialization (`L = 0`) and otherwise within `(exact - 1, exact]` of the rational mint quantity.
- `SolidityRemoveLiquidity` is proved against `RemoveLiquidityFloor`, where each withdrawn reserve amount is within `(exact - 1, exact]` of the rational withdrawal quantity.

This means refinement now covers arbitrary integer-rounded swap/add/remove steps with explicit floor-error bounds.
Additionally, `sim_addLiquidity_bootstrap` explicitly covers the first-liquidity bootstrap path (`totalSupply = reserveX = reserveY = 0`), which is outside `Valid` due strict positive-reserve requirements.
At the abstract transition layer, a separate terminal-close boundary relation (`RemoveLiquidityTerminal`) and preservation theorem are included for the `dL = L` case.

The tokenized refinement layer (`CPAMM/TokenizedRefinement.lean`) extends this with explicit on-chain balance fields and a reserve-sync invariant:
- `reserveX = tokenBalX`
- `reserveY = tokenBalY`

Each tokenized step relation encodes exact transfer-delta assumptions directly in its post-state equations and is proved to:
- preserve reserve-sync
- project/simulate into the arithmetic Solidity relation (`Solidity*`)
- preserve abstract `Valid` via the existing Solidity refinement chain

`CPAMM/TokenizedBehavior.lean` additionally formalizes token behavior classes and machine-checks that unsupported adversarial classes violate exact-transfer assumptions or can break reserve-sync.

## Two-Repo Pipeline Position

This repository is the proof layer in a two-repo workflow:

1. RigidityCore (discovery/confirmation layer)
- Owns protocol sweep, finding discovery, contract-level replay confirmation, materiality signals, and audit dedup.
- Emits `System.json`-anchored evidence for confirmed lanes.

2. cpamm-lean (certificate layer, this repo)
- Owns machine-checked Lean theorem development, refinement proofs, and reviewer-facing proof boundary documentation.

Handoff boundary:
- Lean work here begins only after RigidityCore has produced a confirmed finding package.
- This repo does not run speculative pre-confirmation Lean work.

Gate rule before Lean starts:
1. Contract replay determinism is established.
2. Audit dedup has no unresolved overlap for the lane.
3. The lane shows measurable impact signal worth escalation.

Intake enforcement:
- `scripts/intake_validate.py` validates incoming `System.json` + handoff gate payloads.
- CI runs a protocol-intake gate on template payloads in `Protocol/examples/cpamm/` with strict-gate mode.
- `scripts/protocol_readiness_rehearsal.sh` runs strict-gate rehearsal intake against live RigidityCore target models (Aave/Balancer examples) and emits a ready-to-prove packet.

## Rounding Bounds

From `CPAMM/Rounding.lean`:
- `nat_div_le_rat_div`: floor division never exceeds exact rational division.
- `rat_div_sub_one_lt_nat_div`: floor division is strictly more than exact division minus `1`.
- `reserves_positive_under_rounding`: if the floored swap output is bounded above by the exact rational output, then post-swap reserve positivity is preserved.

## External Validation

- Foundry test suites include baseline unit/fuzz tests plus differential shadow-model fuzzing for swap/add/remove and mixed-operation traces (`solidity/test/CPAMM*.t.sol`).
- ERC20-backed integration tests (`solidity/test/CPAMM.Tokenized.t.sol`) validate reserve/token-balance consistency for add/remove/swaps and reject fee-on-transfer inputs.
- Adversarial ERC20 tests (`solidity/test/CPAMM.Tokenized.Adversarial.t.sol`) validate explicit rejection behavior for unsupported token classes and also demonstrate output-path recipient-fee semantics where reserve-sync can still hold while user-observed output diverges.
- Security static analysis is run via `scripts/security/slither.sh` in fail-on-findings mode over `solidity/src`, with one explicitly triaged exclusion (`divide-before-multiply`).
- CI (`.github/workflows/ci.yml`) runs three gates on push/PR:
  - Lean build
  - Solidity tests
  - Slither security gate
- External-review assumptions and threat-model notes are documented in `security/AUDIT_README.md`.
- CI also enforces coverage regression protection for `solidity/src/CPAMM.sol` and `solidity/src/CPAMMTokenized.sol` (line and statement coverage must remain `100%`, branch coverage must stay above configured floors) and uploads Slither SARIF to GitHub Security.
- Token compatibility assumptions and rejection matrix are tracked in `security/TOKEN_COMPATIBILITY.md`.
- Lean assumption-to-test coupling is tracked in `reports/ASSUMPTION_TEST_MATRIX.md`.
- CI validates matrix references against both real Solidity test functions and Lean declarations via `scripts/validate_assumption_matrix.py`.
- CI additionally publishes a unified `review-package` artifact generated by `scripts/review_package.sh` (theorem inventory + logs + SARIF + LCOV + strict intake report + checksums + manifest).

## Assumptions

- Solidity addresses are abstracted as `SolAddress := ℕ`.
- LP-supply accounting consistency uses finite address universes (`[Fintype α]` and `[DecidableEq α]`).
- Solidity fee denominator is strictly positive (`h_denom_pos`).
- Solidity/refinement remove-liquidity theorems assume nontrivial liquidity actions (`dL < totalSupply`) to keep post-state reserves positive (matching contract behavior).
- The full-withdrawal boundary (`dL = L`) is handled as an abstract terminal-close theorem, not a Solidity-refinement path.
- Tokenized refinement assumes exact ERC20 transfer semantics for modeled transitions (no hidden mint/burn/rebase side effects during a step and no fee-on-transfer behavior).
- Tokenized behavior taxonomy and unsupported-class formal lemmas live in `CPAMM/TokenizedBehavior.lean`.
- Tokenized scope and remaining formalization work are tracked in `VERIFICATION_TOKENIZED.md`.

## Non-goals

- Flash loan protection
- Reentrancy hardening
- Oracle/TWAP integration
- Gas optimization
- Governance controls
- Upgradeability

## `sorry` Status

No `sorry` appears in the CPAMM Lean development files (`CPAMM/*.lean`).

## Reproduction

```bash
~/.elan/bin/lake exe cache get
~/.elan/bin/lake build
cd solidity && ~/.foundry/bin/forge test
./scripts/security/slither.sh
./scripts/review_package.sh
```
