#!/usr/bin/env python3
"""Generate a weekly commercialization dashboard from KPI and pipeline CSVs."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        y, m, d = value.split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def latest_kpi(rows: list[dict[str, str]]) -> dict[str, str]:
    if not rows:
        return {}

    def key(row: dict[str, str]) -> tuple[int, str]:
        d = parse_date(row.get("week_start", ""))
        return (0 if d is None else 1, row.get("week_start", ""))

    return sorted(rows, key=key)[-1]


def pipeline_summary(rows: list[dict[str, str]], week_start: date | None) -> tuple[int, float, int]:
    open_rows = [r for r in rows if r.get("status", "").strip().lower() == "open"]

    weighted = 0.0
    for r in open_rows:
        acv = parse_float(r.get("acv_usd", "0"))
        prob = parse_float(r.get("probability_pct", "0"))
        weighted += acv * prob / 100.0

    next_actions_due = 0
    if week_start is not None:
        week_end = week_start.toordinal() + 6
        for r in open_rows:
            d = parse_date(r.get("next_action_date", ""))
            if d is None:
                continue
            if week_start.toordinal() <= d.toordinal() <= week_end:
                next_actions_due += 1

    return len(open_rows), weighted, next_actions_due


def render_dashboard(kpi: dict[str, str], open_count: int, weighted_usd: float, next_due: int) -> str:
    ws = kpi.get("week_start", "")
    notes = kpi.get("notes", "")

    def get(field: str) -> str:
        return kpi.get(field, "")

    return f"""# Weekly Dashboard

## Week Of

- Week start: {ws}

## North-Star Snapshot

1. Verified releases: {get('verified_releases')}
2. Paid customers: {get('paid_customers')}
3. MRR (USD): {get('mrr_usd')}
4. Time-to-green-release (days): {get('time_to_green_days')}

## Commercial

1. Discovery calls: {get('discovery_calls')}
2. Proposal win rate (%): {get('proposal_win_rate_pct')}
3. Sprint-to-retainer (%): {get('sprint_to_retainer_pct')}
4. NRR (%): {get('nrr_pct')}

## Delivery And Quality

1. Critical issues found: {get('critical_issues_found')}
2. Regression escapes: {get('regression_escapes')}
3. CI gate pass rate (%): {get('ci_gate_pass_rate_pct')}
4. Evidence package success rate (%): {get('evidence_pkg_success_pct')}

## Productization And Support

1. Automation (%): {get('automation_pct')}
2. Support tickets per customer: {get('support_tickets_per_customer')}
3. MTTR (hours): {get('mttr_hours')}

## Pipeline Snapshot

- Total open opportunities: {open_count}
- Weighted pipeline (USD): {weighted_usd:,.2f}
- Next 7-day actions due: {next_due}

## Notes

- {notes}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", required=True, type=Path)
    parser.add_argument("--kpi", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    pipeline_rows = read_csv(args.pipeline)
    kpi_rows = read_csv(args.kpi)

    if not kpi_rows:
        raise ValueError("kpi CSV has no rows")

    kpi = latest_kpi(kpi_rows)
    week_start = parse_date(kpi.get("week_start", ""))
    open_count, weighted_usd, next_due = pipeline_summary(pipeline_rows, week_start)

    rendered = render_dashboard(kpi, open_count, weighted_usd, next_due)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(f"wrote dashboard: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
