# Protocol Readiness Rehearsal

This report documents a strict-gate intake rehearsal from cpamm-lean against live RigidityCore target `System.json` payloads.

## Run Metadata

- run_utc: `2026-03-01T22:48:28Z`
- command:

```bash
./scripts/protocol_readiness_rehearsal.sh \
  /Users/codymitchell/Documents/code/RigidityCore \
  artifacts/protocol-readiness-rehearsal
```

## Targets Rehearsed

| Target | System Payload | Strict Gate | Result |
|---|---|---|---|
| `aave/session1` | `RigidityCore/targets/aave/session1/System.json` | `true` | PASS |
| `balancer/session1` | `RigidityCore/targets/balancer/session1/System.json` | `true` | PASS |

## Generated Packet

- `artifacts/protocol-readiness-rehearsal/READY_TO_PROVE_PACKET.md`
- `artifacts/protocol-readiness-rehearsal/aave_session1.HANDOFF_READY.json`
- `artifacts/protocol-readiness-rehearsal/aave_session1.protocol-intake.md`
- `artifacts/protocol-readiness-rehearsal/balancer_session1.HANDOFF_READY.json`
- `artifacts/protocol-readiness-rehearsal/balancer_session1.protocol-intake.md`

## Interpretation

The cpamm-lean intake gate can consume real RigidityCore protocol models and validate strict-gate handoff structure end-to-end before Lean engagement work begins.
