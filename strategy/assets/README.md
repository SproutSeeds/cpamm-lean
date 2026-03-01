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

## Ops

- `ops/KPI_TRACKER_TEMPLATE.csv`
- `ops/WEEKLY_DASHBOARD_TEMPLATE.md`

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

Validate operating data before running automation:

```bash
python3 scripts/validate_strategy_data.py \
  --pipeline strategy/private/PIPELINE.csv \
  --kpi strategy/private/KPI_TRACKER.csv \
  --deal-input strategy/private/deals/example.json
```

Generate a single commercialization review bundle:

```bash
./scripts/commercial_review_package.sh \
  --pipeline strategy/private/PIPELINE.csv \
  --kpi strategy/private/KPI_TRACKER.csv \
  --deal-input strategy/private/deals/example.json \
  --as-of 2026-03-01
```

Default bundle output path: `artifacts/commercial-review-package-<utcstamp>/`.

Cadence issue automation:

- Workflow: `.github/workflows/operating-cadence.yml`
- Uses `scripts/create_cadence_issue.py` to open recurring KPI and risk-review issues.
- Supports manual workflow dispatch with optional `reference_date` override.

Commercial package CI artifact:

- Workflow: `.github/workflows/ci.yml` job `commercial-review-package`
- Builds a sanitized commercialization bundle from template data each push/PR.
- Publishes artifact names: `commercial-review-package` directory and tarball.
