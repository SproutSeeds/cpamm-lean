# Changelog

All notable changes to this project are documented in this file.

## Unreleased

- Added protocol intake validation gate:
  - `scripts/intake_validate.py` validates RigidityCore `System.json` payloads and handoff gate metadata.
  - strict-gate mode enforces all three Lean-start prerequisites.
- Added theorem inventory integrity gate:
  - `scripts/theorem_inventory.py` generates theorem inventory output and can check/repair `VERIFICATION.md` proven-theorems sync.
  - `scripts/validate_theorem_inventory.py` validates `VERIFICATION.md` theorem entries against actual `theorem` declarations in referenced Lean files.
  - validation now enforces bidirectional completeness by default (every listed theorem must exist, and every theorem in a documented Lean section must be listed).
  - optional listed-only mode is available via `--allow-incomplete`.
  - CI `lean` job now runs theorem-inventory sync + validation and publishes `artifacts/theorem-inventory-sync.log` and `artifacts/theorem-inventory-validation.log`.
  - `scripts/review_package.sh` now includes theorem-inventory sync/validation evidence in the reviewer bundle.
  - `VERIFICATION.md` theorem inventory now includes helper refinement theorems (`frac_mul_div_mono`, `inputEff_cast_le_exact`, `dyOutX_cast_le_dy_of_swap`, `dxOutY_cast_le_dy_of_swap`) to satisfy complete-mode coverage.
- Added protocol intake assets:
  - `PROTOCOL_HANDOFF_CHECKLIST.md`
  - `Protocol/examples/cpamm/System.json`
  - `Protocol/examples/cpamm/HANDOFF_READY.json`
- Added CI `protocol-intake` job in `.github/workflows/ci.yml` and attached intake artifact publication.
- Added protocol intake test coverage in `tests/test_protocol_intake.py`.
- Updated docs (`README.md`, `VERIFICATION.md`) with intake-gate commands and references.
- Added `scripts/protocol_readiness_rehearsal.sh` to run strict-gate intake rehearsal against live RigidityCore target models and emit ready-to-prove packets.
- Added readiness rehearsal report: `reports/PROTOCOL_READINESS_REHEARSAL.md`.
- Updated `scripts/protocol_readiness_rehearsal.sh` to use real RigidityCore `targets/*/HANDOFF_READY.json` payloads when present (fallback to generated rehearsal payloads otherwise).
- Closed remove-path output-divergence symmetry for tokenized recipient-fee semantics:
  - Added Lean theorem `reserveSync_and_removeLiquidityOutputDivergence_by_recipientFeePushY`.
  - Added adversarial test `test_outputFeeOnPoolTransfer_breaksObservedRemoveLiquidityOutputY`.
  - Updated verification/assumption/security docs with theorem/test linkage for both remove outputs.
- Added dedicated tokenized IO semantics module `CPAMM/TokenizedIOSemantics.lean`:
  - moved `ExactPullDelta`, `ExactPushDelta`, `RecipientObservedOutputExact`, and exact-pull extraction lemmas into a refinement-facing shared layer.
  - `CPAMM/TokenizedBehavior.lean` now imports the IO layer and focuses on behavior/adversarial proof obligations.
- Added `PROTOCOL_TEMPLATE.md` defining the RigidityCore-to-cpamm-lean handoff contract:
  - pipeline ownership split
  - `System.json` schema-to-Lean mapping table grounded in `spec/SPEC.md`
  - strict SUNFLOWER gate prerequisites
  - worked CPAMM `System.json` -> `CPAMM/Refinement.lean` mapping example
- Added `Protocol/` engagement scaffold:
  - `Protocol/README.md`
  - `Protocol/State.lean`
  - `Protocol/Refinement.lean` (intentional scaffold `sorry` placeholders)
  - `Protocol/Rounding.lean`
- Updated `VERIFICATION.md` with explicit two-repo pipeline positioning and Lean-start gate conditions.
- Updated `security/AUDIT_README.md` with `Pipeline Position` section clarifying discovery/confirmation vs certificate ownership boundaries.
- Added `strategy/README.md` to define the public technical vs private commercial boundary.
- Removed tracked commercial playbook documents from `strategy/`:
  - `HIGHEST_EV_PATH.md`
  - `OFFER_AND_GTM.md`
  - `REVENUE_MODEL.md`
  - `EXECUTION_90_DAYS.md`
  - `KPI_SCOREBOARD.md`
  - `OPERATING_CADENCE.md`
  - `LEGAL_COMPLIANCE_US.md`
  - `FUNDRAISING_AND_DATA_ROOM.md`
  - `RISK_REGISTER.md`
