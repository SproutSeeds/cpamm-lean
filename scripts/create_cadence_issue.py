#!/usr/bin/env python3
"""Create recurring KPI/risk cadence issues with duplicate protection."""

from __future__ import annotations

import argparse
import calendar
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class IssuePayload:
    title: str
    body: str
    labels: list[str]


LABEL_DEFINITIONS: dict[str, tuple[str, str]] = {
    "ops": ("0e8a16", "Operating cadence"),
    "kpi-review": ("1d76db", "Weekly KPI review"),
    "risk-review": ("d93f0b", "Risk register review"),
}


def parse_ref_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"reference date must be YYYY-MM-DD, got {value!r}") from exc


def next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
    return match.group(1) if match else None


def build_payload(kind: str, ref: date) -> IssuePayload:
    if kind == "kpi":
        week_start = ref
        week_end = ref + timedelta(days=6)
        title = f"[KPI] Weekly Review - {ref.isoformat()}"
        labels = ["ops", "kpi-review"]
        body = f"""## Week Window

- Week start: {week_start.isoformat()}
- Week end: {week_end.isoformat()}

## KPI Snapshot

- Verified releases:
- Paid customers:
- MRR (USD):
- Time-to-green-release (days):
- Discovery calls:
- Proposal win rate (%):
- Sprint-to-retainer (%):
- NRR (%):
- Regression escapes:
- CI gate pass rate (%):
- Evidence package success rate (%):

## Pipeline Health Inputs

- Open opportunities:
- Weighted pipeline (USD):
- Expected weighted closes (30d):
- Expected weighted closes (60d):
- Stale opportunities count:

## What Improved This Week

- 

## Misses / Risks

- 

## Corrective Actions (Owners + Due Dates)

- [ ] Action:
  - Owner:
  - Due:

## Links

- Weekly dashboard:
- Pipeline health report:
- Review package / release artifacts:
"""
        return IssuePayload(title=title, body=body, labels=labels)

    if kind == "risk":
        month_start = ref.replace(day=1)
        month_end = ref.replace(day=calendar.monthrange(ref.year, ref.month)[1])
        title = f"[RISK] Register Review - {ref.isoformat()}"
        labels = ["ops", "risk-review"]
        body = f"""## Review Window

- Period: {month_start.isoformat()} to {month_end.isoformat()}
- Facilitator:
- Participants:

## Top Risks Re-Ranking

| Risk | Previous Likelihood | Previous Impact | New Likelihood | New Impact | Reason For Change |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

## New Risks Identified

- 

## Mitigation Status

- [ ] Mitigation update:
  - Owner:
  - Due:

## Escalations

- Does any risk now require legal/compliance escalation? `yes/no`
- Does any risk block current revenue plan? `yes/no`
- Does any risk require scope freeze or release gate change? `yes/no`

## Decisions

- 

## Follow-ups

- [ ] Follow-up action:
  - Owner:
  - Due:
"""
        return IssuePayload(title=title, body=body, labels=labels)

    raise ValueError(f"unsupported kind: {kind}")


class GitHubClient:
    def __init__(self, token: str, repo: str) -> None:
        if "/" not in repo:
            raise ValueError(f"repo must be in owner/name format, got {repo!r}")
        self.base = "https://api.github.com"
        self.token = token
        self.repo = repo
        self.owner, self.name = repo.split("/", 1)

    def _request(self, method: str, url: str, payload: dict | None = None) -> tuple[object, dict[str, str]]:
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            method=method,
            data=data,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "cpamm-lean-cadence-automation",
            },
        )
        with urllib.request.urlopen(request) as response:
            raw = response.read()
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
            headers = {k: v for (k, v) in response.headers.items()}
            return parsed, headers

    def _api(self, method: str, path: str, payload: dict | None = None) -> tuple[object, dict[str, str]]:
        return self._request(method, f"{self.base}{path}", payload)

    def ensure_label(self, label: str) -> None:
        color, description = LABEL_DEFINITIONS[label]
        encoded = urllib.parse.quote(label, safe="")
        path = f"/repos/{self.owner}/{self.name}/labels/{encoded}"
        try:
            self._api("GET", path)
            return
        except urllib.error.HTTPError as err:
            if err.code != 404:
                raise
        self._api(
            "POST",
            f"/repos/{self.owner}/{self.name}/labels",
            {"name": label, "color": color, "description": description},
        )

    def list_open_issues(self) -> list[dict]:
        issues: list[dict] = []
        url = f"{self.base}/repos/{self.owner}/{self.name}/issues?state=open&per_page=100"
        while url:
            data, headers = self._request("GET", url)
            if not isinstance(data, list):
                break
            issues.extend(data)
            url = next_link(headers.get("Link"))
        return issues

    def create_issue(self, payload: IssuePayload) -> dict:
        data, _ = self._api(
            "POST",
            f"/repos/{self.owner}/{self.name}/issues",
            {
                "title": payload.title,
                "body": payload.body,
                "labels": payload.labels,
            },
        )
        if not isinstance(data, dict):
            raise RuntimeError("unexpected API response when creating issue")
        return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=["kpi", "risk"], help="Issue type to create.")
    parser.add_argument(
        "--reference-date",
        default=None,
        help="Date for title/body window in YYYY-MM-DD (default: today UTC on runner).",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="Repository in owner/name format (default: env GITHUB_REPOSITORY).",
    )
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Environment variable name containing a GitHub token (default: GITHUB_TOKEN).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print payload JSON and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ref = parse_ref_date(args.reference_date)
    payload = build_payload(args.kind, ref)

    if args.dry_run:
        print(
            json.dumps(
                {"title": payload.title, "labels": payload.labels, "body": payload.body},
                indent=2,
            )
        )
        return 0

    token = os.environ.get(args.token_env, "")
    if not token:
        raise ValueError(f"missing token in env var: {args.token_env}")
    if not args.repo:
        raise ValueError("missing repo (pass --repo or set GITHUB_REPOSITORY)")

    client = GitHubClient(token=token, repo=args.repo)
    for label in payload.labels:
        client.ensure_label(label)

    open_issues = client.list_open_issues()
    for issue in open_issues:
        if issue.get("pull_request"):
            continue
        if issue.get("title") == payload.title:
            print(f"issue already exists, skipping: {payload.title}")
            return 0

    created = client.create_issue(payload)
    print(f"created issue #{created.get('number')}: {created.get('html_url')}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f"error: {err}")
        raise SystemExit(1)
