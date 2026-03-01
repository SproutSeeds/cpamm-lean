#!/usr/bin/env python3
"""Validate commercialization operating data files (pipeline, KPI, deal input, portal input)."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path

import case_study_pack
import deal_pack

PIPELINE_REQUIRED_COLUMNS = [
    "account_name",
    "segment",
    "contact_name",
    "contact_role",
    "contact_email",
    "status",
    "stage",
    "deal_type",
    "acv_usd",
    "probability_pct",
    "expected_close_date",
    "owner",
    "next_action",
    "next_action_date",
    "last_touch_date",
    "notes",
]

PIPELINE_SEGMENTS = {"protocol", "fund", "accelerator", "auditor", "other"}
PIPELINE_STATUSES = {"open", "won", "lost", "nurture"}
PIPELINE_STAGES = {"lead", "discovery", "proposal", "negotiation", "closed"}
PIPELINE_DEAL_TYPES = {"sprint", "retainer", "subscription", "partner"}

KPI_REQUIRED_COLUMNS = [
    "week_start",
    "verified_releases",
    "paid_customers",
    "mrr_usd",
    "time_to_green_days",
    "discovery_calls",
    "proposal_win_rate_pct",
    "sprint_to_retainer_pct",
    "nrr_pct",
    "critical_issues_found",
    "regression_escapes",
    "ci_gate_pass_rate_pct",
    "evidence_pkg_success_pct",
    "automation_pct",
    "support_tickets_per_customer",
    "mttr_hours",
    "notes",
]

KPI_PERCENT_FIELDS = {
    "proposal_win_rate_pct",
    "sprint_to_retainer_pct",
    "ci_gate_pass_rate_pct",
    "evidence_pkg_success_pct",
    "automation_pct",
}

KPI_NON_NEGATIVE_FIELDS = {
    "verified_releases",
    "paid_customers",
    "mrr_usd",
    "time_to_green_days",
    "discovery_calls",
    "critical_issues_found",
    "regression_escapes",
    "support_tickets_per_customer",
    "mttr_hours",
    "nrr_pct",
}

PORTAL_REQUIRED_FIELDS = [
    "engagement_id",
    "client_name",
    "protocol_name",
    "engagement_type",
    "status",
    "owner",
]

CASE_STUDY_REQUIRED_FIELDS = [
    "case_study_id",
    "published_date",
    "title",
    "client_alias",
    "client_segment",
    "engagement_type",
]


class ValidationError(Exception):
    pass


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        year, month, day = value.split("-")
        return date(int(year), int(month), int(day))
    except Exception:
        return None


def parse_number(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"expected numeric value, got {value!r}") from exc


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise ValidationError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def ensure_required_columns(headers: list[str], required: list[str], file_name: str) -> None:
    missing = sorted(set(required) - set(headers))
    if missing:
        raise ValidationError(f"{file_name} missing required columns: {', '.join(missing)}")


def require_non_empty(row: dict[str, str], key: str, row_num: int, file_name: str) -> None:
    value = row.get(key, "").strip()
    if not value:
        raise ValidationError(f"{file_name} row {row_num}: '{key}' is required")


def check_enum(row: dict[str, str], key: str, options: set[str], row_num: int, file_name: str) -> str:
    value = row.get(key, "").strip().lower()
    if value not in options:
        allowed = ", ".join(sorted(options))
        raise ValidationError(f"{file_name} row {row_num}: '{key}' must be one of [{allowed}], got {value!r}")
    return value


def check_date_field(row: dict[str, str], key: str, row_num: int, file_name: str, required: bool) -> date | None:
    raw = row.get(key, "").strip()
    if not raw:
        if required:
            raise ValidationError(f"{file_name} row {row_num}: '{key}' is required")
        return None
    parsed = parse_date(raw)
    if parsed is None:
        raise ValidationError(f"{file_name} row {row_num}: '{key}' must be YYYY-MM-DD, got {raw!r}")
    return parsed


def validate_pipeline(path: Path) -> None:
    headers, rows = read_csv(path)
    ensure_required_columns(headers, PIPELINE_REQUIRED_COLUMNS, str(path))
    if not rows:
        raise ValidationError(f"{path} has no data rows")

    for idx, row in enumerate(rows, start=2):
        require_non_empty(row, "account_name", idx, str(path))
        require_non_empty(row, "owner", idx, str(path))

        _ = check_enum(row, "segment", PIPELINE_SEGMENTS, idx, str(path))
        status = check_enum(row, "status", PIPELINE_STATUSES, idx, str(path))
        stage = check_enum(row, "stage", PIPELINE_STAGES, idx, str(path))
        _ = check_enum(row, "deal_type", PIPELINE_DEAL_TYPES, idx, str(path))

        email = row.get("contact_email", "").strip()
        if email and "@" not in email:
            raise ValidationError(f"{path} row {idx}: 'contact_email' must include '@', got {email!r}")

        acv = parse_number(row.get("acv_usd", ""))
        if acv < 0:
            raise ValidationError(f"{path} row {idx}: 'acv_usd' must be >= 0, got {acv}")

        probability = parse_number(row.get("probability_pct", ""))
        if probability < 0 or probability > 100:
            raise ValidationError(f"{path} row {idx}: 'probability_pct' must be in [0, 100], got {probability}")

        expected_close = check_date_field(row, "expected_close_date", idx, str(path), required=False)
        next_action_date = check_date_field(row, "next_action_date", idx, str(path), required=False)
        _ = check_date_field(row, "last_touch_date", idx, str(path), required=False)

        next_action = row.get("next_action", "").strip()

        if status == "open":
            if stage == "closed":
                raise ValidationError(f"{path} row {idx}: open opportunities cannot be in 'closed' stage")
            if expected_close is None:
                raise ValidationError(f"{path} row {idx}: open opportunities require 'expected_close_date'")
            if not next_action:
                raise ValidationError(f"{path} row {idx}: open opportunities require non-empty 'next_action'")
            if next_action_date is None:
                raise ValidationError(f"{path} row {idx}: open opportunities require 'next_action_date'")
            if probability >= 100:
                raise ValidationError(f"{path} row {idx}: open opportunities must have probability < 100")

        if status in {"won", "lost"} and stage != "closed":
            raise ValidationError(f"{path} row {idx}: status '{status}' requires stage 'closed'")

        if status == "won" and probability != 100:
            raise ValidationError(f"{path} row {idx}: status 'won' requires probability_pct = 100")
        if status == "lost" and probability != 0:
            raise ValidationError(f"{path} row {idx}: status 'lost' requires probability_pct = 0")


def validate_kpi(path: Path) -> None:
    headers, rows = read_csv(path)
    ensure_required_columns(headers, KPI_REQUIRED_COLUMNS, str(path))
    if not rows:
        raise ValidationError(f"{path} has no data rows")

    seen_weeks: set[str] = set()
    for idx, row in enumerate(rows, start=2):
        week_start = row.get("week_start", "").strip()
        if not week_start:
            raise ValidationError(f"{path} row {idx}: 'week_start' is required")
        if parse_date(week_start) is None:
            raise ValidationError(f"{path} row {idx}: 'week_start' must be YYYY-MM-DD, got {week_start!r}")
        if week_start in seen_weeks:
            raise ValidationError(f"{path} row {idx}: duplicate week_start {week_start!r}")
        seen_weeks.add(week_start)

        for key in KPI_NON_NEGATIVE_FIELDS:
            value = parse_number(row.get(key, ""))
            if value < 0:
                raise ValidationError(f"{path} row {idx}: '{key}' must be >= 0, got {value}")

        for key in KPI_PERCENT_FIELDS:
            value = parse_number(row.get(key, ""))
            if value < 0 or value > 100:
                raise ValidationError(f"{path} row {idx}: '{key}' must be in [0, 100], got {value}")

        nrr = parse_number(row.get("nrr_pct", ""))
        if nrr > 500:
            raise ValidationError(f"{path} row {idx}: 'nrr_pct' must be <= 500, got {nrr}")


def validate_deal_input(path: Path, contracts_dir: Path) -> None:
    if not path.exists():
        raise ValidationError(f"missing file: {path}")

    with path.open(encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path} invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValidationError(f"{path} root must be a JSON object")

    deal_id = str(data.get("deal_id", "")).strip()
    if not deal_id:
        raise ValidationError(f"{path}: 'deal_id' is required")
    if deal_pack.slugify(deal_id) != deal_id:
        raise ValidationError(
            f"{path}: 'deal_id' must be slug-like (letters/numbers/._-), got {deal_id!r}"
        )

    proposal_map = deal_pack.load_section(data, "proposal")
    sow_map = deal_pack.load_section(data, "sow")

    proposal_template = (contracts_dir / "PROPOSAL_TEMPLATE.md").read_text(encoding="utf-8")
    sow_template = (contracts_dir / "SOW_TEMPLATE.md").read_text(encoding="utf-8")
    # This enforces placeholder completeness and catches missing fields.
    _ = deal_pack.render_template(proposal_template, proposal_map, "PROPOSAL_TEMPLATE.md")
    _ = deal_pack.render_template(sow_template, sow_map, "SOW_TEMPLATE.md")

    kickoff = parse_date(proposal_map.get("kickoff_date", ""))
    midpoint = parse_date(proposal_map.get("midpoint_date", ""))
    handoff = parse_date(proposal_map.get("handoff_date", ""))
    if kickoff is None or midpoint is None or handoff is None:
        raise ValidationError(f"{path}: kickoff_date, midpoint_date, and handoff_date must be valid YYYY-MM-DD")
    if not (kickoff <= midpoint <= handoff):
        raise ValidationError(f"{path}: proposal timeline must satisfy kickoff <= midpoint <= handoff")

    start_date = parse_date(sow_map.get("start_date", ""))
    end_date = parse_date(sow_map.get("end_date", ""))
    if start_date is None or end_date is None:
        raise ValidationError(f"{path}: sow start_date and end_date must be valid YYYY-MM-DD")
    if start_date > end_date:
        raise ValidationError(f"{path}: sow timeline must satisfy start_date <= end_date")


def validate_portal_input(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"missing file: {path}")
    with path.open(encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path} invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: root must be a JSON object")

    for key in PORTAL_REQUIRED_FIELDS:
        value = str(data.get(key, "")).strip()
        if not value:
            raise ValidationError(f"{path}: missing required field {key!r}")

    engagement_id = str(data.get("engagement_id", "")).strip()
    if re.search(r"[^a-zA-Z0-9._-]", engagement_id):
        raise ValidationError(
            f"{path}: engagement_id must be slug-like (letters/numbers/._-), got {engagement_id!r}"
        )

    window = data.get("window", {})
    if window is not None and not isinstance(window, dict):
        raise ValidationError(f"{path}: field 'window' must be an object")
    if isinstance(window, dict):
        start = str(window.get("start", "")).strip()
        end = str(window.get("end", "")).strip()
        if start and parse_date(start) is None:
            raise ValidationError(f"{path}: window.start must be YYYY-MM-DD, got {start!r}")
        if end and parse_date(end) is None:
            raise ValidationError(f"{path}: window.end must be YYYY-MM-DD, got {end!r}")

    milestones = data.get("milestones", [])
    if milestones is not None and not isinstance(milestones, list):
        raise ValidationError(f"{path}: field 'milestones' must be a list")
    if isinstance(milestones, list):
        for idx, milestone in enumerate(milestones, start=1):
            if not isinstance(milestone, dict):
                raise ValidationError(f"{path}: milestone #{idx} must be an object")
            date_raw = str(milestone.get("date", "")).strip()
            if date_raw and parse_date(date_raw) is None:
                raise ValidationError(f"{path}: milestone #{idx} date must be YYYY-MM-DD, got {date_raw!r}")


def validate_case_study_input(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"missing file: {path}")
    with path.open(encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path} invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: root must be a JSON object")

    for key in CASE_STUDY_REQUIRED_FIELDS:
        value = str(data.get(key, "")).strip()
        if not value:
            raise ValidationError(f"{path}: missing required field {key!r}")

    case_study_id = str(data.get("case_study_id", "")).strip()
    if case_study_pack.slugify(case_study_id) != case_study_id:
        raise ValidationError(
            f"{path}: case_study_id must be slug-like (letters/numbers/._-), got {case_study_id!r}"
        )

    published_date = str(data.get("published_date", "")).strip()
    if parse_date(published_date) is None:
        raise ValidationError(f"{path}: published_date must be YYYY-MM-DD, got {published_date!r}")

    engagement_window = data.get("engagement_window", {})
    if engagement_window is not None and not isinstance(engagement_window, dict):
        raise ValidationError(f"{path}: field 'engagement_window' must be an object")
    if isinstance(engagement_window, dict):
        start = str(engagement_window.get("start", "")).strip()
        end = str(engagement_window.get("end", "")).strip()
        start_date = parse_date(start) if start else None
        end_date = parse_date(end) if end else None
        if start and start_date is None:
            raise ValidationError(f"{path}: engagement_window.start must be YYYY-MM-DD, got {start!r}")
        if end and end_date is None:
            raise ValidationError(f"{path}: engagement_window.end must be YYYY-MM-DD, got {end!r}")
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValidationError(f"{path}: engagement_window must satisfy start <= end")

    list_fields = [
        "scope_summary",
        "baseline_risks",
        "interventions",
        "outcomes",
        "artifacts_referenced",
        "anonymization_notes",
        "tags",
    ]
    for field_name in list_fields:
        value = data.get(field_name, [])
        if value is not None and not isinstance(value, list):
            raise ValidationError(f"{path}: field {field_name!r} must be a list")

    metrics = data.get("metrics", {})
    if not isinstance(metrics, dict):
        raise ValidationError(f"{path}: field 'metrics' must be an object")
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
        raise ValidationError(f"{path}: metrics missing required fields: {', '.join(missing_metrics)}")

    for key in required_metrics:
        value = metrics.get(key, None)
        try:
            num = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{path}: metrics.{key} must be numeric, got {value!r}") from exc
        if num < 0:
            raise ValidationError(f"{path}: metrics.{key} must be >= 0, got {num}")

    for key in ["ci_gate_pass_rate_before_pct", "ci_gate_pass_rate_after_pct"]:
        num = float(metrics.get(key))
        if num < 0 or num > 100:
            raise ValidationError(f"{path}: metrics.{key} must be in [0, 100], got {num}")

    quote = data.get("quote", {})
    if quote is not None and not isinstance(quote, dict):
        raise ValidationError(f"{path}: field 'quote' must be an object")
    if isinstance(quote, dict) and quote:
        speaker_role = str(quote.get("speaker_role", "")).strip()
        text = str(quote.get("text", "")).strip()
        if text and not speaker_role:
            raise ValidationError(f"{path}: quote.speaker_role is required when quote.text is set")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", type=Path, help="Path to pipeline CSV.")
    parser.add_argument("--kpi", type=Path, help="Path to KPI tracker CSV.")
    parser.add_argument("--deal-input", type=Path, help="Path to deal input JSON.")
    parser.add_argument("--portal-input", type=Path, help="Path to evidence portal input JSON.")
    parser.add_argument("--case-study-input", type=Path, help="Path to case-study input JSON.")
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=Path("strategy/assets/contracts"),
        help="Contracts template directory for deal placeholder validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.pipeline is None
        and args.kpi is None
        and args.deal_input is None
        and args.portal_input is None
        and args.case_study_input is None
    ):
        raise ValidationError(
            "provide at least one of: --pipeline, --kpi, --deal-input, --portal-input, --case-study-input"
        )

    validated: list[str] = []
    if args.pipeline is not None:
        validate_pipeline(args.pipeline)
        validated.append(f"pipeline={args.pipeline}")
    if args.kpi is not None:
        validate_kpi(args.kpi)
        validated.append(f"kpi={args.kpi}")
    if args.deal_input is not None:
        validate_deal_input(args.deal_input, args.contracts_dir)
        validated.append(f"deal_input={args.deal_input}")
    if args.portal_input is not None:
        validate_portal_input(args.portal_input)
        validated.append(f"portal_input={args.portal_input}")
    if args.case_study_input is not None:
        validate_case_study_input(args.case_study_input)
        validated.append(f"case_study_input={args.case_study_input}")

    print("strategy data validation passed:")
    for item in validated:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as err:
        print(f"validation error: {err}")
        raise SystemExit(1)
    except Exception as err:  # pragma: no cover - defensive CLI guard
        print(f"unexpected error: {err}")
        raise SystemExit(1)