- Added `scripts/check_public_boundary.py` and CI `public-boundary` job to fail on tracked private/commercial-only files.
- Updated commercial/cadence workflows to require `ENABLE_COMMERCIAL_AUTOMATION=true` before execution.
- Updated strategy/readme docs to mark commercial automation as opt-in for private/forked environments.
- Extended `CPAMM/TokenizedBehavior.lean` with step-level unsupported-behavior incompatibility theorems:
  - exact-pull extraction lemmas from tokenized step relations
  - non-exact pull incompatibility lemmas for tokenized add/swap transitions
  - external-drift reserve-sync non-preservation lemmas with unchanged core reserves
- Updated `reports/ASSUMPTION_TEST_MATRIX.md` to include the new step-level Lean theorem mappings.
- Enhanced `scripts/validate_assumption_matrix.py` to validate Lean symbol references in addition to Solidity test references.
- Updated tokenized verification docs (`VERIFICATION_TOKENIZED.md`, `VERIFICATION.md`) to reflect implemented trace-level projection, strengthened behavior lemmas, and matrix validation scope.
- Extended `CPAMM/TokenizedBehavior.lean` with output-path recipient-fee semantics:
  - `RecipientFeePush`
  - `RecipientObservedOutputExact`
  - `recipientObservedOutputExact_iff_exactPullDelta`
  - `recipientFeePush_exactPushDelta`
  - `recipientFeePush_receiver_not_exact`
  - `recipientFeePush_receiverOutput_not_exact`
  - `reserveSync_preserved_by_recipientFeePushY`
  - `reserveSync_and_outputDivergence_by_recipientFeePushY`
  - `reserveSync_and_removeLiquidityOutputDivergence_by_recipientFeePushX`
- Extended `solidity/test/CPAMM.Tokenized.Adversarial.t.sol` with output-path divergence tests:
  - `test_outputFeeOnPoolTransfer_breaksObservedSwapXforYOutput`
  - `test_outputFeeOnPoolTransfer_breaksObservedSwapYforXOutput`
  - `test_outputFeeOnPoolTransfer_breaksObservedRemoveLiquidityOutput`
- Updated token compatibility and assumption matrix docs to include output-path divergence behavior and theorem/test links.
- Refactored `CPAMM/TokenizedRefinement.lean` with reusable step-level preservation theorems:
  - `valid_preserved_tokenizedStep`
  - `reserveSync_preserved_tokenizedStep`
- Upgraded `scripts/review_package.sh` into a fuller reproducibility bundle:
  - theorem inventory export (`theorem-inventory.md`)
  - strict protocol intake report/log (`protocol-intake.md`, `protocol-intake.log`)
  - checksummed inclusion in `SHA256SUMS`
- Updated `reports/REVIEW_PACKAGE.md` and verification docs to reflect expanded bundle contents.
- Added commercialization playbook docs under `strategy/`:
  - highest-EV path thesis and sequencing
  - evidence portal design/purpose and generation workflow
  - offer/GTM model and revenue model
  - 90-day execution plan and KPI scoreboard
  - operating cadence and risk register
  - legal/compliance and fundraising/data-room checklists
- Added execution assets under `strategy/assets/`:
  - CRM schema and pipeline CSV template
  - outbound, discovery, and follow-up sales templates
  - proposal, SOW, and acceptance-criteria templates
  - KPI tracker and weekly dashboard template
