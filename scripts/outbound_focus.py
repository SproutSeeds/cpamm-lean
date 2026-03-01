#!/usr/bin/env python3
"""Generate a prioritized outbound action plan from CRM pipeline data."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


STAGE_WEIGHTS: dict[str, float] = {
    "lead": 6.0,
    "discovery": 12.0,
    "proposal": 20.0,
    "negotiation": 28.0,
}


@dataclass
class Opportunity:
    account_name: str
    segment: str
    contact_name: str
    contact_role: str
    status: str
    stage: str
    acv_usd: float
    probability_pct: float
    expected_close_date: date | None
    owner: str
    next_action: str
    next_action_date: date | None
    last_touch_date: date | None
    notes: str

    @property
    def weighted_value(self) -> float:
        return self.acv_usd * self.probability_pct / 100.0


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
                segment=row.get("segment", "").strip().lower(),
                contact_name=row.get("contact_name", "").strip(),
                contact_role=row.get("contact_role", "").strip(),
                status=row.get("status", "").strip().lower(),
                stage=row.get("stage", "").strip().lower(),
                acv_usd=parse_float(row.get("acv_usd", "0")),
                probability_pct=parse_float(row.get("probability_pct", "0")),
                expected_close_date=parse_date(row.get("expected_close_date", "")),
                owner=row.get("owner", "").strip(),
                next_action=row.get("next_action", "").strip(),
                next_action_date=parse_date(row.get("next_action_date", "")),
                last_touch_date=parse_date(row.get("last_touch_date", "")),
                notes=row.get("notes", "").strip(),
            )
        )
    return out


def template_hint(opp: Opportunity) -> str:
    if opp.segment in {"fund", "accelerator"}:
        return "Template 3 (Fund/Accelerator)"
    role = opp.contact_role.lower()
    if "security" in role or opp.stage in {"proposal", "negotiation"}:
        return "Template 2 (Security Follow-Up)"
    return "Template 1 (Founder/CTO)"


def priority_score(
    opp: Opportunity,
    as_of: date,
    due_window_days: int,
    stale_days: int,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    stage_weight = STAGE_WEIGHTS.get(opp.stage, 0.0)
    if stage_weight > 0.0:
        score += stage_weight
        reasons.append(f"{opp.stage} stage")

    probability_boost = min(40.0, max(0.0, opp.probability_pct) * 0.4)
    if probability_boost > 0.0:
        score += probability_boost
        reasons.append(f"{opp.probability_pct:.0f}% probability")

    if opp.next_action_date is None:
        score -= 10.0
        reasons.append("missing next action date")
    else:
        delta_days = (opp.next_action_date - as_of).days
        if delta_days < 0:
            overdue_days = -delta_days
            boost = 35.0 + min(14.0, float(overdue_days))
            score += boost
            reasons.append(f"overdue {overdue_days}d")
        elif delta_days == 0:
            score += 30.0
            reasons.append("due today")
        elif delta_days <= due_window_days:
            boost = max(5.0, 20.0 - float(delta_days))
            score += boost
            reasons.append(f"due in {delta_days}d")

    if opp.last_touch_date is None:
        score += 5.0
        reasons.append("no last touch date")
    else:
        since_touch = (as_of - opp.last_touch_date).days
        if since_touch > stale_days:
            stale_over = since_touch - stale_days
            boost = min(30.0, float(stale_over))
            score += boost
            reasons.append(f"stale {since_touch}d")

    weighted_boost = min(20.0, opp.weighted_value / 10000.0)
    if weighted_boost > 0.0:
        score += weighted_boost

    if opp.status == "nurture":
        score -= 20.0
        reasons.append("nurture status")
    elif opp.status == "open":
        score += 5.0

    return score, reasons


def render_report(
    as_of: date,
    all_candidates: list[Opportunity],
    ranked: list[tuple[Opportunity, float, list[str]]],
    stale_days: int,
    due_window_days: int,
) -> str:
    stale_cutoff = as_of - timedelta(days=stale_days)
    due_cutoff = as_of + timedelta(days=due_window_days)

    overdue = sum(1 for opp in all_candidates if opp.next_action_date is not None and opp.next_action_date < as_of)
    due_today = sum(1 for opp in all_candidates if opp.next_action_date == as_of)
    due_7d = sum(
        1
        for opp in all_candidates
        if opp.next_action_date is not None and as_of < opp.next_action_date <= due_cutoff
    )
    stale = sum(
        1
        for opp in all_candidates
        if opp.last_touch_date is not None and opp.last_touch_date < stale_cutoff
    )
    no_action = sum(1 for opp in all_candidates if not opp.next_action.strip())

    lines: list[str] = []
    lines.append("# Outbound Focus Plan")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- As of: {as_of.isoformat()}")
    lines.append(f"- Candidate opportunities (`open` + `nurture`): {len(all_candidates)}")
    lines.append(f"- Overdue next actions: {overdue}")
    lines.append(f"- Due today: {due_today}")
    lines.append(f"- Due in next {due_window_days} days: {due_7d}")
    lines.append(f"- Stale opportunities (> {stale_days} days since touch): {stale}")
    lines.append(f"- Missing `next_action` text: {no_action}")
    lines.append("")
    lines.append("## Priority Queue")
    lines.append("")
    lines.append(
        "| Rank | Account | Owner | Status | Stage | Next Action | Next Action Date | Last Touch | Weighted USD | Priority | Template | Why now |"
    )
    lines.append("|---:|---|---|---|---|---|---|---|---:|---:|---|---|")
    for idx, (opp, score, reasons) in enumerate(ranked, start=1):
        next_action_date = opp.next_action_date.isoformat() if opp.next_action_date else ""
        last_touch = opp.last_touch_date.isoformat() if opp.last_touch_date else ""
        weighted = f"${opp.weighted_value:,.2f}"
        reason_text = ", ".join(reasons[:3])
        lines.append(
            "| "
            f"{idx} | {opp.account_name} | {opp.owner} | {opp.status} | {opp.stage} | "
            f"{opp.next_action or '-'} | {next_action_date} | {last_touch} | {weighted} | "
            f"{score:.1f} | {template_hint(opp)} | {reason_text} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Use `strategy/assets/sales/OUTBOUND_TEMPLATES.md` for message drafts.")
    lines.append("- Use `strategy/assets/sales/FOLLOW_UP_SEQUENCE.md` for day-2/day-5/day-8 cadence.")
    return "\n".join(lines) + "\n"


def write_csv(path: Path, ranked: list[tuple[Opportunity, float, list[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "rank",
                "account_name",
                "owner",
                "status",
                "stage",
                "next_action",
                "next_action_date",
                "last_touch_date",
                "weighted_usd",
                "priority_score",
                "template_hint",
                "reasons",
            ]
        )
        for idx, (opp, score, reasons) in enumerate(ranked, start=1):
            writer.writerow(
                [
                    idx,
                    opp.account_name,
                    opp.owner,
                    opp.status,
                    opp.stage,
                    opp.next_action,
                    opp.next_action_date.isoformat() if opp.next_action_date else "",
                    opp.last_touch_date.isoformat() if opp.last_touch_date else "",
                    f"{opp.weighted_value:.2f}",
                    f"{score:.2f}",
                    template_hint(opp),
                    "; ".join(reasons),
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", required=True, type=Path, help="Path to pipeline CSV.")
    parser.add_argument(
        "--as-of",
        default=None,
        help="Snapshot date in YYYY-MM-DD (default: today UTC).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/OUTBOUND_FOCUS.md"),
        help="Markdown output path (default: reports/OUTBOUND_FOCUS.md).",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Optional CSV output path for ranked actions.",
    )
    parser.add_argument(
        "--max-actions",
        type=int,
        default=15,
        help="Maximum prioritized actions to include (default: 15).",
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    as_of = parse_as_of(args.as_of)
    max_actions = max(1, args.max_actions)

    opportunities = read_pipeline(args.pipeline)
    candidates = [
        opp
        for opp in opportunities
        if opp.status in {"open", "nurture"} and opp.stage != "closed"
    ]
    scored = [
        (opp, *priority_score(opp, as_of=as_of, due_window_days=args.due_window_days, stale_days=args.stale_days))
        for opp in candidates
    ]
    ranked = sorted(
        scored,
        key=lambda item: (
            -item[1],
            item[0].next_action_date or date.max,
            -item[0].weighted_value,
            item[0].account_name.lower(),
        ),
    )[:max_actions]

    report = render_report(
        as_of=as_of,
        all_candidates=candidates,
        ranked=ranked,
        stale_days=args.stale_days,
        due_window_days=args.due_window_days,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"wrote outbound focus report: {args.out}")

    csv_out = args.csv_out
    if csv_out is not None:
        write_csv(csv_out, ranked)
        print(f"wrote outbound focus csv: {csv_out}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f"error: {err}")
        raise SystemExit(1)
