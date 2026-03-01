# Review Package Guide

The repository provides a one-command reproducibility/evidence bundle generator:

```bash
./scripts/review_package.sh
```

By default this writes to:
- `artifacts/review-package-<UTC timestamp>/`
- `artifacts/review-package-<UTC timestamp>.tar.gz`

You can also pass an explicit output path:

```bash
./scripts/review_package.sh artifacts/review-package
```

## What It Runs

1. `lake exe cache get`
2. `lake build`
3. theorem inventory generation over `CPAMM/*.lean`
4. theorem inventory sync check against `VERIFICATION.md`
5. theorem inventory validation against `VERIFICATION.md` (complete mode)
6. `forge test --gas-report`
7. `forge test --json`
8. `forge coverage --report summary --report lcov`
9. Coverage threshold parser (same gates as CI)
10. `./scripts/security/slither.sh` with SARIF output
11. strict protocol intake validation over template handoff payloads

## Bundle Contents

- Lean logs: `lake-cache.log`, `lake-build.log`
- Theorem evidence: `theorem-inventory.md`, `theorem-inventory-sync.log`, `theorem-inventory-validation.log`
- Solidity test logs: `forge-test.log`, `forge-test.json`
- Coverage evidence: `forge-coverage.log`, `lcov.info`, `coverage-gate.log`
- Security evidence: `slither.log`, `slither.sarif`
- Intake evidence: `protocol-intake.log`, `protocol-intake.md`
- Metadata: `versions.txt`, `COMMANDS.txt`, `MANIFEST.md`
- Integrity file: `SHA256SUMS`

## CI Publication

The CI workflow publishes this as the `review-package` artifact on each run.
