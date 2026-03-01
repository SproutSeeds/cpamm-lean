#!/usr/bin/env python3
"""Build a stable case-study portal entrypoint from rollup artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CaseStudyPortalError(Exception):
    pass


def load_rollup(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CaseStudyPortalError(f"missing rollup JSON: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CaseStudyPortalError(f"invalid rollup JSON in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise CaseStudyPortalError(f"rollup JSON root must be object: {path}")
    if not isinstance(raw.get("rollup", None), dict):
        raise CaseStudyPortalError(f"rollup JSON missing 'rollup' object: {path}")
    entries = raw.get("entries", None)
    if entries is None or not isinstance(entries, list):
        raise CaseStudyPortalError(f"rollup JSON missing 'entries' list: {path}")
    return raw


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_case_studies(src_dir: Path | None, out_dir: Path) -> tuple[Path | None, int]:
    if src_dir is None:
        return None, 0
    if not src_dir.exists() or not src_dir.is_dir():
        raise CaseStudyPortalError(f"missing case-studies directory: {src_dir}")
    dst = out_dir / "case-studies"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src_dir, dst)
    count = len(list(dst.rglob("CASE_STUDY.md")))
    return dst, count


def case_link(case_id: str, case_root: Path | None, out_dir: Path) -> str:
    if case_root is None:
        return "-"
    target = case_root / case_id / "CASE_STUDY.md"
    if target.exists():
        rel = target.relative_to(out_dir)
        return f"[Open]({rel.as_posix()})"
    return "-"


def render_index(
    *,
    title: str,
    generated_at: str,
    rollup_payload: dict[str, Any],
    out_dir: Path,
    copied_case_root: Path | None,
    copied_case_count: int,
) -> str:
    rollup = rollup_payload["rollup"]
    entries = rollup_payload["entries"]

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("Single-entrypoint view of sanitized case-study outcomes and evidence links.")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at (UTC): {generated_at}")
    lines.append(f"- Case studies: {rollup.get('case_study_count', 0)}")
    window = rollup.get("published_window", {})
    if isinstance(window, dict):
        lines.append(f"- Published window: {window.get('start', '')} to {window.get('end', '')}")
    totals = rollup.get("totals", {})
    averages = rollup.get("averages", {})
    if isinstance(totals, dict):
        lines.append(f"- Total critical findings prevented: {totals.get('critical_findings_prevented', 0)}")
        lines.append(f"- Total proof obligations closed: {totals.get('proof_obligations_closed', 0)}")
        lines.append(f"- Total regression escape reduction: {totals.get('regression_escape_reduction', 0)}")
    if isinstance(averages, dict):
        lines.append(
            "- Average CI gate improvement (pct points): "
            f"{averages.get('ci_gate_improvement_pct_points', 0)}"
        )
        lines.append(
            "- Average time-to-green reduction (days): "
            f"{averages.get('time_to_green_reduction_days', 0)}"
        )
    lines.append(f"- Copied case-study markdown files: {copied_case_count}")
    lines.append("")
    lines.append("## Core Artifacts")
    lines.append("")
    lines.append("- [Case Studies Index](CASE_STUDIES_INDEX.md)")
    lines.append("- [Case Studies Rollup](CASE_STUDIES_ROLLUP.json)")
    lines.append("")
    lines.append("## Case Studies")
    lines.append("")
    lines.append("| Case Study ID | Title | Published | Segment | Engagement | Link |")
    lines.append("|---|---|---|---|---|---|")
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        case_id = str(entry.get("case_study_id", "")).strip()
        title_text = str(entry.get("title", "")).strip()
        published = str(entry.get("published_date", "")).strip()
        segment = str(entry.get("client_segment", "")).strip()
        engagement = str(entry.get("engagement_type", "")).strip()
        link = case_link(case_id, copied_case_root, out_dir)
        lines.append(
            f"| {case_id} | {title_text} | {published} | {segment} | {engagement} | {link} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index-md",
        required=True,
        type=Path,
        help="Path to case-study index markdown source.",
    )
    parser.add_argument(
        "--rollup-json",
        required=True,
        type=Path,
        help="Path to case-study rollup JSON source.",
    )
    parser.add_argument(
        "--case-studies-dir",
        type=Path,
        default=None,
        help="Optional directory containing per-case-study folders with CASE_STUDY.md files.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("artifacts/case-study-portal"),
        help="Output portal directory.",
    )
    parser.add_argument(
        "--title",
        default="Case Study Portal",
        help="Landing page title.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.index_md.exists():
        raise CaseStudyPortalError(f"missing index markdown: {args.index_md}")

    rollup_payload = load_rollup(args.rollup_json)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    copy_file(args.index_md, out_dir / "CASE_STUDIES_INDEX.md")
    copy_file(args.rollup_json, out_dir / "CASE_STUDIES_ROLLUP.json")
    copied_case_root, copied_case_count = copy_case_studies(args.case_studies_dir, out_dir)

    index_text = render_index(
        title=args.title,
        generated_at=generated_at,
        rollup_payload=rollup_payload,
        out_dir=out_dir,
        copied_case_root=copied_case_root,
        copied_case_count=copied_case_count,
    )
    (out_dir / "INDEX.md").write_text(index_text, encoding="utf-8")

    manifest = {
        "generated_at_utc": generated_at,
        "title": args.title,
        "source_index_md": str(args.index_md),
        "source_rollup_json": str(args.rollup_json),
        "source_case_studies_dir": None if args.case_studies_dir is None else str(args.case_studies_dir),
        "out_dir": str(out_dir),
        "copied_case_study_count": copied_case_count,
        "files": [
            "INDEX.md",
            "CASE_STUDIES_INDEX.md",
            "CASE_STUDIES_ROLLUP.json",
            "MANIFEST.json",
        ],
    }
    if copied_case_root is not None:
        manifest["files"].append("case-studies/")

    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"generated case-study portal: {out_dir}")
    print(f"- {out_dir / 'INDEX.md'}")
    print(f"- {out_dir / 'CASE_STUDIES_INDEX.md'}")
    print(f"- {out_dir / 'CASE_STUDIES_ROLLUP.json'}")
    print(f"- {out_dir / 'MANIFEST.json'}")
    if copied_case_root is not None:
        print(f"- {out_dir / 'case-studies'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CaseStudyPortalError as err:
        print(f"case-study-portal error: {err}")
        raise SystemExit(1)
