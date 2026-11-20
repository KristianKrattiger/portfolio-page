#!/usr/bin/env sh
# Build (validates the ledger; aborts on failure) and serve dist/ on loopback only.
# Usage: ./run.sh [port]   (default 8787). Never binds 0.0.0.0.
set -e
cd "$(dirname "$0")"
PORT="${1:-8787}"
PY="$(command -v python3 2>/dev/null || command -v python)"
# On Windows, python3 may be the Store stub; prefer a real interpreter.
"$PY" -c "import sys" 2>/dev/null || PY=python
"$PY" build.py
echo "Serving http://127.0.0.1:$PORT/"
exec "$PY" -m http.server "$PORT" --bind 127.0.0.1 --directory dist
