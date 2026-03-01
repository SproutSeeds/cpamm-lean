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
