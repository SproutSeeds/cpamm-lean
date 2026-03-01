#!/usr/bin/env python3
"""Generate proposal/SOW deal documents from repository templates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return slug or "deal"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing input file: {path}")
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("deal input root must be a JSON object")
    return data


def markdown_list(items: list[Any]) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return "- (none specified)"
    return "\n".join(f"- {item}" for item in cleaned)


def normalize_mapping(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, list):
            out[key] = markdown_list(value)
        elif value is None:
            out[key] = ""
        else:
            out[key] = str(value)
    return out


def template_keys(text: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(text))


def render_template(template_text: str, mapping: dict[str, str], template_name: str) -> str:
    keys = template_keys(template_text)
    missing = sorted(keys - set(mapping.keys()))
    if missing:
        missing_csv = ", ".join(missing)
        raise ValueError(f"{template_name} missing required fields: {missing_csv}")

    def repl(match: re.Match[str]) -> str:
        return mapping[match.group(1)]

    rendered = PLACEHOLDER_RE.sub(repl, template_text)
    unresolved = sorted(template_keys(rendered))
    if unresolved:
        unresolved_csv = ", ".join(unresolved)
        raise ValueError(f"{template_name} unresolved placeholders after render: {unresolved_csv}")
    return rendered


def load_section(data: dict[str, Any], name: str) -> dict[str, str]:
    section = data.get(name)
    if not isinstance(section, dict):
        raise ValueError(f"expected '{name}' to be a JSON object")
    return normalize_mapping(section)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def default_output_dir(input_data: dict[str, Any]) -> Path:
    raw_deal_id = str(input_data.get("deal_id", "")).strip()
    deal_id = slugify(raw_deal_id) if raw_deal_id else "deal"
    return Path("strategy/private/generated") / deal_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to JSON input (see strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json).",
    )
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=Path("strategy/assets/contracts"),
        help="Directory containing template markdown files.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory for rendered docs (default: strategy/private/generated/<deal_id>).",
    )
    parser.add_argument(
        "--include-acceptance-template",
        action="store_true",
        help="Also copy ACCEPTANCE_CRITERIA_TEMPLATE.md into output as ACCEPTANCE_CRITERIA.md.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = read_json(args.input)

    proposal_map = load_section(data, "proposal")
    sow_map = load_section(data, "sow")

    contracts_dir = args.contracts_dir
    proposal_template = (contracts_dir / "PROPOSAL_TEMPLATE.md").read_text(encoding="utf-8")
    sow_template = (contracts_dir / "SOW_TEMPLATE.md").read_text(encoding="utf-8")

    rendered_proposal = render_template(proposal_template, proposal_map, "PROPOSAL_TEMPLATE.md")
    rendered_sow = render_template(sow_template, sow_map, "SOW_TEMPLATE.md")

    out_dir = args.out_dir or default_output_dir(data)
    write_text(out_dir / "PROPOSAL.md", rendered_proposal)
    write_text(out_dir / "SOW.md", rendered_sow)

    if args.include_acceptance_template:
        acceptance_template_path = contracts_dir / "ACCEPTANCE_CRITERIA_TEMPLATE.md"
        acceptance_text = acceptance_template_path.read_text(encoding="utf-8")
        write_text(out_dir / "ACCEPTANCE_CRITERIA.md", acceptance_text)

    manifest = {
        "deal_id": str(data.get("deal_id", "")),
        "input_file": str(args.input),
        "output_dir": str(out_dir),
        "proposal_fields": sorted(proposal_map.keys()),
        "sow_fields": sorted(sow_map.keys()),
    }
    write_text(out_dir / "MANIFEST.json", json.dumps(manifest, indent=2) + "\n")

    print(f"generated deal pack: {out_dir}")
    print(f"- {out_dir / 'PROPOSAL.md'}")
    print(f"- {out_dir / 'SOW.md'}")
    if args.include_acceptance_template:
        print(f"- {out_dir / 'ACCEPTANCE_CRITERIA.md'}")
    print(f"- {out_dir / 'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
