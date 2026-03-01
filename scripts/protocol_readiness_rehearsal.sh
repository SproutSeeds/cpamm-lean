#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RIGIDITYCORE_ROOT="${1:-${RIGIDITYCORE_ROOT:-/Users/codymitchell/Documents/code/RigidityCore}}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${2:-$ROOT_DIR/artifacts/protocol-readiness-$STAMP}"

if [[ "$OUT_DIR" != /* ]]; then
  OUT_DIR="$ROOT_DIR/$OUT_DIR"
fi

mkdir -p "$OUT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found" >&2
  exit 1
fi

if [[ ! -d "$RIGIDITYCORE_ROOT" ]]; then
  echo "error: RigidityCore root not found: $RIGIDITYCORE_ROOT" >&2
  exit 1
fi

TARGETS=(
  "aave/session1"
  "balancer/session1"
)

SUMMARY_ROWS=()
OVERALL_STATUS=0

for target in "${TARGETS[@]}"; do
  target_slug="${target//\//_}"
  system_json="$RIGIDITYCORE_ROOT/targets/$target/System.json"
  handoff_json="$OUT_DIR/${target_slug}.HANDOFF_READY.json"
  intake_md="$OUT_DIR/${target_slug}.protocol-intake.md"
  intake_log="$OUT_DIR/${target_slug}.protocol-intake.log"

  if [[ ! -f "$system_json" ]]; then
    SUMMARY_ROWS+=("| \`$target\` | SKIP | \`$system_json\` missing |")
    continue
  fi

  system_id="$(python3 - "$system_json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("system_id", "unknown_system"))
PY
)"

  python3 - "$handoff_json" "$system_id" "$target_slug" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
system_id = sys.argv[2]
target_slug = sys.argv[3]

payload = {
    "schema_version": "0.1",
    "handoff_id": f"{target_slug}_handoff_ready",
    "system_id": system_id,
    "finding_id": f"finding_{target_slug}_confirmed_lane",
    "lane_id": f"lane_{target_slug}_confirmed_lane",
    "source_repo": "RigidityCore",
    "target_repo": "cpamm-lean",
    "gate": {
        "contract_replay_determinism_established": True,
        "audit_dedup_clear": True,
        "measurable_impact_signal": True,
    },
    "evidence": {
        "replay_artifacts": [
            f"targets/{target_slug.replace('_', '/')}/System.json",
            f"ops/runs/<timestamp>/{target_slug}/replay_summary.md",
        ],
        "dedup_record": f"ops/runs/<timestamp>/{target_slug}/audit-dedup/audit_dedup_gate.md",
        "impact_summary": "Lane marked ready for cpamm-lean strict intake rehearsal.",
    },
    "assumptions": [
        "Rehearsal payload generated for strict-gate intake validation only.",
    ],
    "boundaries": "No protocol claim implied by rehearsal-only payload.",
}

out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

  set +e
  python3 "$ROOT_DIR/scripts/intake_validate.py" \
    --system-json "$system_json" \
    --handoff-json "$handoff_json" \
    --strict-gate \
    --out "$intake_md" >"$intake_log" 2>&1
  rc=$?
  set -e

  if [[ $rc -eq 0 ]]; then
    SUMMARY_ROWS+=("| \`$target\` | PASS | \`$intake_md\` |")
  else
    OVERALL_STATUS=1
    SUMMARY_ROWS+=("| \`$target\` | FAIL | \`$intake_log\` |")
  fi
done

packet="$OUT_DIR/READY_TO_PROVE_PACKET.md"
{
  echo "# Protocol Readiness Rehearsal"
  echo
  echo "- generated_at_utc: \`$STAMP\`"
  echo "- rigiditycore_root: \`$RIGIDITYCORE_ROOT\`"
  echo "- cpamm_lean_root: \`$ROOT_DIR\`"
  echo "- strict_gate: \`true\`"
  echo
  echo "## Results"
  echo
  echo "| Target | Status | Evidence |"
  echo "|---|---|---|"
  for row in "${SUMMARY_ROWS[@]}"; do
    echo "$row"
  done
  echo
  echo "## Generated Files"
  echo
  echo "- \`*.HANDOFF_READY.json\` (rehearsal handoff payloads)"
  echo "- \`*.protocol-intake.md\` (validator reports)"
  echo "- \`*.protocol-intake.log\` (validator logs)"
  echo
  echo "## Command"
  echo
  echo "\`\`\`bash"
  echo "./scripts/protocol_readiness_rehearsal.sh \"$RIGIDITYCORE_ROOT\" \"$OUT_DIR\""
  echo "\`\`\`"
} > "$packet"

echo "wrote readiness packet: $packet"
if [[ $OVERALL_STATUS -eq 0 ]]; then
  echo "protocol readiness rehearsal passed"
else
  echo "protocol readiness rehearsal failed; see packet and logs" >&2
fi

exit "$OVERALL_STATUS"
