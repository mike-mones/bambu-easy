#!/usr/bin/env bash
# bambu-easy first-time setup. Creates a venv, installs the package, and
# prompts for the printer credentials.

set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}

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

if [ ! -f "printer_config.json" ]; then
  echo
  echo "→ Setting up printer_config.json"
  echo "  Open Bambu Studio → Device → Settings → LAN Only Mode."
  read -rp "    Printer IP (e.g. 192.168.0.247): " IP
  read -rp "    Access code (8-char hex): " CODE
  read -rp "    Serial number: " SERIAL
  cat > printer_config.json <<EOF
{
    "printer_ip": "$IP",
    "access_code": "$CODE",
    "serial": "$SERIAL"
}
EOF
  echo "  Wrote printer_config.json"
fi

echo
echo "✅ Setup complete."
echo "Activate the venv with:  source .venv/bin/activate"
echo "Then run:                bambu-easy --doctor"
