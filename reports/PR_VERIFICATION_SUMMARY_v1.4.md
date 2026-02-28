# PR-Style Verification Summary - v1.4

Date: 2026-02-28  
Target: `v1.4` (`7cc57c5`)  
Scope: Trace-level refinement closure + CI security/reliability hardening.

## Change Scope

Commits in scope:
- `34c4abd` - `proof: add Solidity step/reachability validity preservation theorems`
- `7cc57c5` - `ci+release: harden security job reliability and add v1.4 changelog`

Primary files changed:
- `CPAMM/Refinement.lean`
- `.github/workflows/ci.yml`
- `scripts/security/slither.sh`
- `README.md`
- `VERIFICATION.md`
- `security/SECURITY_VALIDATION.md`
- `CHANGELOG.md`

## Formal Verification Additions

Added to `CPAMM/Refinement.lean`:
- `SolidityStep` (single-step concrete transition relation)
- `SolidityReachable` (finite trace reachability relation)
- `valid_preserved_solidityStep`
- `valid_preserved_solidityReachable`

Security implication:
- `Valid (alpha ·)` is now preserved not only per step, but across arbitrary finite Solidity execution traces.

## CI / Tooling Changes

Security job hardening:
- Retry-wrapped package install logic in `scripts/security/slither.sh`.
- Cache configured in CI for:
  - `.venv-security`
  - `~/.cache/pip`
- SARIF upload is conditional on SARIF artifact presence to avoid secondary masking failures.

Existing gates retained:
- Lean build
- Solidity test suite (unit + fuzz + differential + invariant)
- Slither gate (fail-on-findings, policy exclusions)
- Coverage threshold checks

## Validation Evidence

Remote CI evidence:
- `22530910974` (`v1.4`): **success**
- `22530909283` (`main`, same SHA): **success**

Local validation evidence during implementation:
- `~/.elan/bin/lake build` - pass
- `~/.foundry/bin/forge test` - pass (`18/18`)
- `./scripts/security/slither.sh` - pass (`0` findings under policy)

## Risk / Residual Notes

- No new protocol features added.
- No `sorry` introduced.
- Changes are proof/validation and CI reliability focused.

## Reviewer Checklist

- [x] Trace-level Solidity validity theorem chain present and machine-checked.
- [x] CI security job stability hardened with retries/caching.
- [x] SARIF upload behavior robust to missing-file edge case.
- [x] End-to-end CI run for `v1.4` succeeded.
