#!/usr/bin/env bash
# bambu-easy first-time setup. Creates a venv, installs the package, and
# launches the interactive setup wizard.

set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}

if ! command -v "$PY" >/dev/null; then
  echo "❌ python3 not found. Install Python 3.10+ from https://www.python.org/downloads/"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "→ Creating virtual environment in .venv"
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "→ Upgrading pip"
pip install --upgrade pip >/dev/null

echo "→ Installing bambu-easy (editable)"
pip install -e . >/dev/null

echo
echo "→ Launching interactive setup wizard..."
echo
exec bambu-easy --setup
