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
4. `forge test --gas-report`
5. `forge test --json`
6. `forge coverage --report summary --report lcov`
7. Coverage threshold parser (same gates as CI)
8. `./scripts/security/slither.sh` with SARIF output
9. strict protocol intake validation over template handoff payloads

## Bundle Contents

- Lean logs: `lake-cache.log`, `lake-build.log`
- Theorem inventory: `theorem-inventory.md`
- Solidity test logs: `forge-test.log`, `forge-test.json`
- Coverage evidence: `forge-coverage.log`, `lcov.info`, `coverage-gate.log`
- Security evidence: `slither.log`, `slither.sarif`
- Intake evidence: `protocol-intake.log`, `protocol-intake.md`
- Metadata: `versions.txt`, `COMMANDS.txt`, `MANIFEST.md`
- Integrity file: `SHA256SUMS`

## CI Publication

The CI workflow publishes this as the `review-package` artifact on each run.
