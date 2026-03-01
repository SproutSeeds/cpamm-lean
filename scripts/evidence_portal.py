#!/usr/bin/env python3
"""Generate a client-facing evidence portal from engagement metadata and artifacts."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PortalError(Exception):
    pass


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return slug or "engagement"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PortalError(f"missing input file: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PortalError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PortalError("portal input root must be a JSON object")
    return raw


def get_required_str(data: dict[str, Any], key: str) -> str:
    value = str(data.get(key, "")).strip()
    if not value:
        raise PortalError(f"missing required field: {key}")
    return value


def get_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise PortalError(f"expected list for field: {key}")
    return value


def get_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise PortalError(f"expected object for field: {key}")
    return value


def render_bullets(items: list[Any], empty: str = "None") -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in cleaned)


def render_milestones(rows: list[Any]) -> str:
    lines = [
        "| Milestone | Date | Status | Notes |",
        "|---|---|---|---|",
    ]
    if not rows:
        lines.append("| (none) | | | |")
        return "\n".join(lines)
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).strip()
        date = str(row.get("date", "")).strip()
        status = str(row.get("status", "")).strip()
        notes = str(row.get("notes", "")).strip()
        lines.append(f"| {name} | {date} | {status} | {notes} |")
    return "\n".join(lines)


def render_next_actions(rows: list[Any]) -> str:
    lines = [
        "| Action | Owner | Due |",
        "|---|---|---|",
    ]
    if not rows:
        lines.append("| (none) | | |")
        return "\n".join(lines)
    for row in rows:
        if not isinstance(row, dict):
            continue
        action = str(row.get("action", "")).strip()
        owner = str(row.get("owner", "")).strip()
        due = str(row.get("due", "")).strip()
        lines.append(f"| {action} | {owner} | {due} |")
    return "\n".join(lines)


def render_risks(rows: list[Any]) -> str:
    lines = [
        "| Risk | Severity | Status | Mitigation |",
        "|---|---|---|---|",
    ]
    if not rows:
        lines.append("| (none) | | | |")
        return "\n".join(lines)
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title", "")).strip()
        severity = str(row.get("severity", "")).strip()
        status = str(row.get("status", "")).strip()
        mitigation = str(row.get("mitigation", "")).strip()
        lines.append(f"| {title} | {severity} | {status} | {mitigation} |")
    return "\n".join(lines)


def render_findings(rows: list[Any]) -> str:
    lines = [
        "| ID | Finding | Severity | Status | Evidence |",
        "|---|---|---|---|---|",
    ]
    if not rows:
        lines.append("| (none) | | | | |")
        return "\n".join(lines)
    for row in rows:
        if not isinstance(row, dict):
            continue
        fid = str(row.get("id", "")).strip()
        title = str(row.get("title", "")).strip()
        severity = str(row.get("severity", "")).strip()
        status = str(row.get("status", "")).strip()
        evidence = str(row.get("evidence", "")).strip()
        lines.append(f"| {fid} | {title} | {severity} | {status} | {evidence} |")
    return "\n".join(lines)


def render_gate_status(gates: dict[str, Any]) -> str:
    ordered = ["formal", "tests", "security", "ci"]
    lines = [
        "| Gate | Status |",
        "|---|---|",
    ]
    for gate in ordered:
        status = str(gates.get(gate, "unknown")).strip() or "unknown"
        lines.append(f"| {gate} | {status} |")
    return "\n".join(lines)


def list_files(base_dir: Path) -> list[str]:
    files: list[str] = []
    if not base_dir.exists() or not base_dir.is_dir():
        return files
    for p in sorted(base_dir.rglob("*")):
        if p.is_file():
            files.append(str(p.relative_to(base_dir)))
    return files


def summarize_source(name: str, path: Path | None) -> str:
    if path is None:
        return f"### {name}\n\n- Not provided.\n"
    if not path.exists() or not path.is_dir():
        return f"### {name}\n\n- Missing directory: `{path}`\n"

    files = list_files(path)
    lines: list[str] = []
    lines.append(f"### {name}")
    lines.append("")
    lines.append(f"- Source path: `{path}`")
    lines.append(f"- File count: {len(files)}")
    lines.append("")
    lines.append("Top files:")
    for rel in files[:20]:
        lines.append(f"- `{rel}`")
    if len(files) > 20:
        lines.append(f"- ... ({len(files) - 20} more)")
    lines.append("")
    sha = path / "SHA256SUMS"
    if sha.exists():
        lines.append("SHA256 checksums available: `SHA256SUMS`")
        snippet = sha.read_text(encoding="utf-8").splitlines()[:5]
        lines.append("")
        lines.append("```text")
        lines.extend(snippet)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def summarize_file_source(name: str, path: Path | None) -> str:
    if path is None:
        return f"### {name}\n\n- Not provided.\n"
    if not path.exists() or not path.is_file():
        return f"### {name}\n\n- Missing file: `{path}`\n"

    lines: list[str] = []
    lines.append(f"### {name}")
    lines.append("")
    lines.append(f"- Source path: `{path}`")
    lines.append(f"- Size (bytes): {path.stat().st_size}")
    lines.append("")
    if path.suffix.lower() in {".md", ".json"}:
        snippet = path.read_text(encoding="utf-8").splitlines()[:12]
        lines.append("Preview:")
        lines.append("")
        lines.append("```text")
        lines.extend(snippet)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def maybe_copy_source(src: Path | None, dst: Path) -> None:
    if src is None or not src.exists() or not src.is_dir():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def maybe_copy_file(src: Path | None, dst: Path) -> None:
    if src is None or not src.exists() or not src.is_file():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Portal input JSON path.")
    parser.add_argument(
        "--portal-dir",
        type=Path,
        default=None,
        help="Output portal directory (default: strategy/private/portals/<engagement_id>).",
    )
    parser.add_argument(
        "--commercial-package-dir",
        type=Path,
        default=None,
        help="Optional commercial package directory to reference in portal artifacts page.",
    )
    parser.add_argument(
        "--review-package-dir",
        type=Path,
        default=None,
        help="Optional technical review package directory to reference in portal artifacts page.",
    )
    parser.add_argument(
        "--case-studies-index",
        type=Path,
        default=None,
        help="Optional case-study index markdown file to reference in portal artifacts page.",
    )
    parser.add_argument(
        "--case-studies-rollup",
        type=Path,
        default=None,
        help="Optional case-study rollup JSON file to reference in portal artifacts page.",
    )
    parser.add_argument(
        "--copy-artifacts",
        action="store_true",
        help="Copy provided artifact directories into portal/artifacts/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = load_json(args.input)

    engagement_id = get_required_str(data, "engagement_id")
    if slugify(engagement_id) != engagement_id:
        raise PortalError(
            f"engagement_id must be slug-like (letters/numbers/._-), got {engagement_id!r}"
        )

    client_name = get_required_str(data, "client_name")
    protocol_name = get_required_str(data, "protocol_name")
    engagement_type = get_required_str(data, "engagement_type")
    status = get_required_str(data, "status")
    owner = get_required_str(data, "owner")
    technical_contact = str(data.get("technical_contact", "")).strip()

    window = get_dict(data, "window")
    start = str(window.get("start", "")).strip()
    end = str(window.get("end", "")).strip()

    objectives = get_list(data, "objectives")
    scope_in = get_list(data, "scope_in")
    scope_out = get_list(data, "scope_out")
    milestones = get_list(data, "milestones")
    gates = get_dict(data, "gate_status")
    assumptions = get_list(data, "assumptions")
    risks = get_list(data, "risks")
    findings = get_list(data, "findings")
    next_actions = get_list(data, "next_actions")
    client_access = get_list(data, "client_access")

    portal_dir = args.portal_dir or (Path("strategy/private/portals") / engagement_id)
    portal_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    index_text = f"""# Evidence Portal

