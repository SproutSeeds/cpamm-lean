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
- Full ERC20 behavioral formalization across non-standard token classes.

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
- A separate abstract terminal-close relation is proved for the `dL = L` boundary (`RemoveLiquidityTerminal`), but this path is intentionally excluded from the Solidity contract.
- The Solidity model assumes checked arithmetic in compiler `0.8.30`.
- The contract models internal accounting only; no external token hooks are present.

## What Is Proved vs Tested

Machine-checked proofs (`CPAMM/*.lean`) cover:
- State validity preservation.
- LP consistency preservation.
- Economic properties for swaps/removals.
- Floor-rounding bounds.
- Refinement simulations for `swapXforY`, `swapYforX`, `addLiquidity`, `removeLiquidity`.
- Tokenized reserve-sync preservation and projection/simulation under exact-transfer assumptions.

Foundry tests (`solidity/test/*.t.sol`) cover:
- Unit and fuzz checks for contract behavior.
- Differential shadow-model checks against an independent integer model.
- Stateful invariant campaign via handler-driven random call sequences.
- ERC20-backed integration checks (`CPAMM.Tokenized.t.sol`) for reserve/token-balance consistency and fee-on-transfer rejection.
- Adversarial ERC20 behavior checks (`CPAMM.Tokenized.Adversarial.t.sol`) for explicit rejection semantics.

Note:
- `CPAMMTokenized.sol` now has a machine-checked tokenized refinement layer for reserve-sync + projection assumptions (`CPAMM/TokenizedRefinement.lean`), while broader non-standard token semantics remain out of formal scope.

Static analysis (`scripts/security/slither.sh`):
- Fails CI on non-triaged findings.
- Scans `solidity/src` (core and tokenized extension contracts).
- Current explicit exclusion: `divide-before-multiply` (intentional floor-first fee model).

Token compatibility matrix:
- `security/TOKEN_COMPATIBILITY.md`

Review package bundle:
- `scripts/review_package.sh`
- `reports/REVIEW_PACKAGE.md`

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
./scripts/review_package.sh
```

## Primary References

- `VERIFICATION.md`
- `security/SECURITY_VALIDATION.md`
- `CPAMM/Refinement.lean`
