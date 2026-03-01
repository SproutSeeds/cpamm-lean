# Protocol Handoff Checklist

Use this checklist when RigidityCore hands a confirmed lane to cpamm-lean.

## Gate Prerequisites (must all be true)

1. Contract replay determinism is established.
2. Audit dedup gate has no unresolved overlap.
3. Lane has measurable impact signal worth escalation.

If any item is false, Lean status is `DEFERRED`.

## Required Input Artifacts

1. `System.json` payload (schema `0.1`) for the scoped lane.
2. Handoff gate payload with:
- `handoff_id`
- `system_id`
- `finding_id`
- `lane_id`
- `gate` object (three booleans above)
- `evidence.replay_artifacts` (non-empty)
- `evidence.dedup_record`
- `evidence.impact_summary`
3. Explicit assumption and scope notes (what is modeled vs out of scope).
4. Replay command references or immutable evidence paths.

## cpamm-lean Intake Command

```bash
python3 scripts/intake_validate.py \
  --system-json <path-to-System.json> \
  --handoff-json <path-to-handoff.json> \
  --strict-gate
```

Optional report output:

```bash
python3 scripts/intake_validate.py \
  --system-json <path-to-System.json> \
  --handoff-json <path-to-handoff.json> \
  --strict-gate \
  --out artifacts/protocol-intake.md
```

## Template References

- Handoff process mapping: `PROTOCOL_TEMPLATE.md`
- Engagement scaffold: `Protocol/`
- Example intake payloads: `Protocol/examples/cpamm/`

## Cross-Repo Rehearsal

Run a strict-gate readiness rehearsal against live RigidityCore target models (Aave/Balancer examples):

```bash
./scripts/protocol_readiness_rehearsal.sh /Users/codymitchell/Documents/code/RigidityCore
```
