# Protocol Handoff Template (RigidityCore -> cpamm-lean)

This document defines how a confirmed `System.json` finding from RigidityCore is translated into Lean proof work in this repo.

## 1) Pipeline Stages and Ownership

1. RigidityCore discovery stage (owned by RigidityCore)
- Input: protocol model in `System.json` (`schema_version: "0.1"`).
- Work: structural sweep, corridor/replay confirmation, materiality measurement, audit dedup.
- Output: confirmed finding with immutable evidence artifacts and a scoped handoff payload.

2. Handoff boundary (joint contract, triggered from RigidityCore side)
- Trigger: confirmed finding is ready for formal certificate work.
- Payload: relevant `System.json` slice + replay evidence + assumptions + dedup status.

3. cpamm-lean proof stage (owned by cpamm-lean)
- Work: formalize the handed-off transition/invariant/rounding surface and produce machine-checked Lean theorems.
- Output: reproducible Lean certificate artifacts and reviewer-facing proof boundary documentation.

4. Reviewer package stage (owned by cpamm-lean)
- Work: combine proof inventory + tests + static analysis into auditable evidence bundles.
- Output: `VERIFICATION.md`, security notes, and reproducibility package for external review.

## 2) Schema-to-Proof Mapping (System.json -> Lean)

Ground truth schema source: `RigidityCore/spec/SPEC.md` (`System.json` v0.1).

| System.json field | Lean equivalent | cpamm-lean example |
|---|---|---|
| `state_vars[]` | Fields of concrete storage model (`SolidityStorage`) and abstract state via `alpha` | `reserveX`, `reserveY`, `totalSupply` in `CPAMM/Refinement.lean` |
| `transitions[]` | `Solidity*` relation definitions (plus abstract relation counterparts) | `SoliditySwapXforY`, `SolidityAddLiquidity` |
| `invariants[]` | Validity/consistency preservation theorem statements | `valid_preserved_soliditySwapXforY`, `valid_preserved_solidityAddLiquidity` |
| `transitions[].update_model.rounding[].type = "floor_div"` | Floor-div theorem obligations and bounded simulation lemmas | `nat_div_le_rat_div`, `rat_div_sub_one_lt_nat_div`, `sim_swapXforY`, `sim_removeLiquidity` |
| `assumptions[]` | Lean preconditions and explicit theorem assumptions | `h_denom_pos`, `hv : Valid (alpha σ)` |
| `parameters[]` | Immutable storage parameters and constants in refinement model | `feeNumerator`, `feeDenominator` |
| `transitions[].guard` predicates | Relation preconditions in `Solidity*` / abstract transition relations | `dx > 0`, `shares < totalSupply`, proportionality guards |

Notes:
- `reads`/`writes` in `System.json` guide which storage fields appear in each relation and theorem dependency surface.
- `predicate_stub` values in `invariants[]` become concrete Lean propositions/theorem goals during proof implementation.

## 3) SUNFLOWER Gate Rule (Strict)

Lean certificates are downstream of confirmed RigidityCore findings only.  
Lean does **not** run as speculative pre-triage work.

From `ops/SUNFLOWER_LEAN_CROSSOVER.md`, all three conditions must hold before Lean proof work begins:

1. Contract replay determinism is established.
2. Audit dedup gate has no unresolved overlap for that lane.
3. The lane has measurable impact signal worth escalation discussion.

If any condition is missing, Lean work is deferred.

## 4) Worked CPAMM Example (Reference Mapping)

Reference source model:
- `RigidityCore/amm/examples/cpamm/System.json`

Reference proof model:
- `cpamm-lean/CPAMM/Refinement.lean`

Field-by-field mapping:

1. Top-level identity
- `schema_version`, `system_id`, `name`, `domain` map to proof context metadata/scope, not theorem terms.
- In cpamm-lean, the active formal scope is the CPAMM arithmetic/refinement boundary.

2. `state_vars[]`
- `x_reserve` -> `SolidityStorage.reserveX`
- `y_reserve` -> `SolidityStorage.reserveY`
- `total_lp` -> `SolidityStorage.totalSupply`
- Abstract lift: `alpha : SolidityStorage -> CpammState SolAddress`.

3. `parameters[]`
- `fee_bps` in the example becomes explicit fee fields in refinement:
  - `feeNumerator`
  - `feeDenominator`
  - and assumption `h_denom_pos : 0 < feeDenominator`.

4. `transitions[]`
- `swap_x_for_y` maps to:
  - concrete relation `SoliditySwapXforY`
  - abstract bounded relation `SwapXforYFloor`
  - simulation theorem `sim_swapXforY`.
- `add_liquidity` maps to:
  - concrete relation `SolidityAddLiquidity`
  - abstract bounded relation `AddLiquidityFloor`
  - simulation theorem `sim_addLiquidity`.

5. `transitions[].guard`
- Example guard `dx > 0` becomes relation preconditions (`dx > 0`) in `SoliditySwapXforY`.
- Liquidity guard structures map similarly (`dx > 0`, `dy > 0`, proportionality side condition when supply > 0).

6. `transitions[].update_model.rounding[]`
- Example `swap_floor_div` maps to integer floor arithmetic obligations:
  - floor bound lemmas (`nat_div_le_rat_div`, `rat_div_sub_one_lt_nat_div`)
  - bounded simulation into rational model.

7. `invariants[]`
- Example safety/consistency stubs map to formal validity theorems:
  - `valid_preserved_*` theorems for transitions
  - consistency preservation theorems for LP accounting.

8. `assumptions[]`
- Example assumption `token_transfer_exact` corresponds to explicit assumption surfaces in tokenized refinement (`CPAMM/TokenizedRefinement.lean`) and behavior taxonomy (`CPAMM/TokenizedBehavior.lean`).

This CPAMM pair (`System.json` + `Refinement.lean`) is the canonical template for incoming non-CPAMM handoffs.
