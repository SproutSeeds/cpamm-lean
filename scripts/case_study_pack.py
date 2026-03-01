#!/usr/bin/env python3
"""Generate a sanitized case-study package from structured JSON input."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CaseStudyError(Exception):
    pass


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return slug or "case-study"


def parse_date(value: str) -> bool:
    parts = value.split("-")
    if len(parts) != 3:
        return False
    try:
        year, month, day = (int(parts[0]), int(parts[1]), int(parts[2]))
        datetime(year, month, day, tzinfo=timezone.utc)
        return True
    except Exception:
        return False


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CaseStudyError(f"missing input file: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CaseStudyError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise CaseStudyError("case-study input root must be a JSON object")
    return raw


def get_required_str(data: dict[str, Any], key: str) -> str:
    value = str(data.get(key, "")).strip()
    if not value:
        raise CaseStudyError(f"missing required field: {key}")
    return value


def get_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise CaseStudyError(f"expected list for field: {key}")
    return value


def get_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise CaseStudyError(f"expected object for field: {key}")
    return value


def markdown_bullets(items: list[Any], empty: str = "None provided") -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in cleaned)


def format_number(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}"
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    if as_float.is_integer():
        return str(int(as_float))
    return f"{as_float:.2f}"


def metric_delta(before: Any, after: Any, higher_is_better: bool) -> str:
    try:
        b = float(before)
        a = float(after)
    except (TypeError, ValueError):
        return "n/a"
    diff = a - b
    if abs(diff) < 1e-9:
        return "0"
    sign = "+" if diff > 0 else ""
    delta = f"{sign}{diff:.2f}"
    if delta.endswith(".00"):
        delta = delta[:-3]
    outcome = "improved" if (diff > 0 and higher_is_better) or (diff < 0 and not higher_is_better) else "regressed"
    return f"{delta} ({outcome})"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to case-study input JSON.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: strategy/private/case-studies/<case_study_id>).",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=None,
        help="Output root directory for case-study-id subfolders (e.g., artifacts/case-studies).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.out_dir is not None and args.out_root is not None:
        raise CaseStudyError("pass only one of --out-dir or --out-root")

    data = load_json(args.input)

    case_study_id = get_required_str(data, "case_study_id")
    if slugify(case_study_id) != case_study_id:
        raise CaseStudyError(
            f"case_study_id must be slug-like (letters/numbers/._-), got {case_study_id!r}"
        )
    published_date = get_required_str(data, "published_date")
    if not parse_date(published_date):
        raise CaseStudyError(f"published_date must be YYYY-MM-DD, got {published_date!r}")

    title = get_required_str(data, "title")
    client_alias = get_required_str(data, "client_alias")
    client_segment = get_required_str(data, "client_segment")
    engagement_type = get_required_str(data, "engagement_type")
    engagement_window = get_dict(data, "engagement_window")
    start = str(engagement_window.get("start", "")).strip()
    end = str(engagement_window.get("end", "")).strip()
    if start and not parse_date(start):
        raise CaseStudyError(f"engagement_window.start must be YYYY-MM-DD, got {start!r}")
    if end and not parse_date(end):
        raise CaseStudyError(f"engagement_window.end must be YYYY-MM-DD, got {end!r}")

    scope_summary = get_list(data, "scope_summary")
    baseline_risks = get_list(data, "baseline_risks")
    interventions = get_list(data, "interventions")
    outcomes = get_list(data, "outcomes")
    artifacts_referenced = get_list(data, "artifacts_referenced")
    anonymization_notes = get_list(data, "anonymization_notes")
    tags = get_list(data, "tags")

    metrics = get_dict(data, "metrics")
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
    missing_metrics = [key for key in required_metrics if key not in metrics]
    if missing_metrics:
        raise CaseStudyError(f"metrics missing required fields: {', '.join(missing_metrics)}")

    quote = get_dict(data, "quote")
    quote_text = str(quote.get("text", "")).strip()
    quote_role = str(quote.get("speaker_role", "")).strip()
    quote_block = '- (not provided)'
    if quote_text:
        quote_block = f'> "{quote_text}"\n>\n> - {quote_role}'

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.out_dir is not None:
        out_dir = args.out_dir
    elif args.out_root is not None:
        out_dir = args.out_root / case_study_id
    else:
        out_dir = Path("strategy/private/case-studies") / case_study_id
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics_table = "\n".join(
        [
            "| Metric | Before | After | Delta |",
            "|---|---:|---:|---:|",
            "| CI gate pass rate (%) | "
            f"{format_number(metrics['ci_gate_pass_rate_before_pct'])} | "
            f"{format_number(metrics['ci_gate_pass_rate_after_pct'])} | "
            f"{metric_delta(metrics['ci_gate_pass_rate_before_pct'], metrics['ci_gate_pass_rate_after_pct'], True)} |",
            "| Time-to-green (days) | "
            f"{format_number(metrics['time_to_green_before_days'])} | "
            f"{format_number(metrics['time_to_green_after_days'])} | "
            f"{metric_delta(metrics['time_to_green_before_days'], metrics['time_to_green_after_days'], False)} |",
            "| Regression escapes | "
            f"{format_number(metrics['regression_escapes_before'])} | "
            f"{format_number(metrics['regression_escapes_after'])} | "
            f"{metric_delta(metrics['regression_escapes_before'], metrics['regression_escapes_after'], False)} |",
        ]
    )

    case_study_text = f"""# {title}

