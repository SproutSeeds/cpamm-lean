#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${1:-$ROOT_DIR/artifacts/review-package-$STAMP}"
if [[ "$OUT_DIR" != /* ]]; then
  OUT_DIR="$ROOT_DIR/$OUT_DIR"
fi

mkdir -p "$OUT_DIR"

if command -v lake >/dev/null 2>&1; then
  LAKE_BIN="$(command -v lake)"
elif [[ -x "$HOME/.elan/bin/lake" ]]; then
  LAKE_BIN="$HOME/.elan/bin/lake"
else
  echo "error: lake not found (install Lean 4 / elan first)" >&2
  exit 1
fi

if command -v forge >/dev/null 2>&1; then
  FORGE_BIN="$(command -v forge)"
elif [[ -x "$HOME/.foundry/bin/forge" ]]; then
  FORGE_BIN="$HOME/.foundry/bin/forge"
else
  echo "error: forge not found (install Foundry first)" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found" >&2
  exit 1
fi

echo "==> output: $OUT_DIR"

echo "==> lean cache"
"$LAKE_BIN" exe cache get 2>&1 | tee "$OUT_DIR/lake-cache.log"

echo "==> lean build"
"$LAKE_BIN" build 2>&1 | tee "$OUT_DIR/lake-build.log"

echo "==> theorem inventory"
python3 "$ROOT_DIR/scripts/theorem_inventory.py" \
  --root "$ROOT_DIR" \
  --out "$OUT_DIR/theorem-inventory.md"

echo "==> theorem inventory sync check"
python3 "$ROOT_DIR/scripts/theorem_inventory.py" \
  --root "$ROOT_DIR" \
  --verification-md "$ROOT_DIR/VERIFICATION.md" \
  --check-verification 2>&1 | tee "$OUT_DIR/theorem-inventory-sync.log"

echo "==> theorem inventory validation"
python3 "$ROOT_DIR/scripts/validate_theorem_inventory.py" \
  --verification-md "$ROOT_DIR/VERIFICATION.md" \
  --root "$ROOT_DIR" 2>&1 | tee "$OUT_DIR/theorem-inventory-validation.log"

echo "==> forge test (human log)"
(
  cd "$ROOT_DIR/solidity"
  "$FORGE_BIN" test --gas-report 2>&1 | tee "$OUT_DIR/forge-test.log"
)

echo "==> forge test (json)"
(
  cd "$ROOT_DIR/solidity"
  "$FORGE_BIN" test --json > "$OUT_DIR/forge-test.json"
)

echo "==> forge coverage (summary + lcov)"
(
  cd "$ROOT_DIR/solidity"
  "$FORGE_BIN" coverage --report summary --report lcov 2>&1 | tee "$OUT_DIR/forge-coverage.log"
  cp lcov.info "$OUT_DIR/lcov.info"
)

echo "==> coverage gates"
python3 - "$OUT_DIR/forge-coverage.log" > "$OUT_DIR/coverage-gate.log" <<'PY'
import re
import sys
from pathlib import Path

log = Path(sys.argv[1]).read_text()

def parse_row(file_path: str):
    row = next((ln for ln in log.splitlines() if file_path in ln), None)
    if row is None:
        raise SystemExit(f"error: {file_path} coverage row not found")
    vals = re.findall(r"([0-9]+(?:\.[0-9]+)?)%", row)
    if len(vals) < 3:
        raise SystemExit(f"error: could not parse coverage percentages from line: {row}")
    return float(vals[0]), float(vals[1]), float(vals[2])

targets = [
    ("src/CPAMM.sol", 56.0),
    ("src/CPAMMTokenized.sol", 53.0),
]

for file_path, min_branch_cov in targets:
    line_cov, stmt_cov, branch_cov = parse_row(file_path)
    if line_cov < 100.0 or stmt_cov < 100.0 or branch_cov < min_branch_cov:
        raise SystemExit(
            f"error: coverage regression for {file_path} "
            f"(lines={line_cov:.2f}%, statements={stmt_cov:.2f}%, branches={branch_cov:.2f}%)"
        )
    print(
        f"coverage gate passed for {file_path} "
        f"(lines={line_cov:.2f}%, statements={stmt_cov:.2f}%, branches={branch_cov:.2f}%)"
    )
PY

cat "$OUT_DIR/coverage-gate.log"

echo "==> slither"
(
  cd "$ROOT_DIR"
  SLITHER_SARIF="$OUT_DIR/slither.sarif" ./scripts/security/slither.sh 2>&1 | tee "$OUT_DIR/slither.log"
)

echo "==> protocol intake validation (strict gate)"
(
  cd "$ROOT_DIR"
  python3 scripts/intake_validate.py \
    --system-json Protocol/examples/cpamm/System.json \
    --handoff-json Protocol/examples/cpamm/HANDOFF_READY.json \
    --strict-gate \
    --out "$OUT_DIR/protocol-intake.md" 2>&1 | tee "$OUT_DIR/protocol-intake.log"
)

GIT_COMMIT="$(git -C "$ROOT_DIR" rev-parse HEAD)"
GIT_BRANCH="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD)"
GIT_STATUS="$(git -C "$ROOT_DIR" status --short || true)"

{
  echo "generated_at_utc=$STAMP"
  echo "git_commit=$GIT_COMMIT"
  echo "git_branch=$GIT_BRANCH"
  if [[ -z "$GIT_STATUS" ]]; then
    echo "git_status=clean"
  else
    echo "git_status=dirty"
  fi
  echo "lean_toolchain=$(cat "$ROOT_DIR/lean-toolchain")"
  echo "lake_version=$($LAKE_BIN --version | tr '\n' ' ' | sed 's/  */ /g')"
  echo "forge_version=$($FORGE_BIN --version | head -n 1)"
  if [[ -x "$ROOT_DIR/.venv-security/bin/python" ]]; then
    SLITHER_VER="$("$ROOT_DIR/.venv-security/bin/python" -m pip show slither-analyzer 2>/dev/null \
      | awk '/^Version:/{print $2}' | head -n 1)"
    if [[ -n "$SLITHER_VER" ]]; then
      echo "slither_version=$SLITHER_VER"
    fi
  fi
  echo "python_version=$(python3 --version 2>&1)"
} > "$OUT_DIR/versions.txt"

cat > "$OUT_DIR/COMMANDS.txt" <<'EOF_CMDS'
# Commands executed by scripts/review_package.sh

1. lake exe cache get
2. lake build
3. python3 scripts/theorem_inventory.py --out <out>/theorem-inventory.md
4. python3 scripts/theorem_inventory.py --check-verification
5. python3 scripts/validate_theorem_inventory.py
6. (cd solidity && forge test --gas-report)
7. (cd solidity && forge test --json)
8. (cd solidity && forge coverage --report summary --report lcov)
9. python3 coverage gate parser (same thresholds as CI)
10. SLITHER_SARIF=<out>/slither.sarif ./scripts/security/slither.sh
11. python3 scripts/intake_validate.py --strict-gate (template payloads)
EOF_CMDS

cat > "$OUT_DIR/MANIFEST.md" <<EOF_MANIFEST
# CPAMM Review Package

Generated: $STAMP
Commit: $GIT_COMMIT
Branch: $GIT_BRANCH

## Included Evidence

- Lean cache log: lake-cache.log
- Lean build log: lake-build.log
- Theorem inventory: theorem-inventory.md
- Theorem inventory sync log: theorem-inventory-sync.log
- Theorem inventory validation log: theorem-inventory-validation.log
- Forge human log: forge-test.log
- Forge JSON report: forge-test.json
- Forge coverage log: forge-coverage.log
- Coverage gate report: coverage-gate.log
- LCOV report: lcov.info
- Slither log: slither.log
- Slither SARIF: slither.sarif
- Protocol intake report: protocol-intake.md
- Protocol intake log: protocol-intake.log
- Toolchain metadata: versions.txt
- Command transcript list: COMMANDS.txt
- Checksums: SHA256SUMS

## Coverage Gate Results

\`\`\`
$(cat "$OUT_DIR/coverage-gate.log")
\`\`\`

## Re-run

\`\`\`bash
./scripts/review_package.sh
\`\`\`
EOF_MANIFEST

(
  cd "$OUT_DIR"
  shasum -a 256 \
    COMMANDS.txt \
    MANIFEST.md \
    coverage-gate.log \
    forge-coverage.log \
    forge-test.json \
    forge-test.log \
    lake-build.log \
    lake-cache.log \
    lcov.info \
    protocol-intake.log \
    protocol-intake.md \
    slither.log \
    slither.sarif \
    theorem-inventory.md \
    theorem-inventory-sync.log \
    theorem-inventory-validation.log \
    versions.txt > SHA256SUMS
)

TARBALL="${OUT_DIR%/}.tar.gz"
tar -czf "$TARBALL" -C "$(dirname "$OUT_DIR")" "$(basename "$OUT_DIR")"

echo "==> review package complete"
echo "directory: $OUT_DIR"
echo "tarball:   $TARBALL"
