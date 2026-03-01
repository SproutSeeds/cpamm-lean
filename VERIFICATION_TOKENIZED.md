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
  - Trace-level validity + reserve-sync preservation theorem (`validAndSync_preserved_tokenizedReachable`)

## Lean Refinement Scope Today

The machine-checked chain now has two layers:
1. `CPAMM/Refinement.lean`: arithmetic Solidity storage (`CPAMM.sol`) to abstract CPAMM transitions.
2. `CPAMM/TokenizedRefinement.lean`: tokenized storage projection/simulation and reserve-sync preservation.

Current tokenized assumptions are explicit by construction:
- exact transfer-in/transfer-out deltas for each step
- no hidden token-side balance mutation during a modeled transition
- concrete supported/unsupported token classes are listed in `security/TOKEN_COMPATIBILITY.md`

## Formalization Targets (Next)

1. **Token Behavior Taxonomy in Lean**
- Partition token classes (standard ERC20 vs non-standard/rebasing/fee-on-transfer) in the formal model.
- Encode failure boundaries as assumptions/lemmas instead of prose-only scope notes.

2. **Adversarial Semantics Layer**
- Add abstract counterexamples/non-preservation lemmas for unsupported token behaviors to mirror the Solidity adversarial tests.

3. **Tighter Projection Interface**
- Prove a reusable simulation theorem from tokenized traces directly to `SolidityReachable` traces.

4. **Proof/Test Coupling**
- Link each assumption class to concrete Foundry tests in a machine-readable matrix.

## Reviewer Guidance

- `CPAMM.sol` + existing Lean refinement remains the formally verified artifact.
- `CPAMMTokenized.sol` is now both hardened/test-validated and partially formalized:
  reserve-sync and projection are machine-checked under explicit exact-transfer assumptions.
