# Protocol Template Directory

This directory is the engagement template for new proof work.

When RigidityCore confirms a finding on a new protocol (after replay confirmation and dedup gate), copy this directory and replace scaffolding with protocol-specific definitions and proofs.

Contents:
- `State.lean`: parameterized abstract state scaffold.
- `Refinement.lean`: Solidity-to-abstract refinement scaffold with intentional `sorry` placeholders.
- `Rounding.lean`: floor-division proof pattern scaffold.

Important:
- `sorry` placeholders in `Refinement.lean` are intentional scaffolding for new engagements.
- `CPAMM/*.lean` remains the production reference artifact and must stay `sorry`-free.