## Engagement Snapshot

- Engagement ID: {engagement_id}
- Client: {client_name}
- Protocol: {protocol_name}
- Engagement Type: {engagement_type}
- Status: {status}
- Owner: {owner}
- Technical Contact: {technical_contact}
- Window: {start} to {end}
- Generated At (UTC): {generated_at}

## Objectives

{render_bullets(objectives)}

## Quick Links

- [Status](STATUS.md)
- [Artifacts](ARTIFACTS.md)
- [Assumptions And Risks](ASSUMPTIONS_RISKS.md)
- [Findings](FINDINGS.md)
- [Client Access](ACCESS.md)
"""

    status_text = f"""# Status

## Gate Status

{render_gate_status(gates)}

## Milestones

{render_milestones(milestones)}

## Next Actions

{render_next_actions(next_actions)}
"""

    artifacts_text = "\n".join(
        [
            "# Artifacts",
            "",
            summarize_source("Commercial Package", args.commercial_package_dir),
            summarize_source("Technical Review Package", args.review_package_dir),
            summarize_file_source("Case Studies Index", args.case_studies_index),
            summarize_file_source("Case Studies Rollup", args.case_studies_rollup),
        ]
    )

    assumptions_risks_text = f"""# Assumptions And Risks

## In Scope

{render_bullets(scope_in)}

