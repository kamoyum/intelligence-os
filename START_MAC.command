#!/bin/bash
set -e
cd "$(dirname "$0")"
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "Python 3.11+ is required. Install Python from python.org, then run this again."
  read -r
  exit 1
fi
if [ ! -d .venv ]; then "$PY" -m venv .venv; fi
. .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r backend/requirements.txt
python scripts/preflight.py
exec python desktop/app.py
