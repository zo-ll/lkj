# lkj

Local-only push-to-talk voice-to-text app using NVIDIA Parakeet.

## Features

- Local transcription only after first model cache.
- Push-to-talk flow with clipboard auto-copy.
- Transcript log saved locally.
- Doctor command for setup checks.

## Requirements

- Linux desktop.
- NVIDIA GPU + driver with CUDA runtime.
- Python 3.10-3.12 (NeMo ASR compatibility window).
- `portaudio` runtime for `sounddevice`.

## Quick Start

```bash
cd /home/az/projects/lkj
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -e .
```

First run (allow network one time for model download):

```bash
lkj --online once --seconds 5
```

Daily run (offline by default):

```bash
lkj run
```

Default key: hold `f8` to record, release to transcribe.

## Configuration

Create `~/.config/lkj/config.json` from `config.example.json`.

Fields:

- `model_name`: default `nvidia/parakeet-tdt-0.6b-v2`
- `device`: `cuda` or `cpu`
- `sample_rate`: default `16000`
- `push_key`: default `f8`
- `min_seconds`: minimum speech duration before inference
- `offline_only`: `true` for no network model fetch
- `transcript_log_path`: local transcript log path

## Commands

- `lkj run` - push-to-talk mode.
- `lkj once --seconds 5` - one-shot record + transcribe.
- `lkj doctor` - environment checks.
- `lkj doctor --warmup` - checks + model load test.

## Troubleshooting

- No hotkey events on Wayland: run under X11 session or grant input permissions.
- `cuda=False` in doctor output: reinstall CUDA torch wheel.
- Model load fails in offline mode: run one online warmup (`--online`).

## Status

- [x] Repo scaffold
- [x] Core ASR pipeline
- [x] Push-to-talk recorder
- [x] Clipboard + logging
- [x] Diagnostics + docs
