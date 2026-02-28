# CPAMM Audit Readme

This note is a reviewer-facing map of the security posture, assumptions, and verification boundaries for this repository.

## Artifact Scope

In scope:
- Constant-product AMM core with two reserves.
- LP mint/burn accounting.
- Fee-on-input swap arithmetic.
- Integer-floor behavior for swap and liquidity math.
- Lean proofs for safety/economic/refinement properties.

Out of scope:
- Oracle/TWAP logic.
- Governance/admin controls.
- Upgradeability.
- Flash-loan-specific mitigations.
- Token transfer integration (this artifact models arithmetic/state transitions only).

## Threat Model

The primary objective is arithmetic and state-transition correctness under adversarial transaction ordering and parameter choices, not full protocol composability.

Security goals:
- Reserves remain positive under modeled valid transitions.
- LP accounting remains coherent.
- Swap outputs remain bounded by reserves.
- Refinement from Solidity integer behavior to abstract Lean relations is explicit and machine-checked.

## Explicit Assumptions

- Address abstraction in Lean uses `SolAddress := ℕ`.
- Fee denominator is strictly positive and numerator is strictly smaller than denominator.
- Liquidity removal requires `shares < totalSupply` to preserve positive post-state reserves.
- The Solidity model assumes checked arithmetic in compiler `0.8.30`.
- The contract models internal accounting only; no external token hooks are present.

## What Is Proved vs Tested

Machine-checked proofs (`CPAMM/*.lean`) cover:
- State validity preservation.
- LP consistency preservation.
- Economic properties for swaps/removals.
- Floor-rounding bounds.
- Refinement simulations for `swapXforY`, `swapYforX`, `addLiquidity`, `removeLiquidity`.

Foundry tests (`solidity/test/*.t.sol`) cover:
- Unit and fuzz checks for contract behavior.
- Differential shadow-model checks against an independent integer model.
- Stateful invariant campaign via handler-driven random call sequences.

Static analysis (`scripts/security/slither.sh`):
- Fails CI on non-triaged findings.
- Current explicit exclusion: `divide-before-multiply` (intentional floor-first fee model).

## Known Reviewer Notes

- `divide-before-multiply` is intentional and aligned with the Lean refinement strategy.
- CI publishes artifacts for all gates:
  - Lean build logs
  - Forge log/JSON/coverage
  - Slither log/SARIF

## Reproduce Locally

```bash
~/.elan/bin/lake exe cache get
~/.elan/bin/lake build
cd solidity && ~/.foundry/bin/forge test
./scripts/security/slither.sh
```

## Primary References

- `VERIFICATION.md`
- `security/SECURITY_VALIDATION.md`
- `CPAMM/Refinement.lean`
