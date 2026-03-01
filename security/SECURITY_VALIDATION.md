# Security Validation (Step 3)

Date: 2026-03-01

## Scope

This validation pass adds:
- Differential fuzzing between on-chain CPAMM behavior and an independent reference model.
- Stateful invariant fuzzing via Foundry `StdInvariant` (two LP actors).
- ERC20-backed integration testing for reserve/token-balance consistency.
- External static analysis using Slither.

## Differential Fuzzing

File:
- `solidity/test/CPAMM.Differential.t.sol`
- `solidity/test/CPAMM.Tokenized.t.sol`

Added tests:
1. `testFuzz_differential_swapXforY_matches_model_and_bound`
2. `testFuzz_differential_swapYforX_matches_model_and_bound`
3. `testFuzz_differential_three_swap_sequence`
4. `testFuzz_differential_addLiquidity_matches_model_and_bound`
5. `testFuzz_differential_removeLiquidity_matches_model_and_bound`
6. `testFuzz_stateful_differential_mixed_operations`
7. `testFuzz_tokenized_multiStep_reserveSync`

What is checked:
- Exact match with an independent integer reference model for swap outputs and post-state reserves.
- Exact match with an independent integer reference model for add/remove liquidity outputs and post-state reserves.
- Lean-style rational bound for swaps: floor-rounded on-chain output is bounded above by the exact rational no-floor output.
- Lean-style floor bounds for LP minting and reserve withdrawals: floor result stays within `(exact - 1, exact]`.
- Multi-step swap sequence consistency and reserve positivity.
- Mixed-operation stateful consistency (add/remove/swap) against a shadow model over several fuzzed steps.
- Reserve accounting equality with actual ERC20 balances in an ERC20-backed CPAMM variant.
- Rejection of fee-on-transfer token inputs for exact-accounting paths.

Run:

```bash
cd solidity
~/.foundry/bin/forge test
```

Status:
- Pass (`25/25` tests total across the project, including 4 multi-actor invariant tests and 6 ERC20-backed integration tests).

## External Tooling: Slither

Command executed:

```bash
./scripts/security/slither.sh
```

Observed detector findings:
1. `divide-before-multiply` (swap functions)

Triage:
- `divide-before-multiply`: **accepted / intentional** in this artifact.
  The fee model intentionally floors effective input before output computation, matching both the Solidity implementation and refinement strategy.
- `solc-version`: **resolved** by upgrading to exact compiler pin `0.8.30`.

CI gate behavior:
- `scripts/security/slither.sh` runs Slither in fail-on-findings mode (`--fail-pedantic`).
- Scope: `solidity/src` (core + tokenized extension contracts).
- Only `divide-before-multiply` is excluded explicitly via `--exclude`.
- Any new detector finding now fails local security checks and CI.
- Tool versions are pinned for reproducibility (Foundry `1.5.1` in CI, Slither `0.11.4` in script).
- CI exports Slither SARIF output and uploads it to GitHub Security (`upload-sarif`).
- CI caches `.venv-security`/pip state and uses retry-wrapped installs in `scripts/security/slither.sh` to reduce transient network failures.

## Notes

- Local tooling environment used for analysis: `.venv-security/` (gitignored).
- This pass does not add new protocol features; it strengthens validation depth only.
