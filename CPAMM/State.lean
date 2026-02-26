/-
  CPAMM-1: Constant-Product AMM — Abstract State and Validity

  The ideal model uses ℚ (rationals) for exact arithmetic.
  The address type is a parameter — the Solidity refinement
  instantiates it with a concrete type later.

  Authors: Cody Mitchell, Claude
  Date: February 2026
-/

import Mathlib

/-!
## Abstract State

Two tokens (X and Y), LP supply, per-address balances, and a fee fraction.
All quantities are rational for the ideal economic model.
-/

/-- Abstract state of a two-token constant-product AMM. -/
structure CpammState (α : Type*) where
  /-- Reserve of token X -/
  x : ℚ
  /-- Reserve of token Y -/
  y : ℚ
  /-- Total LP token supply -/
  L : ℚ
  /-- LP token balances per address -/
  balances : α → ℚ
  /-- Fee fraction, e.g. 3/1000 for 0.3% -/
  f : ℚ

/-!
## Validity

A state is valid when all economic constraints hold.
-/

/-- A CpammState is valid iff all economic constraints are satisfied. -/
def Valid {α : Type*} (s : CpammState α) : Prop :=
  s.x > 0 ∧
  s.y > 0 ∧
  s.L ≥ 0 ∧
  (∀ a : α, s.balances a ≥ 0) ∧
  0 ≤ s.f ∧ s.f < 1

/-- The constant product of a state. -/
def product {α : Type*} (s : CpammState α) : ℚ := s.x * s.y

/-- A valid state has positive product. -/
theorem product_pos {α : Type*} (s : CpammState α) (h : Valid s) :
    product s > 0 := by
  obtain ⟨hx, hy, _, _, _, _⟩ := h
  exact mul_pos hx hy
