# Acceptance Criteria Template

## Technical Criteria

1. Required theorem set status
- `lake build` passes and required theorem inventory is present.

2. Required test suite status
- `forge test` passes for agreed suites.

3. Required security gate status
- `scripts/security/slither.sh` passes with agreed detector policy.

4. Required coverage gate status
- Coverage thresholds met for agreed contracts.

## Evidence Criteria

1. Reviewer package generated via `scripts/review_package.sh`.
2. Manifest includes versions, checksums, and command list.
3. Assumption/test matrix is current and validator passes.

## Documentation Criteria

1. Verification docs updated with actual scope.
2. Assumptions and out-of-scope boundaries explicitly stated.

## Commercial Completion Criteria

1. Deliverables submitted in writing.
2. Client has 5 business days for review.
3. Unresolved items beyond scope are moved to change control.
