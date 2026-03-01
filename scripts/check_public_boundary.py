#!/usr/bin/env python3
"""Fail when private/commercial-only files are tracked in the public repo."""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path


FORBIDDEN_EXACT = {
    "strategy/EXECUTION_90_DAYS.md",
    "strategy/FUNDRAISING_AND_DATA_ROOM.md",
    "strategy/HIGHEST_EV_PATH.md",
    "strategy/KPI_SCOREBOARD.md",
    "strategy/LEGAL_COMPLIANCE_US.md",
    "strategy/OFFER_AND_GTM.md",
    "strategy/OPERATING_CADENCE.md",
    "strategy/REVENUE_MODEL.md",
    "strategy/RISK_REGISTER.md",
    "reports/PIPELINE_HEALTH.md",
    "reports/OUTBOUND_SLA.md",
}

FORBIDDEN_GLOBS = (
    "strategy/private/*",
    "strategy/private/**",
    "reports/OUTBOUND_*",
    "reports/PIPELINE_HEALTH_PRIVATE.md",
    "reports/WEEKLY_DASHBOARD_PRIVATE.md",
    "reports/CASE_STUDIES_*_PRIVATE.*",
)


def tracked_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def main() -> int:
    files = tracked_files()
    violations: list[str] = []
    seen: set[str] = set()

    for path in files:
        if not Path(path).exists():
            # Ignore tracked files that are already deleted in the working tree.
            continue
        if path in FORBIDDEN_EXACT and path not in seen:
            seen.add(path)
            violations.append(path)
            continue
        for pattern in FORBIDDEN_GLOBS:
            if fnmatch.fnmatch(path, pattern) and path not in seen:
                seen.add(path)
                violations.append(path)
                break

    if violations:
        print("error: private/commercial-only files must not be tracked:")
        for path in sorted(violations):
            print(f"- {path}")
        return 1

    print("public-boundary check passed: no forbidden tracked files found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
