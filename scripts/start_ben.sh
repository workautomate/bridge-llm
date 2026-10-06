#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/bridge-llm/env"
[[ -f "$CONFIG_FILE" ]] && source "$CONFIG_FILE"

BEN_ROOT="${BEN_ROOT:-$HOME/.local/share/bridge-llm/ben}"
BEN_VENV="${BEN_VENV:-$HOME/ben}"
BEN_PORT="${BEN_PORT:-8085}"

if [[ ! -f "$BEN_ROOT/src/gameapi.py" ]]; then
  echo "BEN not found at $BEN_ROOT; run scripts/setup_wsl.sh first." >&2
  exit 1
fi

cd "$BEN_ROOT/src"
exec "$BEN_VENV/bin/python" gameapi.py \
  --host 127.0.0.1 \
  --port "$BEN_PORT" \
  --allowed-hosts 'localhost,127.0.0.1'