## Out Of Scope

{render_bullets(scope_out)}

## Assumptions

{render_bullets(assumptions)}

## Risks

{render_risks(risks)}
"""

    findings_text = f"""# Findings

{render_findings(findings)}
"""

    access_text = f"""# Client Access

The client receives access to the current engagement status and evidence artifacts.

{render_bullets(client_access)}
"""

    write_files = {
        "INDEX.md": index_text,
        "STATUS.md": status_text,
        "ARTIFACTS.md": artifacts_text,
        "ASSUMPTIONS_RISKS.md": assumptions_risks_text,
        "FINDINGS.md": findings_text,
        "ACCESS.md": access_text,
    }
    for name, text in write_files.items():
        (portal_dir / name).write_text(text, encoding="utf-8")

    copied = {"commercial": None, "review": None, "case_studies_index": None, "case_studies_rollup": None}
    if args.copy_artifacts:
        artifacts_dir = portal_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        if args.commercial_package_dir is not None:
            commercial_dst = artifacts_dir / "commercial-package"
            maybe_copy_source(args.commercial_package_dir, commercial_dst)
            copied["commercial"] = str(commercial_dst)
        if args.review_package_dir is not None:
            review_dst = artifacts_dir / "review-package"
            maybe_copy_source(args.review_package_dir, review_dst)
            copied["review"] = str(review_dst)
        if args.case_studies_index is not None:
            index_dst = artifacts_dir / "case-studies" / "CASE_STUDIES_INDEX.md"
            maybe_copy_file(args.case_studies_index, index_dst)
            if index_dst.exists():
                copied["case_studies_index"] = str(index_dst)
        if args.case_studies_rollup is not None:
            rollup_dst = artifacts_dir / "case-studies" / "CASE_STUDIES_ROLLUP.json"
            maybe_copy_file(args.case_studies_rollup, rollup_dst)
            if rollup_dst.exists():
                copied["case_studies_rollup"] = str(rollup_dst)

    manifest = {
        "generated_at_utc": generated_at,
        "engagement_id": engagement_id,
        "input_file": str(args.input),
        "portal_dir": str(portal_dir),
        "commercial_package_dir": None if args.commercial_package_dir is None else str(args.commercial_package_dir),
        "review_package_dir": None if args.review_package_dir is None else str(args.review_package_dir),
        "case_studies_index": None if args.case_studies_index is None else str(args.case_studies_index),
        "case_studies_rollup": None if args.case_studies_rollup is None else str(args.case_studies_rollup),
        "copy_artifacts": args.copy_artifacts,
        "copied_artifacts": copied,
        "files": sorted(write_files.keys()),
    }
    (portal_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"generated evidence portal: {portal_dir}")
    for name in sorted(write_files.keys()):
        print(f"- {portal_dir / name}")
    print(f"- {portal_dir / 'MANIFEST.json'}")
    if args.copy_artifacts:
        print(f"- {portal_dir / 'artifacts'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PortalError as err:
        print(f"portal error: {err}")
        raise SystemExit(1)
