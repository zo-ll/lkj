#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Installing uv to ~/.local/bin"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv install failed. Install manually, then rerun." >&2
  exit 1
fi

echo "Creating Python 3.12 virtualenv"
uv python install 3.12
if [[ ! -x .venv/bin/python ]]; then
  uv venv --python 3.12 .venv
else
  echo "Reusing existing virtualenv at .venv"
fi

echo "Installing runtime dependencies"
uv pip install --python .venv/bin/python --upgrade pip
uv pip install --python .venv/bin/python torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
uv pip install --python .venv/bin/python -e .

echo "Bootstrap done"
echo "Next: run ./scripts/install.sh for full desktop install"
