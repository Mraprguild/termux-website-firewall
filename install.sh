#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "======================================"
echo " Mraprguild Termux Website Firewall"
echo "======================================"

pkg update -y
pkg upgrade -y
pkg install -y python git nano unzip

python -m pip install --upgrade pip setuptools wheel || true

echo "Installing Python requirements..."

if python -m pip install -r requirements.txt; then
  echo "Requirements installed."
elif python -m pip install --user -r requirements.txt; then
  echo "Requirements installed with --user."
else
  echo "Pip install failed. Creating local .venv..."
  python -m venv .venv
  . .venv/bin/activate
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install -r requirements.txt
fi

if [ ! -f config.yml ]; then
  cp config.example.yml config.yml
fi

mkdir -p logs rules

touch logs/blocked.log
touch rules/blocked_ips.txt
touch rules/allowed_ips.txt
touch rules/bad_bots.txt

chmod +x start.sh demo_backend.sh security_test.sh fix_dependencies.sh github_setup.sh 2>/dev/null || true

echo "Verifying modules..."

PYTHON_BIN="python"

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

$PYTHON_BIN - <<'PY'
import requests
import flask
import yaml
import colorama

print("OK: all required Python modules are installed")
PY

echo ""
echo "Install complete."
echo "Edit config:"
echo "nano config.yml"
echo ""
echo "Start:"
echo "bash start.sh"
