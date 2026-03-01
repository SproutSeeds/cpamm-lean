# Evidence Portal

## Purpose

The evidence portal is the client-facing workspace for a verification engagement.
It centralizes status, milestone progress, assumptions, risks, findings, and artifact access in one place.

## What Clients See

1. Engagement snapshot
- Client/protocol, owner, engagement window, and current status.

2. Gate status
- Formal, tests, security, and CI gate state in one status table.

3. Milestones and next actions
- Delivery timeline and owner-assigned next steps.

4. Artifact inventory
- Commercial package and technical review package file lists.
- Checksum evidence when `SHA256SUMS` is present.

5. Assumptions, risks, and findings
- Explicit boundaries and active mitigations.

## Generated Pages

`scripts/evidence_portal.py` generates:

1. `INDEX.md`
2. `STATUS.md`
3. `ARTIFACTS.md`
4. `ASSUMPTIONS_RISKS.md`
5. `FINDINGS.md`
6. `ACCESS.md`
7. `MANIFEST.json`

## Input Contract

Use `strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json` as the source template.

Required fields:
- `engagement_id`
- `client_name`
- `protocol_name`
- `engagement_type`
- `status`
- `owner`

`engagement_id` must be slug-like (`a-z`, `0-9`, `.`, `_`, `-`).

## Generation

```bash
python3 scripts/evidence_portal.py \
  --input strategy/private/portals/example.json \
  --commercial-package-dir artifacts/commercial-review-package \
  --review-package-dir artifacts/review-package \
  --portal-dir strategy/private/portals/example-protocol-a-2026q1 \
  --copy-artifacts
```

## Packaging Integration

`scripts/commercial_review_package.sh` supports:
- `--portal-input <path>`
- `--portal-dir <path>`

When provided, it generates `evidence-portal/` as part of the package output by default.
