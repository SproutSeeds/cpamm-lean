#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v lake >/dev/null 2>&1; then
  LAKE_BIN="$(command -v lake)"
elif [[ -x "$HOME/.elan/bin/lake" ]]; then
  LAKE_BIN="$HOME/.elan/bin/lake"
else
  echo "error: lake not found (install Lean 4 / elan first)" >&2
  exit 1
fi

if command -v forge >/dev/null 2>&1; then
  FORGE_BIN="$(command -v forge)"
elif [[ -x "$HOME/.foundry/bin/forge" ]]; then
  FORGE_BIN="$HOME/.foundry/bin/forge"
else
  echo "error: forge not found (install Foundry first)" >&2
  exit 1
fi

echo "==> Lean cache"
"$LAKE_BIN" exe cache get

echo "==> Lean build"
"$LAKE_BIN" build

echo "==> Foundry tests"
(
  cd "$ROOT_DIR/solidity"
  "$FORGE_BIN" test
)

echo "==> Reproduction complete"
