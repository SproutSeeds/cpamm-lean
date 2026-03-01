# Tokenized Verification Track

This note defines the formal/spec alignment plan for the ERC20-backed extension
`solidity/src/CPAMMTokenized.sol`.

## Current Status (Implemented)

- Implementation exists in Solidity:
  - `solidity/src/CPAMMTokenized.sol`
- Tests exist and pass:
  - `solidity/test/CPAMM.Tokenized.t.sol`
  - Reserve/accounting sync checks: `reserveX == tokenX.balanceOf(this)` and `reserveY == tokenY.balanceOf(this)`
  - Add/remove/swap path coverage, including multi-step fuzz traces
  - Fee-on-transfer rejection path
- Static analysis exists and passes in CI via `scripts/security/slither.sh` (now scanning `solidity/src`).

## Lean Refinement Scope Today

The machine-checked refinement chain in `CPAMM/Refinement.lean` is still scoped to
the arithmetic-state contract model (`CPAMM.sol`), not the ERC20 transfer semantics.

## Formalization Targets (Next)

1. **Reserve Sync Invariant**
- Define and prove that every valid tokenized transition preserves:
  - `reserveX = onChainBalanceX`
  - `reserveY = onChainBalanceY`

2. **Exact Transfer Assumption Surface**
- Make explicit assumptions for token behavior (standard ERC20 semantics, no hidden mint/burn side effects).
- Isolate fee-on-transfer rejection as a precondition boundary.

3. **Tokenized Step Relations**
- Add abstract relations for tokenized add/remove/swap that include transfer pre/post-state.
- Prove validity preservation at this extended state layer.

4. **Projection/Simulation**
- Prove that projecting tokenized states to abstract reserves/supply/balances simulates the existing CPAMM abstract model under the stated token assumptions.

## Reviewer Guidance

- `CPAMM.sol` + existing Lean refinement remains the formally verified artifact.
- `CPAMMTokenized.sol` is currently a hardened, test-validated extension with explicit scope boundaries documented here.
