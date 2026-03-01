#!/usr/bin/env python3
"""Generate a pipeline health report and score from CRM pipeline CSV data."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass
class Opportunity:
    account_name: str
    status: str
    stage: str
    acv_usd: float
    probability_pct: float
    expected_close_date: date | None
    next_action: str
    next_action_date: date | None
    last_touch_date: date | None
    owner: str
    notes: str

    @property
    def weighted_value(self) -> float:
        return self.acv_usd * self.probability_pct / 100.0


@dataclass
class ScoreBreakdown:
    coverage: float
    weighted_pipeline: float
    stale_hygiene: float
    action_hygiene: float
    close_horizon: float

    @property
    def total(self) -> float:
        return self.coverage + self.weighted_pipeline + self.stale_hygiene + self.action_hygiene + self.close_horizon


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


def parse_as_of(value: str | None) -> date:
    if value is None:
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
                acv_usd=parse_float(row.get("acv_usd", "0")),
                probability_pct=parse_float(row.get("probability_pct", "0")),
                expected_close_date=parse_date(row.get("expected_close_date", "")),
                next_action=row.get("next_action", "").strip(),
                next_action_date=parse_date(row.get("next_action_date", "")),
                last_touch_date=parse_date(row.get("last_touch_date", "")),
                owner=row.get("owner", "").strip(),
                notes=row.get("notes", "").strip(),
            )
        )
    return out


def count_stage(open_opps: list[Opportunity]) -> dict[str, int]:
    stages = ["lead", "discovery", "proposal", "negotiation"]
    counts = {stage: 0 for stage in stages}
    for opp in open_opps:
        stage = opp.stage or "unknown"
        if stage not in counts:
            counts[stage] = 0
        counts[stage] += 1
    return counts


def weighted_by_stage(open_opps: list[Opportunity]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for opp in open_opps:
        stage = opp.stage or "unknown"
        totals[stage] = totals.get(stage, 0.0) + opp.weighted_value
    return totals


def score_pipeline(
    open_opps: list[Opportunity],
    stale_opps: list[Opportunity],
    due_7d_count: int,
    with_action_count: int,
    weighted_total: float,
    expected_60d: float,
    target_open_count: int,
    target_weighted_pipeline: float,
    target_expected_60d: float,
) -> ScoreBreakdown:
    open_count = len(open_opps)

    # 20 points: open opportunity coverage vs target.
    coverage = min(20.0, 20.0 * open_count / max(target_open_count, 1))

    # 25 points: weighted pipeline vs target.
    weighted_pipeline = min(25.0, 25.0 * weighted_total / max(target_weighted_pipeline, 1.0))

    # 20 points: stale hygiene (high stale ratio collapses score).
    stale_ratio = (len(stale_opps) / open_count) if open_count else 1.0
    stale_hygiene = max(0.0, 20.0 * (1.0 - stale_ratio / 0.5))

    # 15 points: action hygiene (next action discipline).
    action_coverage = (with_action_count / open_count) if open_count else 0.0
    due_ratio = (due_7d_count / open_count) if open_count else 0.0
    action_hygiene = min(15.0, 10.0 * action_coverage + 5.0 * min(1.0, due_ratio / 0.6))

    # 20 points: expected close horizon (next 60 days).
    close_horizon = min(20.0, 20.0 * expected_60d / max(target_expected_60d, 1.0))

    return ScoreBreakdown(
        coverage=coverage,
        weighted_pipeline=weighted_pipeline,
        stale_hygiene=stale_hygiene,
        action_hygiene=action_hygiene,
        close_horizon=close_horizon,
    )


def score_band(score: float) -> str:
    if score >= 85.0:
        return "Green"
    if score >= 70.0:
        return "Yellow"
    return "Red"


def risk_flags(
    open_count: int,
    stale_count: int,
    due_7d_count: int,
    weighted_total: float,
    expected_30d: float,
    target_weighted_pipeline: float,
) -> list[str]:
    flags: list[str] = []
    stale_ratio = (stale_count / open_count) if open_count else 1.0
    if open_count == 0:
        flags.append("No open opportunities in pipeline.")
    if stale_ratio > 0.30:
        flags.append(f"High stale opportunity ratio ({stale_ratio:.0%}).")
    if due_7d_count == 0 and open_count > 0:
        flags.append("No next-action dates due in the next 7 days.")
    if weighted_total < target_weighted_pipeline * 0.6:
        flags.append("Weighted pipeline is below 60% of target.")
    if expected_30d <= 0.0 and open_count > 0:
        flags.append("No expected weighted closes in the next 30 days.")
    return flags


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def render_report(
    as_of: date,
    all_opps: list[Opportunity],
    open_opps: list[Opportunity],
    stale_opps: list[Opportunity],
    due_7d_opps: list[Opportunity],
    expected_30d: float,
    expected_60d: float,
    weighted_total: float,
    score: ScoreBreakdown,
    target_open_count: int,
    target_weighted_pipeline: float,
    target_expected_60d: float,
    stale_days: int,
    top_n: int,
) -> str:
    stage_counts = count_stage(open_opps)
    stage_weighted = weighted_by_stage(open_opps)

    top_opps = sorted(open_opps, key=lambda opp: opp.weighted_value, reverse=True)[:top_n]
    stale_top = sorted(
        stale_opps,
        key=lambda opp: opp.last_touch_date.toordinal() if opp.last_touch_date else -1,
    )[:top_n]

    with_action_count = sum(1 for opp in open_opps if opp.next_action_date is not None)
    stale_count = len(stale_opps)
    due_7d_count = len(due_7d_opps)
    score_total = score.total
    flags = risk_flags(
        open_count=len(open_opps),
        stale_count=stale_count,
        due_7d_count=due_7d_count,
        weighted_total=weighted_total,
        expected_30d=expected_30d,
        target_weighted_pipeline=target_weighted_pipeline,
    )

    lines: list[str] = []
    lines.append("# Pipeline Health Report")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- As of: {as_of.isoformat()}")
    lines.append(f"- Total opportunities: {len(all_opps)}")
    lines.append(f"- Open opportunities: {len(open_opps)} (target: {target_open_count})")
    lines.append(f"- Weighted open pipeline: {format_currency(weighted_total)} (target: {format_currency(target_weighted_pipeline)})")
    lines.append(f"- Expected weighted closes (30d): {format_currency(expected_30d)}")
    lines.append(f"- Expected weighted closes (60d): {format_currency(expected_60d)} (target: {format_currency(target_expected_60d)})")
    lines.append("")
    lines.append("## Health Score")
    lines.append("")
    lines.append(f"- Total score: {score_total:.1f} / 100 ({score_band(score_total)})")
    lines.append(f"- Coverage: {score.coverage:.1f} / 20")
    lines.append(f"- Weighted pipeline: {score.weighted_pipeline:.1f} / 25")
    lines.append(f"- Stale hygiene: {score.stale_hygiene:.1f} / 20")
    lines.append(f"- Action hygiene: {score.action_hygiene:.1f} / 15")
    lines.append(f"- Close horizon: {score.close_horizon:.1f} / 20")
    lines.append("")
    lines.append("## Stage Distribution (Open Only)")
    lines.append("")
    lines.append("| Stage | Count | Weighted USD |")
    lines.append("|---|---:|---:|")
    for stage in sorted(stage_counts.keys()):
        count = stage_counts.get(stage, 0)
        weighted = stage_weighted.get(stage, 0.0)
        lines.append(f"| {stage} | {count} | {format_currency(weighted)} |")
    lines.append("")
    lines.append("## Execution Hygiene")
    lines.append("")
    lines.append(f"- Opportunities with `next_action_date`: {with_action_count}/{len(open_opps)}")
    lines.append(f"- Next 7-day actions due: {due_7d_count}")
    lines.append(f"- Stale opportunities (>{stale_days} days since last touch): {stale_count}")
    lines.append("")
    lines.append("## Top Opportunities By Weighted Value")
    lines.append("")
    if top_opps:
        lines.append("| Account | Stage | ACV USD | Prob % | Weighted USD | Expected Close | Owner |")
        lines.append("|---|---|---:|---:|---:|---|---|")
        for opp in top_opps:
            ecd = opp.expected_close_date.isoformat() if opp.expected_close_date else ""
            lines.append(
                f"| {opp.account_name} | {opp.stage} | {format_currency(opp.acv_usd)} | "
                f"{opp.probability_pct:.1f}% | {format_currency(opp.weighted_value)} | {ecd} | {opp.owner} |"
            )
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Stale Opportunities")
    lines.append("")
    if stale_top:
        lines.append("| Account | Stage | Last Touch | Next Action | Owner |")
        lines.append("|---|---|---|---|---|")
        for opp in stale_top:
            ltd = opp.last_touch_date.isoformat() if opp.last_touch_date else ""
            lines.append(f"| {opp.account_name} | {opp.stage} | {ltd} | {opp.next_action} | {opp.owner} |")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Risk Flags")
    lines.append("")
    if flags:
        for flag in flags:
            lines.append(f"- {flag}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Next Recommendations")
    lines.append("")
    if len(open_opps) < target_open_count:
        lines.append(f"- Add {target_open_count - len(open_opps)} net-new open opportunities to hit coverage target.")
    if stale_count > 0:
        lines.append("- Run stale-opportunity cleanup and update next-action dates for all stale rows.")
    if due_7d_count == 0 and open_opps:
        lines.append("- Schedule at least one concrete next action in the next 7 days for every open opportunity.")
    if expected_60d < target_expected_60d:
        gap = target_expected_60d - expected_60d
        lines.append(f"- Increase near-term expected close pipeline by {format_currency(gap)}.")
    if not flags:
        lines.append("- Maintain cadence and continue weekly pipeline hygiene checks.")

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", required=True, type=Path, help="Path to pipeline CSV file.")
    parser.add_argument("--out", required=True, type=Path, help="Output markdown file path.")
    parser.add_argument("--as-of", default=None, help="Snapshot date in YYYY-MM-DD format (default: today).")
    parser.add_argument("--stale-days", default=14, type=int, help="Days since last touch before opportunity is stale.")
    parser.add_argument("--target-open-count", default=15, type=int, help="Target minimum count of open opportunities.")
    parser.add_argument(
        "--target-weighted-pipeline",
        default=300000.0,
        type=float,
        help="Target weighted open pipeline (USD).",
    )
    parser.add_argument(
        "--target-expected-60d",
        default=120000.0,
        type=float,
        help="Target expected weighted close amount over next 60 days (USD).",
    )
    parser.add_argument("--top-n", default=5, type=int, help="Number of top/stale opportunities to list.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    as_of = parse_as_of(args.as_of)
    opps = read_pipeline(args.pipeline)

    open_opps = [opp for opp in opps if opp.status == "open"]
    stale_cutoff = as_of - timedelta(days=max(0, args.stale_days))
    stale_opps = [opp for opp in open_opps if opp.last_touch_date is None or opp.last_touch_date < stale_cutoff]

    due_start = as_of
    due_end = as_of + timedelta(days=7)
    due_7d_opps = [
        opp for opp in open_opps if opp.next_action_date is not None and due_start <= opp.next_action_date <= due_end
    ]

    close_30d = as_of + timedelta(days=30)
    close_60d = as_of + timedelta(days=60)
    expected_30d = sum(
        opp.weighted_value
        for opp in open_opps
        if opp.expected_close_date is not None and as_of <= opp.expected_close_date <= close_30d
    )
    expected_60d = sum(
        opp.weighted_value
        for opp in open_opps
        if opp.expected_close_date is not None and as_of <= opp.expected_close_date <= close_60d
    )

    weighted_total = sum(opp.weighted_value for opp in open_opps)
    with_action_count = sum(1 for opp in open_opps if opp.next_action_date is not None)

    score = score_pipeline(
        open_opps=open_opps,
        stale_opps=stale_opps,
        due_7d_count=len(due_7d_opps),
        with_action_count=with_action_count,
        weighted_total=weighted_total,
        expected_60d=expected_60d,
        target_open_count=max(1, args.target_open_count),
        target_weighted_pipeline=max(1.0, args.target_weighted_pipeline),
        target_expected_60d=max(1.0, args.target_expected_60d),
    )

    report = render_report(
        as_of=as_of,
        all_opps=opps,
        open_opps=open_opps,
        stale_opps=stale_opps,
        due_7d_opps=due_7d_opps,
        expected_30d=expected_30d,
        expected_60d=expected_60d,
        weighted_total=weighted_total,
        score=score,
        target_open_count=max(1, args.target_open_count),
        target_weighted_pipeline=max(1.0, args.target_weighted_pipeline),
        target_expected_60d=max(1.0, args.target_expected_60d),
        stale_days=max(0, args.stale_days),
        top_n=max(1, args.top_n),
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"wrote pipeline health report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
