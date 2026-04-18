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

CONFIG_DIR="$HOME/.config/lkj"
CONFIG_PATH="$CONFIG_DIR/config.json"
if [[ ! -f "$CONFIG_PATH" ]]; then
  mkdir -p "$CONFIG_DIR"
  cp "$PROJECT_DIR/config.example.json" "$CONFIG_PATH"
fi

echo "Running one-time warmup to cache model"
.venv/bin/python -m lkj.cli --online doctor --warmup

mkdir -p "$HOME/.local/bin"
cat >"$HOME/.local/bin/lkj" <<EOF
#!/usr/bin/env bash
exec "$PROJECT_DIR/.venv/bin/python" -m lkj.cli "\$@"
EOF
chmod +x "$HOME/.local/bin/lkj"

mkdir -p "$HOME/.local/share/applications"
cat >"$HOME/.local/share/applications/lkj.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=LKJ
Comment=Open LKJ voice-to-text settings
Exec=$HOME/.local/bin/lkj
Icon=audio-input-microphone
Terminal=false
Categories=Utility;AudioVideo;
Keywords=voice;transcription;hotkey;
EOF

mkdir -p "$HOME/.config/systemd/user"
cat >"$HOME/.config/systemd/user/lkj-daemon.service" <<EOF
[Unit]
Description=LKJ hotkey transcription daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=%h/.local/bin/lkj daemon
Restart=on-failure
RestartSec=2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
  systemctl --user daemon-reload
  systemctl --user enable --now lkj-daemon.service
  rm -f "$HOME/.config/autostart/lkj-daemon.desktop"
  echo "Daemon installed with systemd user service"
else
  mkdir -p "$HOME/.config/autostart"
  cat >"$HOME/.config/autostart/lkj-daemon.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=LKJ Daemon
Comment=Start LKJ hotkey daemon on login
Exec=$HOME/.local/bin/lkj daemon
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

  if ! pgrep -f "\.local/bin/lkj daemon" >/dev/null 2>&1; then
    nohup "$HOME/.local/bin/lkj" daemon >/dev/null 2>&1 &
  fi

  echo "Daemon added to desktop autostart"
fi

echo "Install complete"
echo "Open LKJ from app launcher/rofi (entry name: LKJ)"
