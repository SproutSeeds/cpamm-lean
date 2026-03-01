#!/usr/bin/env python3
"""Validate RigidityCore -> cpamm-lean protocol intake payloads."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_:-]{0,127}$")
DOMAIN_SET = {"amm", "sat", "generic"}
ROUNDING_TYPES = {"floor_div", "ceil_div", "mod", "clamp", "quantize", "other"}
INVARIANT_KINDS = {"safety", "economic", "consistency", "custom"}
ASSUMPTION_SCOPES = {"model", "implementation", "environment"}
CMP_OPS = {"==", "!=", "<", "<=", ">", ">="}
VALUE_TYPES = {"bool", "int", "nat", "string", "bytes", "decimal", "enum", "struct"}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json at {path}: {exc}") from None


def _is_id(value: Any) -> bool:
    return isinstance(value, str) and ID_RE.fullmatch(value) is not None


def _guard_validate(
    guard: Any,
    allowed_refs: set[str],
    where: str,
    errors: list[str],
) -> None:
    if not isinstance(guard, dict):
        errors.append(f"{where}: guard must be an object")
        return
    keys = set(guard.keys())
    if keys == {"true"}:
        if guard["true"] is not True:
            errors.append(f"{where}: `true` guard must be literal true")
        return
    if keys == {"and"}:
        val = guard["and"]
        if not isinstance(val, list) or not val:
            errors.append(f"{where}: `and` guard must be a non-empty list")
            return
        for idx, sub in enumerate(val):
            _guard_validate(sub, allowed_refs, f"{where}.and[{idx}]", errors)
        return
    if keys == {"or"}:
        val = guard["or"]
        if not isinstance(val, list) or not val:
            errors.append(f"{where}: `or` guard must be a non-empty list")
            return
        for idx, sub in enumerate(val):
            _guard_validate(sub, allowed_refs, f"{where}.or[{idx}]", errors)
        return
    if keys == {"not"}:
        _guard_validate(guard["not"], allowed_refs, f"{where}.not", errors)
        return
    if keys == {"cmp"}:
        cmp_obj = guard["cmp"]
        if not isinstance(cmp_obj, dict):
            errors.append(f"{where}: `cmp` must be an object")
            return
        for req in ("op", "left", "right"):
            if req not in cmp_obj:
                errors.append(f"{where}: cmp missing `{req}`")
        if "op" in cmp_obj and cmp_obj["op"] not in CMP_OPS:
            errors.append(f"{where}: cmp op must be one of {sorted(CMP_OPS)}")
        _expr_validate(cmp_obj.get("left"), allowed_refs, f"{where}.cmp.left", errors)
        _expr_validate(cmp_obj.get("right"), allowed_refs, f"{where}.cmp.right", errors)
        return
    errors.append(f"{where}: unsupported guard shape (allowed: true/and/or/not/cmp)")


def _expr_validate(expr: Any, allowed_refs: set[str], where: str, errors: list[str]) -> None:
    if not isinstance(expr, dict):
        errors.append(f"{where}: expression must be an object")
        return
    keys = set(expr.keys())
    if keys == {"var"}:
        var_name = expr["var"]
        if not isinstance(var_name, str):
            errors.append(f"{where}: `var` must be a string")
            return
        if var_name not in allowed_refs:
            errors.append(f"{where}: unknown variable reference `{var_name}`")
        return
    if keys == {"const", "type"}:
        if expr["type"] not in VALUE_TYPES:
            errors.append(f"{where}: const type must be one of {sorted(VALUE_TYPES)}")
        return
    errors.append(f"{where}: expression must be either {{var}} or {{const,type}}")


def _validate_system(system: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(system, dict):
        errors.append("system: top-level must be an object")
        return {}

    required = ("schema_version", "system_id", "name", "domain", "state_vars", "transitions", "invariants")
    for key in required:
        if key not in system:
            errors.append(f"system: missing required field `{key}`")

    if system.get("schema_version") != "0.1":
        errors.append("system: `schema_version` must be \"0.1\"")
    if not _is_id(system.get("system_id")):
        errors.append("system: `system_id` must match id format")
    if not isinstance(system.get("name"), str) or not system.get("name"):
        errors.append("system: `name` must be a non-empty string")
    if system.get("domain") not in DOMAIN_SET:
        errors.append(f"system: `domain` must be one of {sorted(DOMAIN_SET)}")

    state_vars = system.get("state_vars", [])
    state_ids: list[str] = []
    if not isinstance(state_vars, list) or not state_vars:
        errors.append("system: `state_vars` must be a non-empty list")
    else:
        for idx, item in enumerate(state_vars):
            where = f"state_vars[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{where}: must be an object")
                continue
            if not _is_id(item.get("id")):
                errors.append(f"{where}: `id` is invalid")
            else:
                state_ids.append(item["id"])
            if item.get("type") not in VALUE_TYPES:
                errors.append(f"{where}: `type` must be one of {sorted(VALUE_TYPES)}")
    if len(state_ids) != len(set(state_ids)):
        errors.append("system: duplicate ids in `state_vars`")
    state_id_set = set(state_ids)

    parameters = system.get("parameters", [])
    param_ids: list[str] = []
    if parameters is not None:
        if not isinstance(parameters, list):
            errors.append("system: `parameters` must be a list when present")
        else:
            for idx, item in enumerate(parameters):
                where = f"parameters[{idx}]"
                if not isinstance(item, dict):
                    errors.append(f"{where}: must be an object")
                    continue
                if not _is_id(item.get("id")):
                    errors.append(f"{where}: `id` is invalid")
                else:
                    param_ids.append(item["id"])
                if item.get("type") not in VALUE_TYPES:
                    errors.append(f"{where}: `type` must be one of {sorted(VALUE_TYPES)}")
                if "value" not in item:
                    errors.append(f"{where}: missing `value`")
    if len(param_ids) != len(set(param_ids)):
        errors.append("system: duplicate ids in `parameters`")
    overlap = state_id_set.intersection(param_ids)
    if overlap:
        errors.append(f"system: parameter ids overlap state var ids: {sorted(overlap)}")

    transitions = system.get("transitions", [])
    transition_ids: list[str] = []
    if not isinstance(transitions, list) or not transitions:
        errors.append("system: `transitions` must be a non-empty list")
    else:
        for t_idx, trans in enumerate(transitions):
            t_where = f"transitions[{t_idx}]"
            if not isinstance(trans, dict):
                errors.append(f"{t_where}: must be an object")
                continue
            for req in ("id", "name", "inputs", "reads", "writes", "guard", "update_model"):
                if req not in trans:
                    errors.append(f"{t_where}: missing `{req}`")
            tid = trans.get("id")
            if not _is_id(tid):
                errors.append(f"{t_where}: invalid transition id")
            else:
                transition_ids.append(tid)
            if not isinstance(trans.get("name"), str) or not trans.get("name"):
                errors.append(f"{t_where}: `name` must be non-empty string")

            inputs = trans.get("inputs", [])
            input_ids: list[str] = []
            if not isinstance(inputs, list):
                errors.append(f"{t_where}: `inputs` must be a list")
                inputs = []
            for i_idx, inp in enumerate(inputs):
                i_where = f"{t_where}.inputs[{i_idx}]"
                if not isinstance(inp, dict):
                    errors.append(f"{i_where}: must be an object")
                    continue
                if not _is_id(inp.get("id")):
                    errors.append(f"{i_where}: invalid input id")
                else:
                    input_ids.append(inp["id"])
                if inp.get("type") not in VALUE_TYPES:
                    errors.append(f"{i_where}: invalid input type")
            if len(input_ids) != len(set(input_ids)):
                errors.append(f"{t_where}: duplicate input ids")

            reads = trans.get("reads", [])
            writes = trans.get("writes", [])
            if not isinstance(reads, list):
                errors.append(f"{t_where}: `reads` must be a list")
                reads = []
            if not isinstance(writes, list) or not writes:
                errors.append(f"{t_where}: `writes` must be a non-empty list")
                writes = []
            for field, values in (("reads", reads), ("writes", writes)):
                for name in values:
                    if not isinstance(name, str) or name not in state_id_set:
                        errors.append(f"{t_where}: `{field}` contains unknown state var `{name}`")

            allowed_refs = set(input_ids).union(state_id_set)
            _guard_validate(trans.get("guard"), allowed_refs, f"{t_where}.guard", errors)

            update = trans.get("update_model")
            if not isinstance(update, dict):
                errors.append(f"{t_where}.update_model: must be an object")
                continue
            if update.get("kind") != "assignment_set":
                errors.append(f"{t_where}.update_model.kind: must be `assignment_set`")

            assignments = update.get("assignments", [])
            if not isinstance(assignments, list) or not assignments:
                errors.append(f"{t_where}.update_model.assignments: must be non-empty list")
                assignments = []
            for a_idx, assignment in enumerate(assignments):
                a_where = f"{t_where}.update_model.assignments[{a_idx}]"
                if not isinstance(assignment, dict):
                    errors.append(f"{a_where}: must be an object")
                    continue
                target = assignment.get("target")
                if not isinstance(target, str) or target not in state_id_set:
                    errors.append(f"{a_where}: `target` must reference known state var")
                source_deps = assignment.get("source_deps")
                if not isinstance(source_deps, list) or not source_deps:
                    errors.append(f"{a_where}: `source_deps` must be non-empty list")
                    source_deps = []
                for dep in source_deps:
                    if not isinstance(dep, str) or dep not in allowed_refs:
                        errors.append(f"{a_where}: unknown source dep `{dep}`")

            rounding = update.get("rounding", [])
            if rounding is not None:
                if not isinstance(rounding, list):
                    errors.append(f"{t_where}.update_model.rounding: must be a list")
                    rounding = []
                for r_idx, round_item in enumerate(rounding):
                    r_where = f"{t_where}.update_model.rounding[{r_idx}]"
                    if not isinstance(round_item, dict):
                        errors.append(f"{r_where}: must be an object")
                        continue
                    if not _is_id(round_item.get("id")):
                        errors.append(f"{r_where}: invalid rounding id")
                    if round_item.get("type") not in ROUNDING_TYPES:
                        errors.append(f"{r_where}: invalid rounding type")
                    deps = round_item.get("depends_on")
                    if not isinstance(deps, list):
                        errors.append(f"{r_where}: `depends_on` must be a list")
                        deps = []
                    for dep in deps:
                        if not isinstance(dep, str) or dep not in allowed_refs:
                            errors.append(f"{r_where}: unknown depends_on dep `{dep}`")

    if len(transition_ids) != len(set(transition_ids)):
        errors.append("system: duplicate transition ids in `transitions`")

    invariants = system.get("invariants", [])
    inv_ids: list[str] = []
    if not isinstance(invariants, list) or not invariants:
        errors.append("system: `invariants` must be a non-empty list")
    else:
        for idx, inv in enumerate(invariants):
            where = f"invariants[{idx}]"
            if not isinstance(inv, dict):
                errors.append(f"{where}: must be an object")
                continue
            if not _is_id(inv.get("id")):
                errors.append(f"{where}: invalid invariant id")
            else:
                inv_ids.append(inv["id"])
            if not isinstance(inv.get("name"), str) or not inv.get("name"):
                errors.append(f"{where}: `name` must be non-empty string")
            if inv.get("kind") not in INVARIANT_KINDS:
                errors.append(f"{where}: `kind` must be one of {sorted(INVARIANT_KINDS)}")
            deps = inv.get("depends_on")
            if not isinstance(deps, list) or not deps:
                errors.append(f"{where}: `depends_on` must be non-empty list")
                deps = []
            for dep in deps:
                if not isinstance(dep, str) or dep not in state_id_set:
                    errors.append(f"{where}: unknown depends_on state var `{dep}`")
    if len(inv_ids) != len(set(inv_ids)):
        errors.append("system: duplicate invariant ids")

    assumptions = system.get("assumptions", [])
    if assumptions is not None:
        if not isinstance(assumptions, list):
            errors.append("system: `assumptions` must be a list when present")
        else:
            for idx, asm in enumerate(assumptions):
                where = f"assumptions[{idx}]"
                if not isinstance(asm, dict):
                    errors.append(f"{where}: must be an object")
                    continue
                if not _is_id(asm.get("id")):
                    errors.append(f"{where}: invalid assumption id")
                if not isinstance(asm.get("description"), str) or not asm.get("description"):
                    errors.append(f"{where}: `description` must be non-empty string")
                if asm.get("scope") not in ASSUMPTION_SCOPES:
                    errors.append(f"{where}: `scope` must be one of {sorted(ASSUMPTION_SCOPES)}")

    return {
        "system_id": system.get("system_id"),
        "state_var_count": len(state_ids),
        "transition_count": len(transitions) if isinstance(transitions, list) else 0,
        "invariant_count": len(invariants) if isinstance(invariants, list) else 0,
    }


def _validate_handoff(
    handoff: Any,
    strict_gate: bool,
    system_id: str | None,
    errors: list[str],
) -> dict[str, Any]:
    if not isinstance(handoff, dict):
        errors.append("handoff: top-level must be an object")
        return {}

    required = ("schema_version", "handoff_id", "system_id", "finding_id", "lane_id", "gate", "evidence")
    for key in required:
        if key not in handoff:
            errors.append(f"handoff: missing required field `{key}`")

    if handoff.get("schema_version") != "0.1":
        errors.append("handoff: `schema_version` must be \"0.1\"")
    for key in ("handoff_id", "system_id", "finding_id", "lane_id"):
        if not _is_id(handoff.get(key)):
            errors.append(f"handoff: `{key}` must match id format")

    if system_id and isinstance(handoff.get("system_id"), str) and handoff["system_id"] != system_id:
        errors.append(
            "handoff: `system_id` mismatch between handoff and system payload "
            f"({handoff['system_id']} != {system_id})"
        )

    gate = handoff.get("gate")
    gate_keys = (
        "contract_replay_determinism_established",
        "audit_dedup_clear",
        "measurable_impact_signal",
    )
    if not isinstance(gate, dict):
        errors.append("handoff: `gate` must be an object")
        gate = {}
    for key in gate_keys:
        if key not in gate:
            errors.append(f"handoff.gate: missing `{key}`")
        elif not isinstance(gate[key], bool):
            errors.append(f"handoff.gate.{key}: must be boolean")
        elif strict_gate and gate[key] is not True:
            errors.append(f"handoff.gate.{key}: strict gate requires value `true`")

    evidence = handoff.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("handoff: `evidence` must be an object")
    else:
        replay = evidence.get("replay_artifacts")
        if not isinstance(replay, list) or not replay:
            errors.append("handoff.evidence.replay_artifacts: must be non-empty list")
        else:
            for idx, item in enumerate(replay):
                if not isinstance(item, str) or not item:
                    errors.append(f"handoff.evidence.replay_artifacts[{idx}]: must be non-empty string")
        for key in ("dedup_record", "impact_summary"):
            value = evidence.get(key)
            if not isinstance(value, str) or not value:
                errors.append(f"handoff.evidence.{key}: must be non-empty string")

    assumptions = handoff.get("assumptions")
    if assumptions is not None and not isinstance(assumptions, list):
        errors.append("handoff: `assumptions` must be a list when present")

    return {"strict_gate": strict_gate, "gate": gate}


def _write_report(
    out_path: Path,
    system_path: Path,
    handoff_path: Path | None,
    strict_gate: bool,
    system_summary: dict[str, Any],
    handoff_summary: dict[str, Any] | None,
) -> None:
    lines: list[str] = []
    lines.append("# Protocol Intake Validation")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- System payload: `{system_path}`")
    lines.append(f"- Handoff payload: `{handoff_path}`" if handoff_path else "- Handoff payload: (not provided)")
    lines.append(f"- Strict gate mode: `{strict_gate}`")
    lines.append("")
    lines.append("## System Summary")
    lines.append("")
    lines.append(f"- system_id: `{system_summary.get('system_id', 'unknown')}`")
    lines.append(f"- state_vars: `{system_summary.get('state_var_count', 0)}`")
    lines.append(f"- transitions: `{system_summary.get('transition_count', 0)}`")
    lines.append(f"- invariants: `{system_summary.get('invariant_count', 0)}`")
    if handoff_summary is not None:
        lines.append("")
        lines.append("## Gate Summary")
        lines.append("")
        gate = handoff_summary.get("gate", {})
        for key in (
            "contract_replay_determinism_established",
            "audit_dedup_clear",
            "measurable_impact_signal",
        ):
            value = gate.get(key)
            lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append("- Status: PASS")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-json", type=Path, required=True, help="Path to RigidityCore System.json payload.")
    parser.add_argument("--handoff-json", type=Path, help="Path to handoff gate payload JSON.")
    parser.add_argument("--strict-gate", action="store_true", help="Require all gate booleans to be true.")
    parser.add_argument("--out", type=Path, help="Optional markdown output report path.")
    args = parser.parse_args()

    errors: list[str] = []
    try:
        system_payload = _load_json(args.system_json)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    system_summary = _validate_system(system_payload, errors)

    handoff_summary: dict[str, Any] | None = None
    if args.handoff_json is not None:
        try:
            handoff_payload = _load_json(args.handoff_json)
        except ValueError as exc:
            print(f"error: {exc}")
            return 1
        handoff_summary = _validate_handoff(
            handoff_payload,
            strict_gate=args.strict_gate,
            system_id=system_summary.get("system_id"),
            errors=errors,
        )

    if errors:
        print("protocol intake validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    if args.out is not None:
        _write_report(
            out_path=args.out,
            system_path=args.system_json,
            handoff_path=args.handoff_json,
            strict_gate=args.strict_gate,
            system_summary=system_summary,
            handoff_summary=handoff_summary,
        )
        print(f"wrote intake report: {args.out}")

    print(
        "protocol intake validation passed: "
        f"system_id={system_summary.get('system_id')} "
        f"(strict_gate={args.strict_gate}, handoff={'yes' if args.handoff_json else 'no'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
