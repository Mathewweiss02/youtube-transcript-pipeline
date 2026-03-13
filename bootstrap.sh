#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Creating local virtual environment at $VENV_DIR..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "Upgrading pip in the local virtual environment..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip

echo
echo "Installing youtube-transcript-pipeline in editable mode..."
"$VENV_DIR/bin/python" -m pip install -e "$ROOT_DIR"

echo
echo "Running first-run environment checks..."
"$VENV_DIR/bin/python" -m yt_processor.pipeline_doctor --create-dirs --verify-examples

echo
echo "Bootstrap complete."
echo "Activate the environment with:"
echo "  source .venv/bin/activate"