## Snapshot

- Case Study ID: {case_study_id}
- Published: {published_date}
- Client Alias: {client_alias}
- Client Segment: {client_segment}
- Engagement Type: {engagement_type}
- Engagement Window: {start} to {end}
- Generated At (UTC): {generated_at}

## Scope Summary

{markdown_bullets(scope_summary)}

## Baseline Risks

{markdown_bullets(baseline_risks)}

## Interventions

{markdown_bullets(interventions)}

## Measurable Outcomes

- Critical findings prevented pre-launch: {format_number(metrics['critical_findings_prevented'])}
- Proof obligations closed: {format_number(metrics['proof_obligations_closed'])}

{metrics_table}

## Narrative Outcomes

{markdown_bullets(outcomes)}

## Evidence References

{markdown_bullets(artifacts_referenced)}

## Anonymization Notes

{markdown_bullets(anonymization_notes)}

## Client Quote

{quote_block}

## Tags

{markdown_bullets(tags, empty="None")}
"""

    summary_json = {
        "case_study_id": case_study_id,
        "published_date": published_date,
        "title": title,
        "client_alias": client_alias,
        "client_segment": client_segment,
        "engagement_type": engagement_type,
        "generated_at_utc": generated_at,
        "key_metrics": {
            "critical_findings_prevented": metrics["critical_findings_prevented"],
            "proof_obligations_closed": metrics["proof_obligations_closed"],
            "ci_gate_pass_rate_before_pct": metrics["ci_gate_pass_rate_before_pct"],
            "ci_gate_pass_rate_after_pct": metrics["ci_gate_pass_rate_after_pct"],
            "time_to_green_before_days": metrics["time_to_green_before_days"],
            "time_to_green_after_days": metrics["time_to_green_after_days"],
            "regression_escapes_before": metrics["regression_escapes_before"],
            "regression_escapes_after": metrics["regression_escapes_after"],
        },
    }

    manifest = {
        "generated_at_utc": generated_at,
        "case_study_id": case_study_id,
        "input_file": str(args.input),
        "output_dir": str(out_dir),
        "files": ["CASE_STUDY.md", "CASE_STUDY_SUMMARY.json", "MANIFEST.json"],
    }

    (out_dir / "CASE_STUDY.md").write_text(case_study_text, encoding="utf-8")
    (out_dir / "CASE_STUDY_SUMMARY.json").write_text(json.dumps(summary_json, indent=2) + "\n", encoding="utf-8")
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"generated case study pack: {out_dir}")
    print(f"- {out_dir / 'CASE_STUDY.md'}")
    print(f"- {out_dir / 'CASE_STUDY_SUMMARY.json'}")
    print(f"- {out_dir / 'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CaseStudyError as err:
        print(f"case-study error: {err}")
        raise SystemExit(1)
