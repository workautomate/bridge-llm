#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/bridge-llm/env"
[[ -f "$CONFIG_FILE" ]] && source "$CONFIG_FILE"

BEN_URL="${BEN_URL:-http://127.0.0.1:8085}"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/bridge-llm"
mkdir -p "$CACHE_DIR"

if curl -fsS --max-time 2 "$BEN_URL/bids?ctx=" >/dev/null 2>&1; then
  exit 0
fi

if [[ -f "$CACHE_DIR/ben.pid" ]] && kill -0 "$(cat "$CACHE_DIR/ben.pid")" 2>/dev/null; then
  :
else
  nohup "$PROJECT_ROOT/scripts/start_ben.sh" >"$CACHE_DIR/ben.log" 2>&1 &
  echo $! > "$CACHE_DIR/ben.pid"
fi

for _ in $(seq 1 120); do
  if curl -fsS --max-time 2 "$BEN_URL/bids?ctx=" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 1
done

echo "BEN did not become ready. See $CACHE_DIR/ben.log" >&2
exit 1
