#!/usr/bin/env python3
"""Generate a portfolio-level index and rollup from case-study inputs."""

from __future__ import annotations

import argparse
import glob
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import case_study_pack


class CaseStudyIndexError(Exception):
    pass


@dataclass
class CaseStudyEntry:
    case_study_id: str
    title: str
    published_date: str
    client_alias: str
    client_segment: str
    engagement_type: str
    critical_findings_prevented: float
    proof_obligations_closed: float
    ci_before_pct: float
    ci_after_pct: float
    time_to_green_before_days: float
    time_to_green_after_days: float
    regression_escapes_before: float
    regression_escapes_after: float
    source_file: str

    @property
    def ci_delta_pct_points(self) -> float:
        return self.ci_after_pct - self.ci_before_pct

    @property
    def time_to_green_delta_days(self) -> float:
        return self.time_to_green_after_days - self.time_to_green_before_days

    @property
    def regression_escape_delta(self) -> float:
        return self.regression_escapes_after - self.regression_escapes_before


def parse_number(value: Any, key: str, path: Path) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise CaseStudyIndexError(f"{path}: {key} must be numeric, got {value!r}") from exc


def load_case_study(path: Path) -> CaseStudyEntry:
    data = case_study_pack.load_json(path)
    case_study_id = case_study_pack.get_required_str(data, "case_study_id")
    if case_study_pack.slugify(case_study_id) != case_study_id:
        raise CaseStudyIndexError(
            f"{path}: case_study_id must be slug-like (letters/numbers/._-), got {case_study_id!r}"
        )
    published_date = case_study_pack.get_required_str(data, "published_date")
    if not case_study_pack.parse_date(published_date):
        raise CaseStudyIndexError(f"{path}: published_date must be YYYY-MM-DD, got {published_date!r}")

    metrics = case_study_pack.get_dict(data, "metrics")
    required_metrics = [
        "critical_findings_prevented",
        "proof_obligations_closed",
        "ci_gate_pass_rate_before_pct",
        "ci_gate_pass_rate_after_pct",
        "time_to_green_before_days",
        "time_to_green_after_days",
        "regression_escapes_before",
        "regression_escapes_after",
    ]
    missing = [key for key in required_metrics if key not in metrics]
    if missing:
        raise CaseStudyIndexError(f"{path}: metrics missing required fields: {', '.join(missing)}")

    return CaseStudyEntry(
        case_study_id=case_study_id,
        title=case_study_pack.get_required_str(data, "title"),
        published_date=published_date,
        client_alias=case_study_pack.get_required_str(data, "client_alias"),
        client_segment=case_study_pack.get_required_str(data, "client_segment"),
        engagement_type=case_study_pack.get_required_str(data, "engagement_type"),
        critical_findings_prevented=parse_number(metrics["critical_findings_prevented"], "metrics.critical_findings_prevented", path),
        proof_obligations_closed=parse_number(metrics["proof_obligations_closed"], "metrics.proof_obligations_closed", path),
        ci_before_pct=parse_number(metrics["ci_gate_pass_rate_before_pct"], "metrics.ci_gate_pass_rate_before_pct", path),
        ci_after_pct=parse_number(metrics["ci_gate_pass_rate_after_pct"], "metrics.ci_gate_pass_rate_after_pct", path),
        time_to_green_before_days=parse_number(metrics["time_to_green_before_days"], "metrics.time_to_green_before_days", path),
        time_to_green_after_days=parse_number(metrics["time_to_green_after_days"], "metrics.time_to_green_after_days", path),
        regression_escapes_before=parse_number(metrics["regression_escapes_before"], "metrics.regression_escapes_before", path),
        regression_escapes_after=parse_number(metrics["regression_escapes_after"], "metrics.regression_escapes_after", path),
        source_file=str(path),
    )


def format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}"


def format_delta(value: float) -> str:
    if abs(value) < 1e-9:
        return "0"
    sign = "+" if value > 0 else ""
    out = f"{sign}{value:.2f}"
    if out.endswith(".00"):
        out = out[:-3]
    return out


