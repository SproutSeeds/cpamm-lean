#!/usr/bin/env python3
"""Generate and sync theorem inventory views from CPAMM Lean files."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

SECTION_HEADING = "## Proven Theorems"
SECTION_RE = re.compile(r"^###\s+`([^`]+\.lean)`\s*$")
THEOREM_RE = re.compile(r"^\s*theorem\s+([A-Za-z_][A-Za-z0-9_']*)\b", re.MULTILINE)


def collect_theorems(cpamm_dir: Path) -> dict[str, list[str]]:
    theorem_map: dict[str, list[str]] = {}
    for lean_file in sorted(cpamm_dir.glob("*.lean")):
        rel = f"CPAMM/{lean_file.name}"
        names = THEOREM_RE.findall(lean_file.read_text(encoding="utf-8"))
        theorem_map[rel] = names
    return theorem_map


def read_proven_section(verification_md: Path) -> tuple[str, str, str]:
    text = verification_md.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    start = None
    for idx, line in enumerate(lines):
        if line.strip() == SECTION_HEADING:
            start = idx
            break
    if start is None:
        raise ValueError(f"missing `{SECTION_HEADING}` section in {verification_md}")

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break

    prefix = "".join(lines[:start])
    section = "".join(lines[start:end])
    suffix = "".join(lines[end:])
    return prefix, section, suffix


def parse_section_order(section: str) -> list[str]:
    order: list[str] = []
    for line in section.splitlines():
        match = SECTION_RE.match(line)
        if match:
            order.append(match.group(1))
    return order


def render_verification_section(
    theorem_map: dict[str, list[str]],
    preferred_order: list[str],
) -> str:
    seen: set[str] = set()
    ordered_files: list[str] = []

    for file_path in preferred_order:
        if file_path in theorem_map and theorem_map[file_path]:
            ordered_files.append(file_path)
            seen.add(file_path)

    for file_path in sorted(theorem_map):
        if file_path in seen:
            continue
        if theorem_map[file_path]:
            ordered_files.append(file_path)

    out: list[str] = [SECTION_HEADING, ""]
    for file_path in ordered_files:
        out.append(f"### `{file_path}`")
        for theorem_name in theorem_map[file_path]:
            out.append(f"- `{theorem_name}`")
        out.append("")
    return "\n".join(out).rstrip() + "\n\n"


def render_inventory_markdown(theorem_map: dict[str, list[str]]) -> str:
    total = 0
    out: list[str] = ["# CPAMM Theorem Inventory", ""]
    for file_path in sorted(theorem_map):
        theorem_names = theorem_map[file_path]
        if not theorem_names:
            continue
        out.append(f"## {Path(file_path).name}")
        out.append("")
        for theorem_name in theorem_names:
            out.append(f"- `{theorem_name}`")
        out.append("")
        total += len(theorem_names)
    out.append(f"Total theorems: `{total}`")
    out.append("")
    return "\n".join(out)


def check_sync(current: str, generated: str, label: str) -> tuple[bool, str]:
    if current == generated:
        return True, f"{label} is in sync"

    diff = "".join(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            generated.splitlines(keepends=True),
            fromfile=f"{label} (current)",
            tofile=f"{label} (generated)",
        )
    )
    message = f"{label} is out of sync\n{diff}"
    return False, message


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate theorem inventory and sync VERIFICATION.md theorem section."
    )
    parser.add_argument("--root", default=".", help="Repository root (default: .)")
    parser.add_argument(
        "--verification-md",
        default="VERIFICATION.md",
        help="Verification markdown path (default: VERIFICATION.md)",
    )
    parser.add_argument(
        "--out",
        help="Optional output path for standalone theorem inventory markdown",
    )
    parser.add_argument(
        "--check-verification",
        action="store_true",
        help="Fail if VERIFICATION.md proven-theorems section is out of sync.",
    )
    parser.add_argument(
        "--write-verification",
        action="store_true",
        help="Rewrite VERIFICATION.md proven-theorems section from Lean declarations.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    cpamm_dir = root / "CPAMM"
    verification_md = Path(args.verification_md).resolve()

    if not cpamm_dir.exists():
        print(f"error: CPAMM directory not found: {cpamm_dir}")
        return 1

    theorem_map = collect_theorems(cpamm_dir)
    prefix, current_section, suffix = read_proven_section(verification_md)
    preferred_order = parse_section_order(current_section)
    generated_section = render_verification_section(theorem_map, preferred_order)

    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_inventory_markdown(theorem_map), encoding="utf-8")

    if args.check_verification:
        ok, message = check_sync(
            current_section,
            generated_section,
            label=str(verification_md),
        )
        if not ok:
            print(message)
            return 1
        print(message)

    if args.write_verification:
        updated = prefix + generated_section + suffix
        verification_md.write_text(updated, encoding="utf-8")
        print(f"updated {verification_md}")

    if not args.out and not args.check_verification and not args.write_verification:
        print(render_inventory_markdown(theorem_map), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
