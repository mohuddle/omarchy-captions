#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
BIN_DIR="${HOME}/.local/bin"
PLUGIN_ID="io.github.mohuddle.captions"
PLUGIN_DIR="${HOME}/.config/omarchy/plugins/${PLUGIN_ID}"

if ! command -v pw-record >/dev/null; then
  echo "pw-record not found. On Omarchy: omarchy pkg add pipewire-audio" >&2
  exit 1
fi

echo "creating venv"
python3 -m venv --without-pip "$VENV"
curl -fsSL https://bootstrap.pypa.io/get-pip.py | "$VENV/bin/python"
"$VENV/bin/pip" install -e "$ROOT"

echo "downloading English streaming model"
"$VENV/bin/captions" setup

mkdir -p "$BIN_DIR"
ln -sfn "$VENV/bin/captions" "$BIN_DIR/captions"

mkdir -p "$(dirname "$PLUGIN_DIR")"
ln -sfn "$ROOT" "$PLUGIN_DIR"

if command -v omarchy >/dev/null; then
  omarchy plugin enable "$PLUGIN_ID" >/dev/null 2>&1 || true
  echo "enable the bar widget if it is not already there:"
  echo "  omarchy bar move $PLUGIN_ID --section right"
fi

echo
echo "ready. open the TUI:"
echo "  captions tui"
echo "space starts listening to the speakers."