def resolve_inputs(inputs: list[str], input_globs: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()

    for raw in inputs:
        p = Path(raw)
        key = str(p)
        if key not in seen:
            files.append(p)
            seen.add(key)

    for pattern in input_globs:
        matched = sorted(glob.glob(pattern))
        for m in matched:
            p = Path(m)
            key = str(p)
            if key not in seen:
                files.append(p)
                seen.add(key)

    if not files:
        raise CaseStudyIndexError("provide at least one case-study input via --inputs or --input-glob")
    return files


def build_rollup(entries: list[CaseStudyEntry]) -> dict[str, Any]:
    by_segment: dict[str, int] = {}
    for entry in entries:
        by_segment[entry.client_segment] = by_segment.get(entry.client_segment, 0) + 1

    count = len(entries)
    total_findings = sum(e.critical_findings_prevented for e in entries)
    total_proofs = sum(e.proof_obligations_closed for e in entries)
    total_regression_reduction = sum(e.regression_escapes_before - e.regression_escapes_after for e in entries)
    avg_ci_delta = sum(e.ci_delta_pct_points for e in entries) / max(1, count)
    avg_time_to_green_reduction = sum(
        e.time_to_green_before_days - e.time_to_green_after_days for e in entries
    ) / max(1, count)
    dates = sorted(e.published_date for e in entries)

    return {
        "case_study_count": count,
        "published_window": {
            "start": dates[0] if dates else "",
            "end": dates[-1] if dates else "",
        },
        "totals": {
            "critical_findings_prevented": total_findings,
            "proof_obligations_closed": total_proofs,
            "regression_escape_reduction": total_regression_reduction,
        },
        "averages": {
            "ci_gate_improvement_pct_points": avg_ci_delta,
            "time_to_green_reduction_days": avg_time_to_green_reduction,
        },
        "by_segment": by_segment,
    }


def render_markdown(entries: list[CaseStudyEntry], rollup: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Case Studies Index")
    lines.append("")
    lines.append("## Rollup")
    lines.append("")
    lines.append(f"- Case studies: {rollup['case_study_count']}")
    lines.append(
        "- Published window: "
        f"{rollup['published_window']['start']} to {rollup['published_window']['end']}"
    )
    lines.append(
        "- Total critical findings prevented: "
        f"{format_number(float(rollup['totals']['critical_findings_prevented']))}"
    )
    lines.append(
        "- Total proof obligations closed: "
        f"{format_number(float(rollup['totals']['proof_obligations_closed']))}"
    )
    lines.append(
        "- Total regression escapes reduced: "
        f"{format_number(float(rollup['totals']['regression_escape_reduction']))}"
    )
    lines.append(
        "- Average CI gate improvement (pct points): "
        f"{format_delta(float(rollup['averages']['ci_gate_improvement_pct_points']))}"
    )
    lines.append(
        "- Average time-to-green reduction (days): "
        f"{format_delta(float(rollup['averages']['time_to_green_reduction_days']))}"
    )
    lines.append("")
    lines.append("## Segment Mix")
    lines.append("")
    lines.append("| Segment | Count |")
    lines.append("|---|---:|")
    for segment, count in sorted(rollup["by_segment"].items()):
        lines.append(f"| {segment} | {count} |")
    lines.append("")
    lines.append("## Case Studies")
    lines.append("")
    lines.append(
        "| Case Study ID | Published | Segment | Engagement | Critical Findings Prevented | "
        "Proof Obligations Closed | CI Gate Delta (pp) | Time-to-Green Delta (days) | "
        "Regression Escapes Delta |"
    )
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|")
    for entry in sorted(entries, key=lambda e: (e.published_date, e.case_study_id), reverse=True):
        lines.append(
            "| "
            f"{entry.case_study_id} | {entry.published_date} | {entry.client_segment} | "
            f"{entry.engagement_type} | {format_number(entry.critical_findings_prevented)} | "
            f"{format_number(entry.proof_obligations_closed)} | {format_delta(entry.ci_delta_pct_points)} | "
            f"{format_delta(entry.time_to_green_delta_days)} | {format_delta(entry.regression_escape_delta)} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inputs",
        nargs="*",
        default=[],
        help="Explicit case-study input JSON paths.",
    )
    parser.add_argument(
        "--input-glob",
        action="append",
        default=[],
        help="Glob pattern for case-study inputs (repeatable).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/CASE_STUDIES_INDEX.md"),
        help="Markdown index output path.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("reports/CASE_STUDIES_ROLLUP.json"),
        help="Rollup JSON output path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_paths = resolve_inputs(args.inputs, args.input_glob)
    entries = [load_case_study(path) for path in input_paths]

    rollup = build_rollup(entries)
    markdown = render_markdown(entries, rollup)
    index_payload = {
        "generated_from": [entry.source_file for entry in entries],
        "rollup": rollup,
        "entries": [
            {
                "case_study_id": e.case_study_id,
                "title": e.title,
                "published_date": e.published_date,
                "client_alias": e.client_alias,
                "client_segment": e.client_segment,
                "engagement_type": e.engagement_type,
                "critical_findings_prevented": e.critical_findings_prevented,
                "proof_obligations_closed": e.proof_obligations_closed,
                "ci_delta_pct_points": e.ci_delta_pct_points,
                "time_to_green_delta_days": e.time_to_green_delta_days,
                "regression_escape_delta": e.regression_escape_delta,
                "source_file": e.source_file,
            }
            for e in entries
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown, encoding="utf-8")
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(index_payload, indent=2) + "\n", encoding="utf-8")

    print(f"wrote case-study index markdown: {args.out}")
    print(f"wrote case-study rollup json: {args.json_out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CaseStudyIndexError as err:
        print(f"case-study-index error: {err}")
        raise SystemExit(1)
