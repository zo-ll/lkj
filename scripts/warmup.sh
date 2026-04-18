#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ ! -x .venv/bin/python ]]; then
  echo ".venv missing. Run scripts/bootstrap.sh first." >&2
  exit 1
fi

echo "Running doctor"
.venv/bin/python -m lkj.cli doctor

echo "Downloading/loading model cache"
.venv/bin/python -m lkj.cli --online doctor --warmup

echo "Warmup complete. Daily command: .venv/bin/python -m lkj.cli run"
