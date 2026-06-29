#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "======================================"
echo " Fix Python Dependencies"
echo " Mraprguild Termux Website Firewall"
echo "======================================"

pkg update -y
pkg install -y python

echo "[1/4] Python version"
python --version

echo "[2/4] Upgrade pip"
python -m pip install --upgrade pip setuptools wheel || true

echo "[3/4] Install required modules"
if python -m pip install -r requirements.txt; then
  echo "Dependencies installed successfully."
elif python -m pip install --user -r requirements.txt; then
  echo "Dependencies installed with --user."
else
  echo "Normal pip failed. Creating local virtual environment..."
  python -m venv .venv
  . .venv/bin/activate
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install -r requirements.txt
  echo "Dependencies installed inside .venv"
fi

echo "[4/4] Verify modules"

PYTHON_BIN="python"

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

$PYTHON_BIN - <<'PY'
import requests
import flask
import yaml
import colorama

print("OK: requests, flask, yaml, colorama installed")
PY

echo ""
echo "Fix complete."
echo "Start firewall:"
echo "bash start.sh"
