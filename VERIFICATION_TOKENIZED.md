# Tokenized Verification Track

This note defines the formal/spec alignment plan for the ERC20-backed extension
`solidity/src/CPAMMTokenized.sol`.

## Current Status (Implemented)

- Implementation exists in Solidity:
  - `solidity/src/CPAMMTokenized.sol`
- Tests exist and pass:
  - `solidity/test/CPAMM.Tokenized.t.sol`
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol`
  - Reserve/accounting sync checks: `reserveX == tokenX.balanceOf(this)` and `reserveY == tokenY.balanceOf(this)`
  - Add/remove/swap path coverage, including multi-step fuzz traces
  - Fee-on-transfer rejection path
  - Adversarial token-class rejection paths (false return, no-op transfer, inflationary transfer, external balance drift)
- Static analysis exists and passes in CI via `scripts/security/slither.sh` (now scanning `solidity/src`).
- Unified reviewer bundle generation exists via `scripts/review_package.sh` (published by CI as `review-package` artifact).
- Lean tokenized refinement exists in:
  - `CPAMM/TokenizedRefinement.lean`
  - Reserve-sync invariant (`reserveX = tokenBalX`, `reserveY = tokenBalY`)
  - Tokenized step relations for add/remove/swaps with exact transfer-delta assumptions
  - Projection/simulation theorems from tokenized steps to `Solidity*` relations
  - Trace-level projection theorem from `TokenizedReachable` to `SolidityReachable`
  - Trace-level validity + reserve-sync preservation theorem (`validAndSync_preserved_tokenizedReachable`)
- Lean token behavior taxonomy exists in:
  - `CPAMM/TokenizedBehavior.lean`
  - formal token-class partition (`TokenClass`, `SupportedTokenClass`)
  - adversarial non-exact lemmas (`feeOnTransferPull_not_exact`, `inflationaryPull_not_exact`, `noOpPull_not_exact`)
  - output-path recipient-fee lemmas (`recipientFeePush_exactPushDelta`, `recipientFeePush_receiverOutput_not_exact`)
  - explicit reserve-sync break witness (`exists_reserveSync_break_by_externalDrift`)
- Lean tokenized IO semantics layer exists in:
  - `CPAMM/TokenizedIOSemantics.lean`
  - transfer exactness relations (`ExactPullDelta`, `ExactPushDelta`)
  - recipient-observed output exactness (`RecipientObservedOutputExact`)
  - extraction lemmas from tokenized steps (`exactPullDelta_of_tokenized*`)

## Lean Refinement Scope Today

The machine-checked chain now has two layers:
1. `CPAMM/Refinement.lean`: arithmetic Solidity storage (`CPAMM.sol`) to abstract CPAMM transitions.
2. `CPAMM/TokenizedRefinement.lean`: tokenized storage projection/simulation and reserve-sync preservation.

Current tokenized assumptions are explicit by construction:
- exact transfer-in/transfer-out deltas for each step
- no hidden token-side balance mutation during a modeled transition
- concrete supported/unsupported token classes are listed in `security/TOKEN_COMPATIBILITY.md`
- assumption/test mapping is tracked in `reports/ASSUMPTION_TEST_MATRIX.md`
- CI enforces matrix consistency via `scripts/validate_assumption_matrix.py`

## Formalization Track Status

Implemented:

1. **Tighter Projection Interface**
- `sim_tokenizedReachable_to_solidityReachable` proves trace-level simulation directly from tokenized traces into `SolidityReachable`.

2. **Semantic Strengthening (step-level)**
- `CPAMM/TokenizedBehavior.lean` now includes step-level incompatibility theorems for unsupported pull classes:
  - `feeOnTransferPull_incompatible_tokenizedAddLiquidityX`
  - `feeOnTransferPull_incompatible_tokenizedAddLiquidityY`
  - `inflationaryPull_incompatible_tokenizedSwapXforY`
  - `noOpPull_incompatible_tokenizedSwapYforX`
- It also includes reserve-sync non-preservation theorems under external drift with unchanged core reserves:
  - `reserveSync_not_preserved_by_externalDriftX`
  - `reserveSync_not_preserved_by_externalDriftY`
- It now includes output-path divergence lemmas for recipient-fee token behavior:
  - `reserveSync_preserved_by_recipientFeePushY`
  - `reserveSync_and_outputDivergence_by_recipientFeePushY`
  - `reserveSync_and_removeLiquidityOutputDivergence_by_recipientFeePushX`
  - `reserveSync_and_removeLiquidityOutputDivergence_by_recipientFeePushY`
  - matched by adversarial Solidity tests where returned quote differs from recipient-observed transfer while reserve-sync holds (swap and remove paths).

3. **Proof/Test Coupling Automation**
- CI validation in `scripts/validate_assumption_matrix.py` now checks:
  - fully-qualified test references resolve to real Solidity test functions
  - Lean symbols in matrix Lean-encoding cells resolve to declarations in `CPAMM/*.lean`

4. **Projection Abstraction Cleanup**
- Added step-level helper theorems:
  - `valid_preserved_tokenizedStep`
  - `reserveSync_preserved_tokenizedStep`
- This factors repeated case analysis out of `validAndSync_preserved_tokenizedStep` and provides reusable scaffolding for future tokenized modules.

5. **Recipient-Semantics Refinement Integration**
- Moved recipient/output exactness and transfer-delta relations into dedicated module:
  - `CPAMM/TokenizedIOSemantics.lean`
- `CPAMM/TokenizedBehavior.lean` now imports this IO layer and focuses on token-class/adversarial behavior proofs.

## Remaining Priority Work

- No known blocking tokenized formalization gaps for the current CPAMM tokenized scope.

## Reviewer Guidance

- `CPAMM.sol` + existing Lean refinement remains the formally verified artifact.
- `CPAMMTokenized.sol` is now both hardened/test-validated and partially formalized:
  reserve-sync/projection are machine-checked under explicit exact-transfer assumptions, and unsupported token classes are explicitly formalized in Lean.
