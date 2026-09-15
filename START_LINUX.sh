#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then echo "Python 3.11+ is required."; exit 1; fi
if [ ! -d .venv ]; then "$PY" -m venv .venv; fi
. .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r backend/requirements.txt
python scripts/preflight.py
exec python desktop/app.py
