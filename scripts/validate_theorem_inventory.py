#!/usr/bin/env python3
"""Validate theorem references in VERIFICATION.md against Lean declarations."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SECTION_RE = re.compile(r"^###\s+`([^`]+\.lean)`\s*$")
BULLET_RE = re.compile(r"^- `([A-Za-z_][A-Za-z0-9_']*)`\s*$")
THEOREM_RE = re.compile(r"^\s*theorem\s+([A-Za-z_][A-Za-z0-9_']*)\b", re.MULTILINE)


@dataclass(frozen=True)
class SectionRef:
    file_path: Path
    theorem_name: str


def parse_sections(verification_text: str) -> list[SectionRef]:
    refs: list[SectionRef] = []
    current_section: Path | None = None

    for line in verification_text.splitlines():
        section_match = SECTION_RE.match(line)
        if section_match:
            current_section = Path(section_match.group(1))
            continue

        if current_section is None:
            continue

        if line.startswith("### "):
            current_section = None
            continue

        theorem_match = BULLET_RE.match(line)
        if theorem_match:
            refs.append(
                SectionRef(
                    file_path=current_section,
                    theorem_name=theorem_match.group(1),
                )
            )

    return refs


def collect_theorems(lean_file: Path) -> set[str]:
    source = lean_file.read_text(encoding="utf-8")
    return set(THEOREM_RE.findall(source))


def validate(verification_md: Path, root: Path) -> tuple[bool, list[str], int, int]:
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
    theorem_cache: dict[Path, set[str]] = {}

    for ref in refs:
        lean_file = root / ref.file_path
        if not lean_file.exists():
            errors.append(f"section file not found for `{ref.theorem_name}`: {ref.file_path}")
            continue

        if lean_file not in theorem_cache:
            theorem_cache[lean_file] = collect_theorems(lean_file)

        if ref.theorem_name not in theorem_cache[lean_file]:
            errors.append(
                f"theorem `{ref.theorem_name}` not declared in {ref.file_path}"
            )

    unique_files = len({ref.file_path for ref in refs})
    return not errors, errors, len(refs), unique_files


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
    args = parser.parse_args()

    root = Path(args.root).resolve()
    verification_md = Path(args.verification_md).resolve()

    ok, errors, ref_count, file_count = validate(verification_md, root)
    if not ok:
        print("theorem inventory validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(
        "theorem inventory validation passed: "
        f"{ref_count} references across {file_count} Lean files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
