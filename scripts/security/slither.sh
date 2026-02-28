#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-security"
ACCEPTED_DETECTORS="divide-before-multiply,solc-version"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip
  pip install slither-analyzer
else
  source "$VENV_DIR/bin/activate"
fi

cd "$ROOT_DIR"
slither solidity/src/CPAMM.sol \
  --exclude "$ACCEPTED_DETECTORS" \
  --exclude-dependencies \
  --fail-pedantic
