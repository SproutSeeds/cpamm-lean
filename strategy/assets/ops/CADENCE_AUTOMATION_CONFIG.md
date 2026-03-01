# Cadence Automation Config

Use this guide to configure assignees and notifications for recurring KPI/risk issue automation.

## Workflow

- `.github/workflows/operating-cadence.yml`

## Repository Variables

Set these in GitHub repository `Settings -> Secrets and variables -> Actions -> Variables`:

1. `CADENCE_KPI_ASSIGNEES`
- Comma-separated GitHub logins assigned on weekly KPI issues.
- Example: `founder,ops-lead`

2. `CADENCE_RISK_ASSIGNEES`
- Comma-separated GitHub logins assigned on monthly risk issues.
- Example: `founder,security-lead`

## Repository Secret (Optional)

Set in `Settings -> Secrets and variables -> Actions -> Secrets`:

1. `CADENCE_NOTIFY_WEBHOOK_URL`
- Optional webhook URL for notifications when issues are created.
- If set, `scripts/create_cadence_issue.py` posts a compact JSON payload.

## Manual Testing

```bash
python3 scripts/create_cadence_issue.py \
  --kind kpi \
  --reference-date 2026-03-02 \
  --assignees founder,ops-lead \
  --dry-run
```