- Added `scripts/strategy_dashboard.py` to generate `reports/WEEKLY_DASHBOARD.md` from CRM/KPI trackers.
- Added `strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json` for structured deal-pack input.
- Added `scripts/deal_pack.py` to render proposal/SOW docs from JSON input into `strategy/private/generated/<deal_id>/`.
- Added `scripts/pipeline_health.py` to score funnel health and produce close-horizon forecast reports from CRM pipeline data.
- Added `scripts/outbound_focus.py` to generate a prioritized weekly outbound execution queue (`OUTBOUND_FOCUS.md` + `OUTBOUND_FOCUS.csv`) from CRM pipeline data.
- Added `scripts/outbound_sla_gate.py` to enforce outbound SLA thresholds (overdue/missing/stale ratios) with strict CI/cadence gating support.
- Added `scripts/case_study_pack.py` to generate sanitized case-study artifacts (`CASE_STUDY.md` + summary JSON + manifest) from structured input.
- Added `scripts/case_study_index.py` to generate portfolio-level case-study index and rollup artifacts.
- Added `scripts/case_study_portal.py` to generate a stable case-study portal entrypoint (`INDEX.md` + manifest) for outbound linking.
- Added `scripts/commercial_review_package.sh` to build a one-command commercialization evidence bundle (dashboard, pipeline health, optional deal pack, checksums, tarball).
- Updated `scripts/commercial_review_package.sh` to include outbound focus + outbound SLA artifacts, optional case-study packaging, and case-study rollup outputs.
- Extended `scripts/case_study_pack.py` with `--out-root` support for multi-case-study publication layouts.
- Added `scripts/validate_strategy_data.py` with strict schema/range/date checks for pipeline CSV, KPI CSV, and deal JSON.
- Added `scripts/evidence_portal.py` to generate multi-page client-facing evidence portals from engagement metadata and artifact bundles.
- Added evidence portal templates under `strategy/assets/portal/` (`PORTAL_INPUT_TEMPLATE.json` + usage README).
- Added `scripts/create_cadence_issue.py` to create recurring KPI/risk cadence issues with label bootstrapping and duplicate-title protection.
- Added assignee routing and optional webhook notification support to cadence issue creation (`CADENCE_KPI_ASSIGNEES`, `CADENCE_RISK_ASSIGNEES`, `CADENCE_NOTIFY_WEBHOOK_URL`).
- Added strategy tooling regression tests in `tests/test_strategy_tooling.py`.
- Added `strategy-tooling` CI gate checks for strategy-data validation (including portal input) and script regression tests on every push/PR.
- Added strict outbound SLA CI gate in `strategy-tooling` job (`scripts/outbound_sla_gate.py` over template data).
- Added case-study template validation in `strategy-tooling` job (`--case-study-input`).
- Added case-study index generation check in `strategy-tooling` job.
- Added `commercial-review-package` CI job to build and upload a sanitized commercialization evidence artifact on every push/PR, including optional evidence portal generation from template input.
- Added `.github/workflows/operating-cadence.yml` to auto-open weekly KPI and monthly risk review issues (plus manual dispatch support).
- Extended `.github/workflows/operating-cadence.yml` with KPI outbound digest generation, artifact upload, and issue-thread digest comments.
- Added `.github/workflows/evidence-portal-publish.yml` to publish evidence portal artifacts on schedule and manual dispatch.
- Added `.github/workflows/case-study-publish.yml` to publish case-study package + rollup artifacts on schedule and manual dispatch.
- Expanded `.github/workflows/case-study-publish.yml` to support multi-input glob resolution and multi-package publication.
- Expanded `.github/workflows/case-study-publish.yml` to emit a dedicated `case-study-portal` landing artifact.
- Added cadence automation configuration guide: `strategy/assets/ops/CADENCE_AUTOMATION_CONFIG.md`.
- Added GitHub issue templates for execution cadence:
  - `.github/ISSUE_TEMPLATE/weekly-kpi-review.md`
  - `.github/ISSUE_TEMPLATE/risk-register-review.md`
- Hardened `.gitignore` for private commercialization data (`strategy/private/*`, live CRM/KPI files, and generated weekly/pipeline reports).
- Extended `.gitignore` with outbound report outputs (`reports/OUTBOUND_*`) to reduce risk of committing private pipeline activity data.
- Extended `.gitignore` with case-study rollup report outputs (`reports/CASE_STUDIES_*`) to reduce risk of committing private pipeline activity data.
- Updated evidence portal generation and publish workflow to include optional case-study index/rollup artifact references.
- Updated commercialization docs with deal-pack and pipeline-health automation commands.

## v1.5.0 - 2026-03-01

### Added
- Abstract full-withdrawal boundary model in Lean:
  - `RemoveLiquidityTerminal`
  - `Terminal`
  - `ValidOrTerminal`
- Boundary preservation theorems:
  - `terminal_preserved_removeLiquidityTerminal`
  - `validOrTerminal_preserved_removeLiquidityBoundary`
- Solidity unit test `test_removeLiquidity_fullWithdraw_reverts` to lock current contract behavior (`shares < totalSupply`).
- ERC20-backed CPAMM extension contract: `solidity/src/CPAMMTokenized.sol`.
- ERC20-backed integration suite: `solidity/test/CPAMM.Tokenized.t.sol`:
  - reserve/token-balance sync checks across add/remove/swaps
  - fee-on-transfer rejection path
  - multi-step fuzzed sequence with proportional add step generation
