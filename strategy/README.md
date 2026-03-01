# Strategy Boundary

This repository is public by design for technical verification evidence.

## Public In This Repo

- Lean proofs, Solidity contracts, tests, and security validation artifacts.
- Sanitized templates under `strategy/assets/` for reproducible process scaffolding.
- Public-facing evidence portal design (`strategy/EVIDENCE_PORTAL.md`).

## Private By Default

- Commercial strategy playbooks (GTM, pricing, outbound execution, pipeline internals).
- Live pipeline/KPI/deal/account data.
- Client-specific operating cadence notes and revenue planning docs.

Keep private materials under `strategy/private/` and private report outputs under `reports/`.
Both are gitignored in this repository.

## Recommended Working Pattern

1. Copy template inputs from `strategy/assets/` into `strategy/private/`.
2. Run automation scripts against private copies.
3. Publish only sanitized technical/evidence artifacts intended for external review.

## Optional Commercial Automation In CI

Commercial workflow jobs are opt-in and should be enabled only in private/forked environments by setting:

- `ENABLE_COMMERCIAL_AUTOMATION=true` (repository variable)

Without this variable, public CI runs technical verification gates only.
