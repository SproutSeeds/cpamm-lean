#!/usr/bin/env python3
"""Validate theorem inventory in VERIFICATION.md against Lean declarations."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"^###\s+`([^`]+\.lean)`\s*$")
BULLET_RE = re.compile(r"^- `([A-Za-z_][A-Za-z0-9_']*)`\s*$")
THEOREM_RE = re.compile(r"^\s*theorem\s+([A-Za-z_][A-Za-z0-9_']*)\b", re.MULTILINE)


def parse_sections(verification_text: str) -> dict[Path, list[str]]:
    refs: dict[Path, list[str]] = {}
    current_section: Path | None = None

    for line in verification_text.splitlines():
        section_match = SECTION_RE.match(line)
        if section_match:
            current_section = Path(section_match.group(1))
            refs.setdefault(current_section, [])
            continue

        if current_section is None:
            continue

        if line.startswith("### "):
            current_section = None
            continue

        theorem_match = BULLET_RE.match(line)
        if theorem_match:
            refs[current_section].append(theorem_match.group(1))

    return refs


def collect_theorems(lean_file: Path) -> list[str]:
    source = lean_file.read_text(encoding="utf-8")
    return THEOREM_RE.findall(source)


def validate(
    verification_md: Path,
    root: Path,
    require_complete: bool,
) -> tuple[bool, list[str], int, int]:
    if not verification_md.exists():
        return False, [f"verification file not found: {verification_md}"], 0, 0

    refs = parse_sections(verification_md.read_text(encoding="utf-8"))
    if not refs:
        return (
            False,
            ["no theorem references found in verification file (expected section bullets)"],
            0,
            0,
        )

    errors: list[str] = []
    theorem_cache: dict[Path, list[str]] = {}
    listed_count = 0

    for relative_path, listed_theorems in refs.items():
        listed_count += len(listed_theorems)
        lean_file = root / relative_path
        if not lean_file.exists():
            errors.append(f"section file not found: {relative_path}")
            continue

        if lean_file not in theorem_cache:
            theorem_cache[lean_file] = collect_theorems(lean_file)

        declared_theorems = theorem_cache[lean_file]
        declared_set = set(declared_theorems)
        listed_set = set(listed_theorems)

        seen: set[str] = set()
        for theorem_name in listed_theorems:
            if theorem_name in seen:
                errors.append(
                    f"duplicate theorem `{theorem_name}` listed under {relative_path}"
                )
                continue
            seen.add(theorem_name)
            if theorem_name not in declared_set:
                errors.append(
                    f"theorem `{theorem_name}` not declared in {relative_path}"
                )

        if require_complete:
            missing = sorted(declared_set - listed_set)
            for theorem_name in missing:
                errors.append(
                    "theorem "
                    f"`{theorem_name}` declared in {relative_path} "
                    "but missing from VERIFICATION.md inventory"
                )

    unique_files = len(refs)
    return not errors, errors, listed_count, unique_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate theorem inventory entries in VERIFICATION.md."
    )
    parser.add_argument(
        "--verification-md",
        default="VERIFICATION.md",
        help="Path to verification markdown file (default: VERIFICATION.md)",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root for resolving Lean file paths (default: .)",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Only validate listed references (skip completeness check).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    verification_md = Path(args.verification_md).resolve()
    require_complete = not args.allow_incomplete

    ok, errors, ref_count, file_count = validate(
        verification_md,
        root,
        require_complete=require_complete,
    )
    if not ok:
        print("theorem inventory validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    mode = "complete" if require_complete else "listed-only"
    print(
        "theorem inventory validation passed: "
        f"{ref_count} references across {file_count} Lean files ({mode} mode)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
