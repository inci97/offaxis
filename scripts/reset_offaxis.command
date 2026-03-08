#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.offaxis-venv"

rm -rf "$VENV_DIR"
echo "Reset complete. Removed local runtime environment: $VENV_DIR"
