# Execution Assets

These are operational templates for running the commercialization plan.

## CRM

- `crm/CRM_SCHEMA.md`
- `crm/PIPELINE_TEMPLATE.csv`

## Sales

- `sales/OUTBOUND_TEMPLATES.md`
- `sales/DISCOVERY_CALL_RUNBOOK.md`
- `sales/FOLLOW_UP_SEQUENCE.md`

## Contracts

- `contracts/PROPOSAL_TEMPLATE.md`
- `contracts/SOW_TEMPLATE.md`
- `contracts/ACCEPTANCE_CRITERIA_TEMPLATE.md`

## Portal

- `portal/PORTAL_INPUT_TEMPLATE.json`
- `portal/README.md`

## Ops

- `ops/KPI_TRACKER_TEMPLATE.csv`
- `ops/WEEKLY_DASHBOARD_TEMPLATE.md`
- `ops/CADENCE_AUTOMATION_CONFIG.md`

## Automation

Generate a live weekly dashboard from trackers:

```bash
# one-time setup for private working copies
mkdir -p strategy/private
cp strategy/assets/crm/PIPELINE_TEMPLATE.csv strategy/private/PIPELINE.csv
cp strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv strategy/private/KPI_TRACKER.csv

python3 scripts/strategy_dashboard.py \
  --pipeline strategy/private/PIPELINE.csv \
  --kpi strategy/private/KPI_TRACKER.csv \
  --out reports/WEEKLY_DASHBOARD.md
```

Generate proposal + SOW deal docs from a structured JSON input:

```bash
mkdir -p strategy/private/deals
cp strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json strategy/private/deals/example.json

python3 scripts/deal_pack.py \
  --input strategy/private/deals/example.json \
  --include-acceptance-template
```

The default output is written under `strategy/private/generated/<deal_id>/`.

Generate a pipeline health score and forecast report:

```bash
python3 scripts/pipeline_health.py \
  --pipeline strategy/private/PIPELINE.csv \
  --as-of 2026-03-01 \
  --out reports/PIPELINE_HEALTH.md
```

Generate a prioritized outbound focus queue:

```bash
python3 scripts/outbound_focus.py \
  --pipeline strategy/private/PIPELINE.csv \
  --as-of 2026-03-01 \
  --out reports/OUTBOUND_FOCUS.md \
  --csv-out reports/OUTBOUND_FOCUS.csv
```

Run outbound SLA checks:

```bash
python3 scripts/outbound_sla_gate.py \
  --pipeline strategy/private/PIPELINE.csv \
  --as-of 2026-03-01 \
  --out reports/OUTBOUND_SLA.md \
  --json-out reports/OUTBOUND_SLA.json \
  --strict
```

Validate operating data before running automation:

```bash
python3 scripts/validate_strategy_data.py \
  --pipeline strategy/private/PIPELINE.csv \
  --kpi strategy/private/KPI_TRACKER.csv \
  --deal-input strategy/private/deals/example.json \
  --portal-input strategy/private/portals/example.json
```

Generate a single commercialization review bundle:

```bash
./scripts/commercial_review_package.sh \
  --pipeline strategy/private/PIPELINE.csv \
  --kpi strategy/private/KPI_TRACKER.csv \
  --deal-input strategy/private/deals/example.json \
  --portal-input strategy/private/portals/example.json \
  --as-of 2026-03-01
```

Default bundle output path: `artifacts/commercial-review-package-<utcstamp>/`.

Generate an evidence portal for a client engagement:

```bash
mkdir -p strategy/private/portals
cp strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json strategy/private/portals/example.json

python3 scripts/evidence_portal.py \
  --input strategy/private/portals/example.json \
  --commercial-package-dir artifacts/commercial-review-package \
  --review-package-dir artifacts/review-package \
  --portal-dir strategy/private/portals/example-protocol-a-2026q1 \
  --copy-artifacts
```

Cadence issue automation:

- Workflow: `.github/workflows/operating-cadence.yml`
- Uses `scripts/create_cadence_issue.py` to open recurring KPI and risk-review issues.
- Supports manual workflow dispatch with optional `reference_date` override.
- Supports optional assignee routing via repo variables (`CADENCE_KPI_ASSIGNEES`, `CADENCE_RISK_ASSIGNEES`).
- Supports optional webhook notifications via secret `CADENCE_NOTIFY_WEBHOOK_URL`.
- KPI runs generate/upload outbound digest artifacts and post a digest comment on the created cadence issue.
- Optional SLA threshold/strictness vars are documented in `ops/CADENCE_AUTOMATION_CONFIG.md`.
- Configuration guide: `ops/CADENCE_AUTOMATION_CONFIG.md`.

Commercial package CI artifact:

- Workflow: `.github/workflows/ci.yml` job `commercial-review-package`
- Builds a sanitized commercialization bundle from template data each push/PR.
- Publishes artifact names: `commercial-review-package` directory and tarball.
- Includes outbound execution artifacts (`OUTBOUND_FOCUS.md`, `OUTBOUND_FOCUS.csv`, `OUTBOUND_SLA.md`, `OUTBOUND_SLA.json`).

Evidence portal publish automation:

- Workflow: `.github/workflows/evidence-portal-publish.yml`
- Weekly scheduled refresh plus manual dispatch.
- Publishes `evidence-portal` artifact, and optional linked commercial package artifact outputs.
