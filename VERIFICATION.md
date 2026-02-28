# CPAMM-1 Verification Dossier

## Proven Theorems

### `CPAMM/State.lean`
- `product_pos`

### `CPAMM/Invariants.lean`
- `valid_preserved_addLiquidity`
- `valid_preserved_removeLiquidity`
- `valid_preserved_swapXforY`
- `valid_preserved_swapYforX`
- `consistent_preserved_addLiquidity`
- `consistent_preserved_removeLiquidity`

### `CPAMM/Economics.lean`
- `product_preserved_swap_no_fee`
- `product_nondecreasing_swap_with_fee`
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

## Refinement Scope

The refinement layer models Solidity storage and transitions in Lean (`SolidityStorage`, `alpha`, and `Solidity*` relations) and proves simulation into the abstract CPAMM relations.

Current scope is **bounded floor simulation** in the Solidity relations:
- `SoliditySwapXforY` and `SoliditySwapYforX` are modeled with pure integer floor arithmetic and are proved against bounded abstract swap relations (`SwapXforYFloor`, `SwapYforXFloor`), where floored outputs are bounded above by the exact `dy_of_swap`.
- `SolidityAddLiquidity` is proved against `AddLiquidityFloor`, where minted shares are exact at initialization (`L = 0`) and otherwise within `(exact - 1, exact]` of the rational mint quantity.
- `SolidityRemoveLiquidity` is proved against `RemoveLiquidityFloor`, where each withdrawn reserve amount is within `(exact - 1, exact]` of the rational withdrawal quantity.

This means refinement now covers arbitrary integer-rounded swap/add/remove steps with explicit floor-error bounds.
Additionally, `sim_addLiquidity_bootstrap` explicitly covers the first-liquidity bootstrap path (`totalSupply = reserveX = reserveY = 0`), which is outside `Valid` due strict positive-reserve requirements.

## Rounding Bounds

From `CPAMM/Rounding.lean`:
- `nat_div_le_rat_div`: floor division never exceeds exact rational division.
- `rat_div_sub_one_lt_nat_div`: floor division is strictly more than exact division minus `1`.
- `reserves_positive_under_rounding`: if the floored swap output is bounded above by the exact rational output, then post-swap reserve positivity is preserved.

## External Validation

- Foundry test suites include baseline unit/fuzz tests plus differential shadow-model fuzzing for swap/add/remove and mixed-operation traces (`solidity/test/CPAMM*.t.sol`).
- Security static analysis is run via `scripts/security/slither.sh` in fail-on-findings mode, with one explicitly triaged exclusion (`divide-before-multiply`).
- CI (`.github/workflows/ci.yml`) runs three gates on push/PR:
  - Lean build
  - Solidity tests
  - Slither security gate
- External-review assumptions and threat-model notes are documented in `security/AUDIT_README.md`.
- CI also enforces coverage regression protection for `solidity/src/CPAMM.sol` (line and statement coverage must remain `100%`, branch coverage must stay above a configured floor) and uploads Slither SARIF to GitHub Security.

## Assumptions

- Solidity addresses are abstracted as `SolAddress := ℕ`.
- LP-supply accounting consistency uses finite address universes (`[Fintype α]` and `[DecidableEq α]`).
- Solidity fee denominator is strictly positive (`h_denom_pos`).
- Add/remove refinement theorems assume nontrivial liquidity actions (`dL < totalSupply`) to keep post-state reserves positive.

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
```
