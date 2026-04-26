# lkj

Local-first hotkey voice-to-text app using NVIDIA Parakeet.

## Features

- One-command install script for desktop setup.
- GUI settings app (launch from `lkj` or app launcher/rofi).
- Background hotkey daemon (no terminal needed for daily use).
- Manual stop by default, with optional auto-stop on silence.
- Desktop notifications when recording starts and stops.
- Clipboard auto-copy and local transcript log.

## Requirements

- Linux desktop.
- NVIDIA GPU + driver with CUDA runtime.
- Python 3.10-3.12 (NeMo ASR compatibility window).
- `portaudio` runtime for `sounddevice`.

## Install

```bash
git clone https://github.com/zo-ll/lkj
cd lkj
./scripts/install.sh
```

What install does:

- Creates `.venv` and installs dependencies.
- Runs one-time online warmup to cache model files.
- Installs `lkj` launcher to `~/.local/bin/lkj`.
- Adds `LKJ` desktop entry for app launcher/rofi.
- Starts `lkj-daemon` immediately after install, but does not enable auto-start on login.

## Daily usage

- Open settings from app launcher/rofi (`LKJ`) or run `lkj`.
- In settings, choose `Input device` from the dropdown list (or type a custom value).
- Recording does not start when opening settings.
- Press `start_hotkey` to begin recording.
- By default, press `start_hotkey` again to stop manually.
- Optionally enable auto-stop in settings to stop on trailing silence.
- If `stop_hotkey` is set, press it to stop immediately.
- Notifications show when recording starts and stops.
- Default mode prioritizes responsiveness: model preloads on startup and stays loaded.
- To reduce idle power later, disable preload and set a non-zero idle unload timeout.

## Configuration

Config path: `~/.config/lkj/config.json`

Fields:

- `model_name`: default `nvidia/parakeet-tdt-0.6b-v2`
- `device`: `cuda` or `cpu`
- `input_device`: optional sounddevice input (e.g. `pulse`, `default`, or device name)
- `preload_model`: load and warm model at daemon startup (`true` by default)
- `unload_model_after_seconds`: unload model after idle seconds (`0` disables unload, default)
- `daemon_poll_seconds`: daemon loop interval (`0.2` default)
- `sample_rate`: default `16000`
- `channels`: default `1`
- `start_hotkey`: default `alt+space`
- `stop_hotkey`: optional separate stop key, default empty
- `auto_stop_enabled`: `false` by default (manual stop mode)
- `min_seconds`: minimum speech duration before inference
- `auto_stop_silence_seconds`: trailing silence before auto-stop
- `silence_threshold`: amplitude threshold used for silence detection
- `offline_only`: `true` for no network model fetch after cache
- `remove_fillers`: omit hesitation words like `uh`, `um`, and `ah` from transcripts (`true` by default)
- `transcript_log_path`: local transcript log path

## Commands

```bash
lkj                 # open settings GUI
lkj gui             # open settings GUI
lkj daemon          # run background daemon in foreground
lkj once --seconds 5
lkj doctor
lkj doctor --warmup
```

## Troubleshooting

- Hotkeys not working: run `systemctl --user status lkj-daemon.service`.
- No hotkey events on Wayland: run under X11 session or grant input permissions.
- Hotkey conflict with desktop shortcuts: change `start_hotkey`/`stop_hotkey`.
- No speech detected repeatedly: set `input_device` to `pulse` in settings and retry.
- If idle power is too high, set `preload_model=false` and use a non-zero `unload_model_after_seconds`.
- Accuracy for non-English speech may be limited with the default Parakeet model.
- `cuda=False` in doctor output: reinstall CUDA torch wheel.
- Model load fails in offline mode: run one online warmup (`lkj --online doctor --warmup`).

## Status

- [x] Repo scaffold
- [x] Core ASR pipeline
- [x] Push-to-talk recorder
- [x] Clipboard + logging
- [x] Diagnostics + docs
- [x] GUI settings app
- [x] Desktop installer and launcher
- [x] Background daemon with notifications and auto-stop
