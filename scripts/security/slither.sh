#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-security"
SLITHER_VERSION="0.11.4"
ACCEPTED_DETECTORS="divide-before-multiply"
SLITHER_SARIF="${SLITHER_SARIF:-}"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

INSTALLED_SLITHER_VERSION="$(
  python -m pip show slither-analyzer 2>/dev/null | awk '/^Version:/{print $2}'
)"
if [[ "$INSTALLED_SLITHER_VERSION" != "$SLITHER_VERSION" ]]; then
  python -m pip install "slither-analyzer==$SLITHER_VERSION"
fi

cd "$ROOT_DIR"
SLITHER_ARGS=(
  solidity/src/CPAMM.sol
  --exclude "$ACCEPTED_DETECTORS"
  --exclude-dependencies
  --fail-pedantic
)

if [[ -n "$SLITHER_SARIF" ]]; then
  SLITHER_ARGS+=(--sarif "$SLITHER_SARIF")
fi

slither "${SLITHER_ARGS[@]}"
