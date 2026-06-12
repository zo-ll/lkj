# lkj

Local speech-to-text bridge for AI agents.

`lkj` started as a Linux push-to-talk dictation app. The new direction is broader: a cross-platform app that lets you talk to local and remote agents using local speech-to-text models.

## Vision

```text
microphone -> local STT model -> transcript -> agent / app / output target
```

Goals:

- local-first speech-to-text
- push-to-talk by default
- cross-platform desktop support over time
- pluggable STT backends
- pluggable output targets
- simple integrations for coding agents and local LLM tools

Non-goals:

- cloud-required transcription
- Linux-only design
- one hard-coded model/runtime
- replacing ASR engines like whisper.cpp

## Current state

Today `lkj` is an early Linux desktop app using NVIDIA Parakeet through NeMo.

Current features:

- GUI settings app
- background hotkey daemon
- manual stop or optional auto-stop on silence
- desktop notifications
- clipboard auto-copy
- local transcript log
- NVIDIA Parakeet backend

Current limits:

- Linux-focused
- CUDA/NVIDIA-focused
- Python/NeMo install is heavy
- output is mostly clipboard/log-oriented

## Target architecture

```text
lkj core
  audio capture
  session control
  config

STT backends
  whisper.cpp
  Parakeet / NeMo
  faster-whisper
  future local models

output targets
  clipboard
  type into active app
  stdout
  HTTP webhook
  WebSocket
  terminal stdin
  agent adapters
```

Core idea: `lkj` should not be only a dictation app. Dictation is one output target. Agent control is the main use case.

## Example future commands

```bash
lkj once --seconds 5 --output stdout
lkj listen --backend whispercpp --output clipboard
lkj listen --output http --url http://localhost:8765/input
lkj agent -- pi
lkj agent -- codex
```

## Agent use cases

- talk to a coding agent in a terminal
- send voice prompts to a local agent HTTP endpoint
- dictate into browser-based chat apps
- trigger command routing with prefixes like `agent`, `terminal`, or `note`
- keep all speech recognition local

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Current install

Linux/NVIDIA path still works as the first prototype.

```bash
git clone https://github.com/zo-ll/lkj
cd lkj
./scripts/install.sh
```

## Current commands

```bash
lkj                 # open settings GUI
lkj gui             # open settings GUI
lkj daemon          # run background daemon in foreground
lkj once --seconds 5
lkj doctor
lkj doctor --warmup
```

## Configuration

Config path: `~/.config/lkj/config.json`

Important current fields:

- `model_name`: default `nvidia/parakeet-tdt-0.6b-v2`
- `device`: `cuda` or `cpu`
- `input_device`: optional sounddevice input
- `preload_model`: load and warm model at daemon startup
- `unload_model_after_seconds`: unload model after idle seconds
- `start_hotkey`: default `alt+space`
- `stop_hotkey`: optional separate stop key
- `auto_stop_enabled`: manual stop by default
- `offline_only`: avoid network model fetch after cache
- `transcript_log_path`: local transcript log path

## Project status

Early prototype. Direction likely to change. Contributions and experiments should align with the roadmap: backend abstraction, output targets, whisper.cpp support, and agent integrations.
