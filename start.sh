#!/data/data/com.termux/files/usr/bin/bash
set -e

PYTHON_BIN="python"

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

if ! $PYTHON_BIN - <<'PY' >/dev/null 2>&1
import requests
import flask
import yaml
import colorama
PY
then
  echo "Missing Python dependencies."
  echo "Running dependency fixer..."
  bash fix_dependencies.sh
fi

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

$PYTHON_BIN waf.py --config config.yml