- Tokenized verification-track document: `VERIFICATION_TOKENIZED.md`.
- Tokenized Lean refinement module: `CPAMM/TokenizedRefinement.lean` with:
  - tokenized step relations (`TokenizedSwap*`, `TokenizedAddLiquidity`, `TokenizedRemoveLiquidity`)
  - reserve/token-balance sync invariant (`ReserveSync`) and per-step preservation theorems
  - projection/simulation into arithmetic `Solidity*` relations
  - trace-level `validAndSync_preserved_tokenizedReachable`
- Token behavior taxonomy module: `CPAMM/TokenizedBehavior.lean` with:
  - token class partition (`TokenClass`, `SupportedTokenClass`)
  - unsupported-class non-exactness lemmas
  - concrete reserve-sync break witness for external drift
- Adversarial token behavior test suite: `solidity/test/CPAMM.Tokenized.Adversarial.t.sol` with rejection-path coverage for:
  - false-return `transferFrom`
  - no-op `transferFrom`
  - inflationary transfer behavior
  - false-return `transfer` on output path
  - external balance drift (rebase-style mismatch)
- Reviewer-facing token compatibility matrix: `security/TOKEN_COMPATIBILITY.md`.
- Assumption-to-test coupling matrix: `reports/ASSUMPTION_TEST_MATRIX.md`.
- Matrix validator script: `scripts/validate_assumption_matrix.py`.
- One-command review package generator: `scripts/review_package.sh`.
- Review package usage guide: `reports/REVIEW_PACKAGE.md`.

### Changed
- Verification and audit docs now explicitly distinguish:
  - Solidity/refinement path (`dL < totalSupply`)
  - Abstract terminal-close boundary (`dL = L`)
- Verification docs now include the tokenized refinement theorem inventory and exact-transfer assumption boundary.
- Security validation report now records `30/30` passing tests (including tokenized adversarial matrix coverage).
- Slither gate scope extended from `solidity/src/CPAMM.sol` to `solidity/src` (core + tokenized extension).
- CI coverage gate now checks both:
  - `src/CPAMM.sol`
  - `src/CPAMMTokenized.sol`
- CI now includes a dedicated `review-package` job that publishes a single bundled artifact with manifest, checksums, and reproducibility evidence.
- CI now enforces assumption-matrix correctness by checking each referenced test function exists.

## v1.4.1 - 2026-03-01

### Changed
- CI moved Slither SARIF upload from `github/codeql-action/upload-sarif@v3` to `@v4`.
- CI workflow actions are now fully pinned to immutable commit SHAs (checkout, upload-artifact, setup-python, cache, foundry-toolchain, codeql upload) for stronger reproducibility and supply-chain hardening.

## v1.3 - 2026-02-28

### Added
- Multi-actor Foundry invariant harness for LP accounting correctness across two LP holders.
- Bootstrap add-liquidity simulation theorem (`sim_addLiquidity_bootstrap`) for the `L = 0`, zero-reserve initialization path.
- Abstract floor-preservation theorem for add-liquidity validity (`valid_preserved_addLiquidityFloor`).
- Solidity-layer validity preservation theorem chain for all core operations:
  - `valid_preserved_soliditySwapXforY`
  - `valid_preserved_soliditySwapYforX`
  - `valid_preserved_solidityAddLiquidity`
  - `valid_preserved_solidityRemoveLiquidity`
- Symmetric economic theorem `product_nondecreasing_swapYforX_with_fee`.

### Changed
- CI now pins Lean action by commit SHA for stronger reproducibility.
- CI uploads Slither SARIF into GitHub Security (Code Scanning).
- CI coverage gate now enforces:
  - `src/CPAMM.sol` line coverage = `100%`
  - `src/CPAMM.sol` statement coverage = `100%`
  - `src/CPAMM.sol` branch coverage floor gate
- Documentation updated for theorem inventory, refinement scope, and audit/security workflow.

## v1.4 - 2026-02-28

### Added
- Trace-level Solidity refinement closure in Lean:
  - `SolidityStep`
  - `SolidityReachable`
  - `valid_preserved_solidityStep`
  - `valid_preserved_solidityReachable`

### Changed
- CI security reliability improvements:
  - retry-wrapped pip/slither installs in `scripts/security/slither.sh`
  - `.venv-security` and pip cache reuse in CI security job
- CI SARIF upload made conditional on SARIF file presence to avoid secondary failure masking.

## v1.2 - 2026-02-28

### Added
- Compiler/security hardening to remove `solc-version` warning via Solidity `0.8.30`.
- Stateful invariant campaign and CI artifact/report pipeline.
- External reviewer guide: `security/AUDIT_README.md`.
