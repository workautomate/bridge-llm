#!/usr/bin/env bash
set -euo pipefail
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/bridge-llm"
PID_FILE="$CACHE_DIR/ben.pid"
if [[ ! -f "$PID_FILE" ]]; then
  echo "No managed BEN process found." >&2
  exit 0
fi
PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
fi
rm -f "$PID_FILE"
