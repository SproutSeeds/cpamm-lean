# Token Compatibility Matrix

This matrix documents the ERC20 behavior classes exercised by the tokenized integration/adversarial tests and the expected CPAMMTokenized behavior.

## Supported Class

1. **Standard exact-transfer ERC20**
- Behavior: `transfer`/`transferFrom` return `true`, and the pool's balance delta is exactly `amount` for both pull/push paths.
- Outcome: supported.
- Evidence:
  - `solidity/test/CPAMM.Tokenized.t.sol::test_addLiquidity_reserveSync`
  - `solidity/test/CPAMM.Tokenized.t.sol::test_swapXforY_reserveSync`
  - `solidity/test/CPAMM.Tokenized.t.sol::test_swapYforX_reserveSync`
  - `solidity/test/CPAMM.Tokenized.t.sol::test_removeLiquidity_reserveSync`
  - `solidity/test/CPAMM.Tokenized.t.sol::testFuzz_tokenized_multiStep_reserveSync`

## Unsupported / Rejected Classes

1. **Fee-on-transfer / deflationary tokens**
- Behavior: received amount on pull is `< amount`.
- Outcome: rejected with `fee-on-transfer unsupported`.
- Evidence:
  - `solidity/test/CPAMM.Tokenized.t.sol::test_feeOnTransferToken_rejected`

2. **Inflationary / mint-on-transfer tokens**
- Behavior: received amount on pull is `> amount`.
- Outcome: rejected with `fee-on-transfer unsupported`.
- Evidence:
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol::test_rejectsInflationaryTransferToken`

3. **False-return `transferFrom` tokens**
- Behavior: `transferFrom` returns `false`.
- Outcome: rejected with `transferFrom failed`.
- Evidence:
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol::test_rejectsFalseTransferFromToken`

4. **No-op `transferFrom` tokens**
- Behavior: `transferFrom` returns `true` but does not move balances.
- Outcome: rejected with `fee-on-transfer unsupported`.
- Evidence:
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol::test_rejectsNoOpTransferFromToken`

5. **False-return `transfer` tokens (output path)**
- Behavior: `transfer` returns `false` when AMM sends output.
- Outcome: rejected with `transfer failed`.
- Evidence:
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol::test_rejectsFalseTransferOnOutputPath`

6. **External balance drift (rebasing/airdrop/manual transfer into pool)**
- Behavior: `token.balanceOf(address(pool)) != reserve` before an operation.
- Outcome: rejected with reserve mismatch (`reserveX mismatch` or `reserveY mismatch`).
- Evidence:
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol::test_revertsOnExternalBalanceDrift`

7. **Pool-output recipient fee tokens (output-path semantic divergence)**
- Behavior: when the pool sends `amount`, pool balance drops by `amount` exactly, but recipient is credited `< amount`.
- Outcome: not rejected by reserve-sync checks; unsupported for exact user-observed output semantics.
- Evidence:
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol::test_outputFeeOnPoolTransfer_breaksObservedSwapXforYOutput`
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol::test_outputFeeOnPoolTransfer_breaksObservedSwapYforXOutput`
  - `solidity/test/CPAMM.Tokenized.Adversarial.t.sol::test_outputFeeOnPoolTransfer_breaksObservedRemoveLiquidityOutput`

## Interpretation

`CPAMMTokenized` is intentionally strict around pool-balance sync. This keeps reserve accounting aligned with the Lean tokenized refinement assumptions (`CPAMM/TokenizedRefinement.lean`), but does not by itself guarantee exact user-observed output transfer semantics for every non-standard token class.
