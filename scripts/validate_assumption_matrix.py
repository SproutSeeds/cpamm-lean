#!/usr/bin/env python3
"""Validate that test references in reports/ASSUMPTION_TEST_MATRIX.md exist."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "reports" / "ASSUMPTION_TEST_MATRIX.md"
TEST_DIR = ROOT / "solidity" / "test"


def main() -> int:
    if not MATRIX.exists():
        print(f"error: matrix file not found: {MATRIX}")
        return 1

    text = MATRIX.read_text(encoding="utf-8")

    tokens = re.findall(r"`([^`]+)`", text)
    errors: list[str] = []

    # Enforce fully-qualified test references in the matrix.
    for token in tokens:
        if token.startswith("test") and "::" not in token:
            errors.append(
                f"unqualified test reference `{token}`; use `File.t.sol::{token}`"
            )

    refs = sorted(
        set(re.findall(r"([A-Za-z0-9_.-]+\.t\.sol::[A-Za-z0-9_]+)", text))
    )
    if not refs:
        errors.append("no fully-qualified test references found in matrix")

    for ref in refs:
        file_name, fn_name = ref.split("::", 1)
        file_path = TEST_DIR / file_name

        if not file_path.exists():
            errors.append(f"missing test file for `{ref}`: {file_path}")
            continue

        source = file_path.read_text(encoding="utf-8")
        fn_pat = re.compile(rf"\bfunction\s+{re.escape(fn_name)}\s*\(")
        if fn_pat.search(source) is None:
            errors.append(f"missing test function for `{ref}` in {file_path}")

    if errors:
        print("assumption matrix validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(
        "assumption matrix validation passed: "
        f"{len(refs)} fully-qualified references verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
