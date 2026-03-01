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
3. `forge test --gas-report`
4. `forge test --json`
5. `forge coverage --report summary --report lcov`
6. Coverage threshold parser (same gates as CI)
7. `./scripts/security/slither.sh` with SARIF output

## Bundle Contents

- Lean logs: `lake-cache.log`, `lake-build.log`
- Solidity test logs: `forge-test.log`, `forge-test.json`
- Coverage evidence: `forge-coverage.log`, `lcov.info`, `coverage-gate.log`
- Security evidence: `slither.log`, `slither.sarif`
- Metadata: `versions.txt`, `COMMANDS.txt`, `MANIFEST.md`
- Integrity file: `SHA256SUMS`

## CI Publication

The CI workflow publishes this as the `review-package` artifact on each run.
