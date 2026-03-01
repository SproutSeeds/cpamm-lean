#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

OUT_DIR="${ROOT_DIR}/artifacts/commercial-review-package-${STAMP}"
PIPELINE_PATH="${ROOT_DIR}/strategy/private/PIPELINE.csv"
KPI_PATH="${ROOT_DIR}/strategy/private/KPI_TRACKER.csv"
DEAL_INPUT_PATH=""
PORTAL_INPUT_PATH=""
PORTAL_DIR=""
AS_OF_DATE="$(date -u +%F)"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/commercial_review_package.sh [options]

Options:
  --pipeline <path>     Pipeline CSV (default: strategy/private/PIPELINE.csv)
  --kpi <path>          KPI CSV (default: strategy/private/KPI_TRACKER.csv)
  --deal-input <path>   Optional deal JSON for proposal/SOW generation
  --portal-input <path> Optional portal JSON for evidence portal generation
  --portal-dir <path>   Optional portal output directory (default: <out>/evidence-portal)
  --as-of <YYYY-MM-DD>  Snapshot date for pipeline health (default: today UTC)
  --out-dir <path>      Output directory (default: artifacts/commercial-review-package-<utcstamp>)
  -h, --help            Show this help message
EOF
}

make_abs() {
  local candidate="$1"
  if [[ "$candidate" = /* ]]; then
    printf "%s" "$candidate"
  else
    printf "%s/%s" "$ROOT_DIR" "$candidate"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pipeline)
      PIPELINE_PATH="$(make_abs "$2")"
      shift 2
      ;;
    --kpi)
      KPI_PATH="$(make_abs "$2")"
      shift 2
      ;;
    --deal-input)
      DEAL_INPUT_PATH="$(make_abs "$2")"
      shift 2
      ;;
    --portal-input)
      PORTAL_INPUT_PATH="$(make_abs "$2")"
      shift 2
      ;;
    --portal-dir)
      PORTAL_DIR="$(make_abs "$2")"
      shift 2
      ;;
    --as-of)
      AS_OF_DATE="$2"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="$(make_abs "$2")"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found" >&2
  exit 1
fi

if [[ ! -f "$PIPELINE_PATH" ]]; then
  echo "error: missing pipeline CSV: $PIPELINE_PATH" >&2
  exit 1
fi

if [[ ! -f "$KPI_PATH" ]]; then
  echo "error: missing KPI CSV: $KPI_PATH" >&2
  exit 1
fi

if [[ -n "$DEAL_INPUT_PATH" && ! -f "$DEAL_INPUT_PATH" ]]; then
  echo "error: missing deal input JSON: $DEAL_INPUT_PATH" >&2
  exit 1
fi

if [[ -n "$PORTAL_INPUT_PATH" && ! -f "$PORTAL_INPUT_PATH" ]]; then
  echo "error: missing portal input JSON: $PORTAL_INPUT_PATH" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "==> output: $OUT_DIR"
echo "==> validate input data"
VALIDATE_ARGS=(
  "--pipeline" "$PIPELINE_PATH"
  "--kpi" "$KPI_PATH"
)
if [[ -n "$DEAL_INPUT_PATH" ]]; then
  VALIDATE_ARGS+=("--deal-input" "$DEAL_INPUT_PATH")
fi
if [[ -n "$PORTAL_INPUT_PATH" ]]; then
  VALIDATE_ARGS+=("--portal-input" "$PORTAL_INPUT_PATH")
fi
python3 "$ROOT_DIR/scripts/validate_strategy_data.py" "${VALIDATE_ARGS[@]}" \
  | tee "$OUT_DIR/strategy-data-validation.log"

echo "==> weekly dashboard"
python3 "$ROOT_DIR/scripts/strategy_dashboard.py" \
  --pipeline "$PIPELINE_PATH" \
  --kpi "$KPI_PATH" \
  --out "$OUT_DIR/WEEKLY_DASHBOARD.md"

echo "==> pipeline health"
python3 "$ROOT_DIR/scripts/pipeline_health.py" \
  --pipeline "$PIPELINE_PATH" \
  --as-of "$AS_OF_DATE" \
  --out "$OUT_DIR/PIPELINE_HEALTH.md"

echo "==> outbound focus"
python3 "$ROOT_DIR/scripts/outbound_focus.py" \
  --pipeline "$PIPELINE_PATH" \
  --as-of "$AS_OF_DATE" \
  --out "$OUT_DIR/OUTBOUND_FOCUS.md" \
  --csv-out "$OUT_DIR/OUTBOUND_FOCUS.csv"

if [[ -n "$DEAL_INPUT_PATH" ]]; then
  echo "==> deal pack"
  python3 "$ROOT_DIR/scripts/deal_pack.py" \
    --input "$DEAL_INPUT_PATH" \
    --out-dir "$OUT_DIR/deal-pack" \
    --include-acceptance-template
fi

if [[ -n "$PORTAL_INPUT_PATH" ]]; then
  if [[ -z "$PORTAL_DIR" ]]; then
    PORTAL_DIR="$OUT_DIR/evidence-portal"
  fi
  echo "==> evidence portal"
  python3 "$ROOT_DIR/scripts/evidence_portal.py" \
    --input "$PORTAL_INPUT_PATH" \
    --portal-dir "$PORTAL_DIR" \
    --commercial-package-dir "$OUT_DIR"
fi

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
  echo "python_version=$(python3 --version 2>&1)"
  echo "as_of_date=$AS_OF_DATE"
  echo "pipeline_source=$PIPELINE_PATH"
  echo "kpi_source=$KPI_PATH"
  if [[ -n "$DEAL_INPUT_PATH" ]]; then
    echo "deal_input_source=$DEAL_INPUT_PATH"
  fi
} > "$OUT_DIR/versions.txt"

{
  echo "# Commands executed by scripts/commercial_review_package.sh"
  echo ""
  echo "1. python3 scripts/validate_strategy_data.py --pipeline <pipeline> --kpi <kpi> [--deal-input <deal-json>]"
  echo "2. python3 scripts/strategy_dashboard.py --pipeline <pipeline> --kpi <kpi> --out <out>/WEEKLY_DASHBOARD.md"
  echo "3. python3 scripts/pipeline_health.py --pipeline <pipeline> --as-of <date> --out <out>/PIPELINE_HEALTH.md"
  echo "4. python3 scripts/outbound_focus.py --pipeline <pipeline> --as-of <date> --out <out>/OUTBOUND_FOCUS.md --csv-out <out>/OUTBOUND_FOCUS.csv"
  if [[ -n "$DEAL_INPUT_PATH" ]]; then
    echo "5. python3 scripts/deal_pack.py --input <deal-json> --out-dir <out>/deal-pack --include-acceptance-template"
  fi
  if [[ -n "$PORTAL_INPUT_PATH" ]]; then
    echo "6. python3 scripts/evidence_portal.py --input <portal-json> --portal-dir <dir> --commercial-package-dir <out>"
  fi
} > "$OUT_DIR/COMMANDS.txt"

cat > "$OUT_DIR/MANIFEST.md" <<EOF_MANIFEST
# Commercial Review Package

Generated: $STAMP
Commit: $GIT_COMMIT
Branch: $GIT_BRANCH

## Included Artifacts

- Weekly dashboard: WEEKLY_DASHBOARD.md
- Pipeline health report: PIPELINE_HEALTH.md
- Outbound focus queue: OUTBOUND_FOCUS.md + OUTBOUND_FOCUS.csv
$(if [[ -n "$DEAL_INPUT_PATH" ]]; then echo "- Deal pack: deal-pack/"; fi)
$(if [[ -n "$PORTAL_INPUT_PATH" ]]; then echo "- Evidence portal: ${PORTAL_DIR}"; fi)
- Strategy data validation log: strategy-data-validation.log
- Toolchain and source metadata: versions.txt
- Command transcript list: COMMANDS.txt
- Checksums: SHA256SUMS

## Re-run

\`\`\`bash
./scripts/commercial_review_package.sh
\`\`\`
EOF_MANIFEST

CHECKSUM_FILES=(
  "COMMANDS.txt"
  "MANIFEST.md"
  "OUTBOUND_FOCUS.csv"
  "OUTBOUND_FOCUS.md"
  "PIPELINE_HEALTH.md"
  "strategy-data-validation.log"
  "WEEKLY_DASHBOARD.md"
  "versions.txt"
)

if [[ -n "$DEAL_INPUT_PATH" ]]; then
  CHECKSUM_FILES+=(
    "deal-pack/ACCEPTANCE_CRITERIA.md"
    "deal-pack/MANIFEST.json"
    "deal-pack/PROPOSAL.md"
    "deal-pack/SOW.md"
  )
fi

(
  cd "$OUT_DIR"
  shasum -a 256 "${CHECKSUM_FILES[@]}" > SHA256SUMS
)

TARBALL="${OUT_DIR%/}.tar.gz"
tar -czf "$TARBALL" -C "$(dirname "$OUT_DIR")" "$(basename "$OUT_DIR")"

echo "==> commercial review package complete"
echo "directory: $OUT_DIR"
echo "tarball:   $TARBALL"
