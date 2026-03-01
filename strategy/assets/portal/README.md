# Evidence Portal Inputs

This folder contains input templates for generating client-facing evidence portals.

## Files

- `PORTAL_INPUT_TEMPLATE.json`

## Usage

```bash
mkdir -p strategy/private/portals
cp strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json strategy/private/portals/example.json

python3 scripts/evidence_portal.py \
  --input strategy/private/portals/example.json \
  --commercial-package-dir artifacts/commercial-review-package \
  --portal-dir strategy/private/portals/example-protocol-a-2026q1 \
  --copy-artifacts
```

## Notes

- Keep real client portal inputs under `strategy/private/` (ignored by git).
- `engagement_id` should be slug-like (`a-z`, `0-9`, `.`, `_`, `-`).
