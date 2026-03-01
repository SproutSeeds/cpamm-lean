#!/usr/bin/env python3
"""Evaluate outbound execution SLAs from pipeline data."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass
class Opportunity:
    account_name: str
    status: str
    stage: str
    owner: str
    next_action: str
    next_action_date: date | None
    last_touch_date: date | None


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        y, m, d = value.split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def parse_as_of(value: str | None) -> date:
    if not value:
        return date.today()
    parsed = parse_date(value)
    if parsed is None:
        raise ValueError(f"invalid --as-of date, expected YYYY-MM-DD: {value}")
    return parsed


def read_pipeline(path: Path) -> list[Opportunity]:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    out: list[Opportunity] = []
    for row in rows:
        out.append(
            Opportunity(
                account_name=row.get("account_name", "").strip(),
                status=row.get("status", "").strip().lower(),
                stage=row.get("stage", "").strip().lower(),
                owner=row.get("owner", "").strip(),
                next_action=row.get("next_action", "").strip(),
                next_action_date=parse_date(row.get("next_action_date", "")),
                last_touch_date=parse_date(row.get("last_touch_date", "")),
            )
        )
    return out


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def render_report(
    *,
    as_of: date,
    stale_days: int,
    due_window_days: int,
    candidate_count: int,
    overdue_count: int,
    due_7d_count: int,
    missing_action_count: int,
    missing_action_date_count: int,
    stale_count: int,
    max_overdue_ratio: float,
    max_missing_action_ratio: float,
    max_stale_ratio: float,
    breach_messages: list[str],
) -> str:
    overdue_ratio = ratio(overdue_count, candidate_count)
    missing_action_ratio = ratio(missing_action_count, candidate_count)
    stale_ratio = ratio(stale_count, candidate_count)
    missing_action_date_ratio = ratio(missing_action_date_count, candidate_count)

    lines: list[str] = []
    lines.append("# Outbound SLA Gate")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- As of: {as_of.isoformat()}")
    lines.append(f"- Candidate opportunities (`open` + `nurture`): {candidate_count}")
    lines.append(f"- Overdue actions: {overdue_count} ({overdue_ratio:.1%})")
    lines.append(f"- Due in next {due_window_days} days: {due_7d_count}")
    lines.append(f"- Missing `next_action`: {missing_action_count} ({missing_action_ratio:.1%})")
    lines.append(f"- Missing `next_action_date`: {missing_action_date_count} ({missing_action_date_ratio:.1%})")
    lines.append(f"- Stale opportunities (> {stale_days} days since touch): {stale_count} ({stale_ratio:.1%})")
    lines.append("")
    lines.append("## SLA Thresholds")
    lines.append("")
    lines.append(f"- Max overdue ratio: {max_overdue_ratio:.1%}")
    lines.append(f"- Max missing-action ratio: {max_missing_action_ratio:.1%}")
    lines.append(f"- Max stale ratio: {max_stale_ratio:.1%}")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    if breach_messages:
        lines.append("- Status: FAIL")
        for msg in breach_messages:
            lines.append(f"- Breach: {msg}")
    else:
        lines.append("- Status: PASS")
        lines.append("- No SLA breaches detected.")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", required=True, type=Path, help="Path to pipeline CSV.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD (default: today UTC).")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/OUTBOUND_SLA.md"),
        help="Markdown output path (default: reports/OUTBOUND_SLA.md).",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON output path for machine-readable gate results.",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=7,
        help="Days since last touch considered stale (default: 7).",
    )
    parser.add_argument(
        "--due-window-days",
        type=int,
        default=7,
        help="Upcoming action window in days (default: 7).",
    )
    parser.add_argument(
        "--max-overdue-ratio",
        type=float,
        default=0.35,
        help="Maximum allowed overdue next-action ratio (default: 0.35).",
    )
    parser.add_argument(
        "--max-missing-action-ratio",
        type=float,
        default=0.25,
        help="Maximum allowed missing `next_action` ratio (default: 0.25).",
    )
    parser.add_argument(
        "--max-stale-ratio",
        type=float,
        default=0.40,
        help="Maximum allowed stale-opportunity ratio (default: 0.40).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when SLA breaches are detected.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    as_of = parse_as_of(args.as_of)
    opportunities = read_pipeline(args.pipeline)
    candidates = [
        opp
        for opp in opportunities
        if opp.status in {"open", "nurture"} and opp.stage != "closed"
    ]

    due_cutoff = as_of + timedelta(days=args.due_window_days)
    candidate_count = len(candidates)
    overdue_count = sum(
        1 for opp in candidates if opp.next_action_date is not None and opp.next_action_date < as_of
    )
    due_7d_count = sum(
        1 for opp in candidates if opp.next_action_date is not None and as_of <= opp.next_action_date <= due_cutoff
    )
    missing_action_count = sum(1 for opp in candidates if not opp.next_action)
    missing_action_date_count = sum(1 for opp in candidates if opp.next_action_date is None)
    stale_cutoff = as_of - timedelta(days=args.stale_days)
    stale_count = sum(
        1 for opp in candidates if opp.last_touch_date is not None and opp.last_touch_date < stale_cutoff
    )

    overdue_ratio = ratio(overdue_count, candidate_count)
    missing_action_ratio = ratio(missing_action_count, candidate_count)
    stale_ratio = ratio(stale_count, candidate_count)

    breaches: list[str] = []
    if overdue_ratio > args.max_overdue_ratio:
        breaches.append(
            f"overdue ratio {overdue_ratio:.1%} exceeds max {args.max_overdue_ratio:.1%}"
        )
    if missing_action_ratio > args.max_missing_action_ratio:
        breaches.append(
            f"missing-action ratio {missing_action_ratio:.1%} exceeds max {args.max_missing_action_ratio:.1%}"
        )
    if stale_ratio > args.max_stale_ratio:
        breaches.append(
            f"stale ratio {stale_ratio:.1%} exceeds max {args.max_stale_ratio:.1%}"
        )

    report = render_report(
        as_of=as_of,
        stale_days=args.stale_days,
        due_window_days=args.due_window_days,
        candidate_count=candidate_count,
        overdue_count=overdue_count,
        due_7d_count=due_7d_count,
        missing_action_count=missing_action_count,
        missing_action_date_count=missing_action_date_count,
        stale_count=stale_count,
        max_overdue_ratio=args.max_overdue_ratio,
        max_missing_action_ratio=args.max_missing_action_ratio,
        max_stale_ratio=args.max_stale_ratio,
        breach_messages=breaches,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"wrote outbound SLA report: {args.out}")

    payload = {
        "as_of": as_of.isoformat(),
        "candidate_count": candidate_count,
        "overdue_count": overdue_count,
        "due_window_days": args.due_window_days,
        "due_7d_count": due_7d_count,
        "missing_action_count": missing_action_count,
        "missing_action_date_count": missing_action_date_count,
        "stale_days": args.stale_days,
        "stale_count": stale_count,
        "max_overdue_ratio": args.max_overdue_ratio,
        "max_missing_action_ratio": args.max_missing_action_ratio,
        "max_stale_ratio": args.max_stale_ratio,
        "overdue_ratio": overdue_ratio,
        "missing_action_ratio": missing_action_ratio,
        "stale_ratio": stale_ratio,
        "status": "fail" if breaches else "pass",
        "breaches": breaches,
    }

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote outbound SLA json: {args.json_out}")

    if breaches and args.strict:
        print("error: outbound SLA breaches detected:")
        for msg in breaches:
            print(f"- {msg}")
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f"error: {err}")
        raise SystemExit(1)
