#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${BRIDGE_LLM_HOME:-$HOME/.local/share/bridge-llm}"
BEN_ROOT="${BEN_ROOT:-$DATA_ROOT/ben}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/bridge-llm"
BEN_VENV="${BEN_VENV:-$HOME/ben}"

if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then
    echo "[bridge-llm] WARNING: BEN's vendored DDS3 is built for Ubuntu 24.04+/glibc >= 2.38." >&2
    echo "[bridge-llm] Current distro: ${PRETTY_NAME:-unknown}" >&2
  fi
fi

mkdir -p "$DATA_ROOT" "$CONFIG_DIR"

if [[ ! -d "$BEN_ROOT/.git" ]]; then
  echo "[bridge-llm] Cloning BEN into $BEN_ROOT" >&2
  git clone https://github.com/lorserker/ben.git "$BEN_ROOT"
else
  echo "[bridge-llm] Updating BEN checkout" >&2
  git -C "$BEN_ROOT" pull --ff-only
fi

# BEN's official Linux setup installs Python 3.12 dependencies and creates ~/ben.
(
  cd "$BEN_ROOT"
  bash setup_linux.sh
)

"$BEN_VENV/bin/python" -m pip install --upgrade pip
"$BEN_VENV/bin/python" -m pip install -e "$PROJECT_ROOT"

cat > "$CONFIG_DIR/env" <<ENV
export BEN_ROOT="$BEN_ROOT"
export BEN_URL="http://127.0.0.1:8085"
export BEN_TIMEOUT="120"
export BEN_VENV="$BEN_VENV"
ENV

chmod +x "$PROJECT_ROOT"/scripts/*.sh

echo "[bridge-llm] Installed." >&2
echo "[bridge-llm] Environment: $CONFIG_DIR/env" >&2
echo "[bridge-llm] Start BEN: $PROJECT_ROOT/scripts/start_ben.sh" >&2
echo "[bridge-llm] Check: source $CONFIG_DIR/env && $BEN_VENV/bin/bridge-doctor" >&2
