# Cadence Automation Config

Use this guide to configure assignees and notifications for recurring KPI/risk issue automation.

## Workflow

- `.github/workflows/operating-cadence.yml`

## Repository Variables

Set these in GitHub repository `Settings -> Secrets and variables -> Actions -> Variables`:

1. `ENABLE_COMMERCIAL_AUTOMATION`
- Set to `true` to enable commercial/cadence workflow jobs in this repo.
- Default behavior is disabled when unset.

2. `CADENCE_KPI_ASSIGNEES`
- Comma-separated GitHub logins assigned on weekly KPI issues.
- Example: `founder,ops-lead`

3. `CADENCE_RISK_ASSIGNEES`
- Comma-separated GitHub logins assigned on monthly risk issues.
- Example: `founder,security-lead`

4. `CADENCE_MAX_OVERDUE_RATIO` (optional)
- Override for outbound SLA max overdue ratio in KPI digest runs.
- Example: `0.30`

5. `CADENCE_MAX_MISSING_ACTION_RATIO` (optional)
- Override for outbound SLA max missing-action ratio in KPI digest runs.
- Example: `0.20`

6. `CADENCE_MAX_STALE_RATIO` (optional)
- Override for outbound SLA max stale ratio in KPI digest runs.
- Example: `0.35`

7. `CADENCE_OUTBOUND_SLA_STRICT` (optional)
- Set to `true` to fail KPI cadence workflow runs when outbound SLA thresholds are breached.
- Default behavior is report-only (`false`/unset).

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
  --result-json-out /tmp/kpi-cadence-result.json \
  --dry-run
```
