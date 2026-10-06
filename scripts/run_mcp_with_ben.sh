#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/bridge-llm/env"
[[ -f "$CONFIG_FILE" ]] && source "$CONFIG_FILE"
BEN_VENV="${BEN_VENV:-$HOME/ben}"

# Never write startup text to stdout: stdio is reserved for MCP protocol frames.
"$PROJECT_ROOT/scripts/ensure_ben.sh" 1>&2
exec "$BEN_VENV/bin/bridge-mcp"
