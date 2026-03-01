# Assumption-Test Matrix

This matrix links tokenized formal assumptions to concrete test evidence.

| Assumption / Behavior | Lean Encoding | Solidity Test Evidence | Status |
|---|---|---|---|
| Exact pull delta (`after = before + amount`) | `ExactPullDelta` in `CPAMM/TokenizedBehavior.lean` and tokenized step relations in `CPAMM/TokenizedRefinement.lean` | `CPAMM.Tokenized.t.sol::test_addLiquidity_reserveSync` + fuzz `CPAMM.Tokenized.t.sol::testFuzz_tokenized_multiStep_reserveSync` | Supported |
| Exact push delta (`before = after + amount`) | `ExactPushDelta` + tokenized remove/swap relations | `CPAMM.Tokenized.t.sol::test_swapXforY_reserveSync`, `CPAMM.Tokenized.t.sol::test_swapYforX_reserveSync`, `CPAMM.Tokenized.t.sol::test_removeLiquidity_reserveSync` | Supported |
| Fee-on-transfer deflationary pull violates exact delta | `feeOnTransferPull_not_exact` | `CPAMM.Tokenized.t.sol::test_feeOnTransferToken_rejected` | Rejected |
| Inflationary pull violates exact delta | `inflationaryPull_not_exact` | `CPAMM.Tokenized.Adversarial.t.sol::test_rejectsInflationaryTransferToken` | Rejected |
| No-op transferFrom violates exact delta | `noOpPull_not_exact` | `CPAMM.Tokenized.Adversarial.t.sol::test_rejectsNoOpTransferFromToken` | Rejected |
| External drift can break reserve-sync | `externalBalanceDrift_not_exactSync`, `exists_reserveSync_break_by_externalDrift` | `CPAMM.Tokenized.Adversarial.t.sol::test_revertsOnExternalBalanceDrift` | Rejected |
| False-return transferFrom/transfer | modeled operationally in Solidity checks (`transferFrom failed`, `transfer failed`) | `CPAMM.Tokenized.Adversarial.t.sol::test_rejectsFalseTransferFromToken`, `CPAMM.Tokenized.Adversarial.t.sol::test_rejectsFalseTransferOnOutputPath` | Rejected |

## Notes

- This file is reviewer-facing coupling metadata.
- The machine-checked source of truth remains Lean theorem files under `CPAMM/`.
