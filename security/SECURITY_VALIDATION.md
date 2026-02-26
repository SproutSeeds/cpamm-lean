# Security Validation (Step 3)

Date: 2026-02-26

## Scope

This validation pass adds:
- Differential fuzzing between on-chain CPAMM behavior and an independent reference model.
- External static analysis using Slither.

## Differential Fuzzing

File:
- `solidity/test/CPAMM.Differential.t.sol`

Added tests:
1. `testFuzz_differential_swapXforY_matches_model_and_bound`
2. `testFuzz_differential_swapYforX_matches_model_and_bound`
3. `testFuzz_differential_three_swap_sequence`

What is checked:
- Exact match with an independent integer reference model for swap outputs and post-state reserves.
- Lean-style rational bound for swaps: floor-rounded on-chain output is bounded above by the exact rational no-floor output.
- Multi-step swap sequence consistency and reserve positivity.

Run:

```bash
cd solidity
~/.foundry/bin/forge test
```

Status:
- Pass (`11/11` tests total across the project).

## External Tooling: Slither

Command executed:

```bash
source .venv-security/bin/activate
slither solidity/src/CPAMM.sol
```

Observed detector findings:
1. `divide-before-multiply` (swap functions)
2. `solc-version` warning for `^0.8.20` and known compiler issues listed by Slither

Triage:
- `divide-before-multiply`: **accepted / intentional** in this artifact.
  The fee model intentionally floors effective input before output computation, matching both the Solidity implementation and refinement strategy.
- `solc-version`: **known warning**.
  The project requirement specifies Solidity `^0.8.20`; version hardening (e.g., pinning a newer patched compiler) can be done in a follow-up if scope allows.

## Notes

- Local tooling environment used for analysis: `.venv-security/` (gitignored).
- This pass does not add new protocol features; it strengthens validation depth only.
