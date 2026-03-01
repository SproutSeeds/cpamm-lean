# CPAMM Lean

[![CI](https://github.com/SproutSeeds/cpamm-lean/actions/workflows/ci.yml/badge.svg)](https://github.com/SproutSeeds/cpamm-lean/actions/workflows/ci.yml)

Formally verified constant-product AMM artifact:
- Lean 4 model and proofs over rationals (`CPAMM/*.lean`)
- Solidity implementation (`solidity/src/CPAMM.sol`)
- ERC20-backed Solidity extension (`solidity/src/CPAMMTokenized.sol`)
- Foundry tests (`solidity/test/CPAMM.t.sol`)
- Refinement layers from Solidity/tokenized storage relations to Lean transitions

## Capability Map

| Capability | Lean Proof Status | Test Status | Notes |
|---|---|---|---|
| Core CPAMM arithmetic-state refinement (`CPAMM.sol`) | Fully proved | Differential + invariant + unit/fuzz | Main formal artifact |
| Tokenized reserve-sync + projection simulation | Proved under exact-transfer assumptions | Integration + adversarial matrix | `CPAMM/TokenizedRefinement.lean` |
| Token behavior taxonomy / assumption boundaries | Formalized (classification + non-exact lemmas + sync-break witness) | Adversarial rejection tests | `CPAMM/TokenizedBehavior.lean` |
| Non-standard token composability (rebasing/FoT/inflationary) | Explicitly outside supported proof envelope | Explicitly rejected at runtime | See token compatibility docs |

## Pinned Toolchain

- Lean: `leanprover/lean4:v4.26.0` (`lean-toolchain`)
- Solidity compiler: `0.8.30` (exact pragma + `foundry.toml`)
- Foundry (CI): `1.5.1`
- Slither: `0.11.4` (`scripts/security/slither.sh`)

## Quick Start

Run full reproduction (Lean + Solidity):

```bash
./scripts/repro.sh
```

Generate a single reviewer bundle (logs, JSON, SARIF, LCOV, checksums):

```bash
./scripts/review_package.sh
```

## Commercialization

Business and execution playbooks for the highest-EV path are in `strategy/`:
- [`strategy/HIGHEST_EV_PATH.md`](strategy/HIGHEST_EV_PATH.md)
- [`strategy/EVIDENCE_PORTAL.md`](strategy/EVIDENCE_PORTAL.md)
- [`strategy/OFFER_AND_GTM.md`](strategy/OFFER_AND_GTM.md)
- [`strategy/REVENUE_MODEL.md`](strategy/REVENUE_MODEL.md)
- [`strategy/EXECUTION_90_DAYS.md`](strategy/EXECUTION_90_DAYS.md)
- [`strategy/KPI_SCOREBOARD.md`](strategy/KPI_SCOREBOARD.md)
- [`strategy/OPERATING_CADENCE.md`](strategy/OPERATING_CADENCE.md)
- [`strategy/LEGAL_COMPLIANCE_US.md`](strategy/LEGAL_COMPLIANCE_US.md)
- [`strategy/FUNDRAISING_AND_DATA_ROOM.md`](strategy/FUNDRAISING_AND_DATA_ROOM.md)
- [`strategy/RISK_REGISTER.md`](strategy/RISK_REGISTER.md)

Execution templates and trackers are in:
- [`strategy/assets/README.md`](strategy/assets/README.md)
- [`strategy/assets/crm/CRM_SCHEMA.md`](strategy/assets/crm/CRM_SCHEMA.md)
- [`strategy/assets/crm/PIPELINE_TEMPLATE.csv`](strategy/assets/crm/PIPELINE_TEMPLATE.csv)
- [`strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv`](strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv)
- [`strategy/assets/ops/CADENCE_AUTOMATION_CONFIG.md`](strategy/assets/ops/CADENCE_AUTOMATION_CONFIG.md)
- [`strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json`](strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json)
- [`strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json`](strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json)

Generate weekly business dashboard from trackers:

```bash
mkdir -p strategy/private
cp strategy/assets/crm/PIPELINE_TEMPLATE.csv strategy/private/PIPELINE.csv
cp strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv strategy/private/KPI_TRACKER.csv

python3 scripts/strategy_dashboard.py \
  --pipeline strategy/private/PIPELINE.csv \
  --kpi strategy/private/KPI_TRACKER.csv \
  --out reports/WEEKLY_DASHBOARD.md
```

Generate proposal/SOW deal packs from JSON input:

```bash
mkdir -p strategy/private/deals
cp strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json strategy/private/deals/example.json

python3 scripts/deal_pack.py \
  --input strategy/private/deals/example.json \
  --include-acceptance-template
```

Default output path is `strategy/private/generated/<deal_id>/`.

Generate pipeline health scoring + close-horizon forecast:

```bash
python3 scripts/pipeline_health.py \
  --pipeline strategy/private/PIPELINE.csv \
  --out reports/PIPELINE_HEALTH.md
```

Generate a prioritized outbound action queue from the pipeline:

```bash
python3 scripts/outbound_focus.py \
  --pipeline strategy/private/PIPELINE.csv \
  --as-of 2026-03-01 \
  --out reports/OUTBOUND_FOCUS.md \
  --csv-out reports/OUTBOUND_FOCUS.csv
```

Evaluate outbound SLA hygiene (overdue/missing/stale ratios):

```bash
python3 scripts/outbound_sla_gate.py \
  --pipeline strategy/private/PIPELINE.csv \
  --as-of 2026-03-01 \
  --out reports/OUTBOUND_SLA.md \
  --json-out reports/OUTBOUND_SLA.json \
  --strict
```

Validate commercialization operating data (pipeline/KPI/deal input):

```bash
python3 scripts/validate_strategy_data.py \
  --pipeline strategy/private/PIPELINE.csv \
  --kpi strategy/private/KPI_TRACKER.csv \
  --deal-input strategy/private/deals/example.json \
  --portal-input strategy/private/portals/example.json \
  --case-study-input strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json
```

Generate a sanitized case-study package:

```bash
mkdir -p strategy/private/case-studies
cp strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json strategy/private/case-studies/example.json

python3 scripts/case_study_pack.py \
  --input strategy/private/case-studies/example.json
```

Generate a portfolio case-study index + rollup:

```bash
python3 scripts/case_study_index.py \
  --inputs strategy/private/case-studies/example.json \
  --out reports/CASE_STUDIES_INDEX.md \
  --json-out reports/CASE_STUDIES_ROLLUP.json
```

Generate a commercialization review package (dashboard + pipeline health + optional deal pack + optional portal):

```bash
./scripts/commercial_review_package.sh \
  --pipeline strategy/private/PIPELINE.csv \
  --kpi strategy/private/KPI_TRACKER.csv \
  --deal-input strategy/private/deals/example.json \
  --portal-input strategy/private/portals/example.json \
  --case-study-input strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json \
  --as-of 2026-03-01
```

The package now includes outbound execution artifacts:
- `OUTBOUND_FOCUS.md`
- `OUTBOUND_FOCUS.csv`
- `OUTBOUND_SLA.md`
- `OUTBOUND_SLA.json`
and optional `case-study/` output when `--case-study-input` is provided.
When case-study input is provided, it also includes:
- `CASE_STUDIES_INDEX.md`
- `CASE_STUDIES_ROLLUP.json`

This writes a verifiable bundle under `artifacts/commercial-review-package-<utcstamp>/`
plus a `.tar.gz` archive.

Generate an evidence portal for a specific client engagement:

```bash
python3 scripts/evidence_portal.py \
  --input strategy/private/portals/example.json \
  --commercial-package-dir artifacts/commercial-review-package \
  --review-package-dir artifacts/review-package \
  --portal-dir strategy/private/portals/example-protocol-a-2026q1 \
  --copy-artifacts
```

Operating cadence issue templates are now included in:
- `.github/ISSUE_TEMPLATE/weekly-kpi-review.md`
- `.github/ISSUE_TEMPLATE/risk-register-review.md`

Recurring cadence issue creation is automated in:
- `.github/workflows/operating-cadence.yml`
- Weekly KPI issue schedule: Mondays `14:00 UTC`
- Monthly risk issue schedule: day `1` at `15:00 UTC`
- Manual runs are supported via `workflow_dispatch` with optional `reference_date`.
- Optional assignee routing via repo vars:
  - `CADENCE_KPI_ASSIGNEES`
  - `CADENCE_RISK_ASSIGNEES`
- Optional webhook notification via secret:
  - `CADENCE_NOTIFY_WEBHOOK_URL`
- Optional KPI outbound SLA threshold overrides via repo vars:
  - `CADENCE_MAX_OVERDUE_RATIO`
  - `CADENCE_MAX_MISSING_ACTION_RATIO`
  - `CADENCE_MAX_STALE_RATIO`
- Optional strict-fail toggle for KPI SLA breaches:
  - `CADENCE_OUTBOUND_SLA_STRICT` (`true` to fail workflow on breach)
- KPI run also generates and uploads outbound digest artifacts, and posts a digest comment on the cadence issue thread.

Evidence portal publishing automation:
- `.github/workflows/evidence-portal-publish.yml`
- Weekly scheduled portal refresh and manual dispatch support.

Case-study publishing automation:
- `.github/workflows/case-study-publish.yml`
- Weekly scheduled case-study artifact refresh and manual dispatch support.

## Security Validation

Run differential fuzzing + baseline test suite:

```bash
cd solidity
~/.foundry/bin/forge test
```

Differential coverage includes swap/add/remove checks plus a mixed-operation stateful shadow-model fuzz test.
The suite also includes a Foundry invariant campaign (`CPAMM.Invariant.t.sol`) with a two-actor stateful handler.
An ERC20-backed integration suite (`CPAMM.Tokenized.t.sol`) checks reserve/token-balance consistency and fee-on-transfer rejection.
An adversarial token matrix suite (`CPAMM.Tokenized.Adversarial.t.sol`) verifies explicit rejection behavior for unsupported token classes.

Run Slither static analysis:

```bash
./scripts/security/slither.sh
```

See triaged findings in [`security/SECURITY_VALIDATION.md`](security/SECURITY_VALIDATION.md).
Token support/rejection policy is documented in [`security/TOKEN_COMPATIBILITY.md`](security/TOKEN_COMPATIBILITY.md).
Assumption-to-test coupling is tracked in [`reports/ASSUMPTION_TEST_MATRIX.md`](reports/ASSUMPTION_TEST_MATRIX.md).
External reviewer assumptions and scope boundaries are summarized in [`security/AUDIT_README.md`](security/AUDIT_README.md).
CI runs this gate across `solidity/src` and fails on any non-triaged detector findings.

Each CI run also publishes artifacts for review:
- Lean cache/build logs
- Forge test log + JSON report + coverage output (`lcov.info`)
- Slither log + SARIF report
- Unified review bundle (`review-package` artifact) generated by `scripts/review_package.sh`
- Commercial review bundle (`commercial-review-package` artifact) generated from template/synthetic operating data via `scripts/commercial_review_package.sh`
- Outbound execution artifacts inside commercial package (`OUTBOUND_FOCUS.md`, `OUTBOUND_FOCUS.csv`, `OUTBOUND_SLA.md`, `OUTBOUND_SLA.json`)
- Dedicated evidence portal publication artifact (`evidence-portal`) via `.github/workflows/evidence-portal-publish.yml`
- Dedicated case-study publication artifact (`case-study-publish`) via `.github/workflows/case-study-publish.yml`
- KPI cadence digest artifact (`kpi-outbound-digest`) via `.github/workflows/operating-cadence.yml`

CI enforcement now includes:
- pinned Lean action SHA (`leanprover/lean-action@c544e896...`)
- coverage threshold gates for:
  - `src/CPAMM.sol`
  - `src/CPAMMTokenized.sol`
  (lines/statements must remain `100%`; branch coverage has floor gates)
- SARIF upload to GitHub Security for Slither findings
- cached/retried Slither toolchain setup in CI for stability
- assumption/test matrix validation gate (`scripts/validate_assumption_matrix.py`)
- outbound SLA strict gate over template data (`scripts/outbound_sla_gate.py`)

## What Is Proved

- State validity invariants are preserved across add/remove/swap relations
- LP accounting consistency is preserved for add/remove liquidity
- Constant product is preserved at zero fee and nondecreasing with positive fee
- Output is bounded by reserves
- Integer floor-division bounds and reserve-positivity rounding safety
- Full-withdrawal terminal boundary at abstract level:
  - `terminal_preserved_removeLiquidityTerminal`
  - `validOrTerminal_preserved_removeLiquidityBoundary`
- Refinement simulation theorems for:
  - `sim_swapXforY`
  - `sim_swapYforX`
  - `sim_addLiquidity`
  - `sim_addLiquidity_bootstrap`
  - `sim_removeLiquidity`
- Tokenized refinement theorems for:
  - reserve/token-balance sync preservation per operation
  - projection from tokenized steps to arithmetic Solidity relations
  - trace-level validity+sync preservation under exact-transfer assumptions
- Trace-level Solidity validity preservation for arbitrary finite step sequences

Full theorem inventory and assumptions are in [`VERIFICATION.md`](VERIFICATION.md).
Tokenized extension scope and the formalization roadmap are in [`VERIFICATION_TOKENIZED.md`](VERIFICATION_TOKENIZED.md).
Assumption/test linkage for the tokenized path is summarized in [`reports/ASSUMPTION_TEST_MATRIX.md`](reports/ASSUMPTION_TEST_MATRIX.md).

## Repository Layout

```text
CPAMM/
  State.lean
  Transitions.lean
  Invariants.lean
  Economics.lean
  Rounding.lean
  Refinement.lean
  TokenizedRefinement.lean
  TokenizedBehavior.lean
solidity/
  src/CPAMM.sol
  src/CPAMMTokenized.sol
  test/CPAMM.t.sol
  test/CPAMM.Tokenized.t.sol
.github/workflows/ci.yml
VERIFICATION.md
VERIFICATION_TOKENIZED.md
scripts/repro.sh
```

## Notes On Scope

This is a minimal verifiable AMM core artifact (no oracle/TWAP/governance/upgrade logic).
Refinement for swaps and liquidity operations is modeled with integer-floor arithmetic and explicit ±1 bounds against exact rational quantities, documented in [`VERIFICATION.md`](VERIFICATION.md).
The Solidity contract intentionally enforces `shares < totalSupply` on `removeLiquidity`; the `dL = L` full-withdrawal case is modeled and proved only at the abstract Lean boundary layer.
`CPAMMTokenized.sol` extends this with real ERC20 transfers and reserve/balance checks.
`CPAMM/TokenizedRefinement.lean` now formalizes reserve/balance sync and projection simulation under explicit exact-transfer assumptions (documented in [`VERIFICATION_TOKENIZED.md`](VERIFICATION_TOKENIZED.md)).
