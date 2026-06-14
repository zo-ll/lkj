# lkj

Tiny local voice input bridge for agents.

`lkj` is being rewritten in Go. The old Python/Linux/Parakeet prototype is kept in git history, but the project direction is now:

```text
microphone or wav -> local STT backend -> transcript -> agent/output sink
```

Designed as a standalone tool: agents can consume its transcripts over generic sinks like stdout, HTTP, WebSocket, or stdin. No specific agent runtime should be required.

## Goals

- CPU-only support as a first-class path.
- Go binary by default, no Python environment unless the optional Parakeet helper is selected.
- Local speech-to-text by default.
- `whisper.cpp` backend by default.
- Optional Parakeet backend on the `parakeet-backend` branch.
- Protocol-first integration for any agent/tool/runtime.
- CLI/daemon/server before GUI.
- Cross-platform design.

## Current scaffold

Implemented now:

- Go module skeleton.
- CLI entrypoint.
- Config loader.
- STT backend interface.
- `whisper.cpp` subprocess backend.
- Optional Parakeet subprocess backend.
- Output sink interface.
- stdout, file, and HTTP sinks.
- Pipeline for `wav -> transcript -> sink`.

Not implemented yet:

- push-to-talk hotkeys.
- clipboard sink.
- generic agent adapters.
- bundled whisper.cpp binaries/models.

Microphone recording is implemented through local recorder commands. Prefer `ffmpeg` for cross-platform use, or install a platform fallback:

- `ffmpeg` on Linux/macOS.
- `arecord` on Linux.
- `rec` from SoX.

## Quick start

Build:

```bash
go build -o bin/lkj ./cmd/lkj
```

Transcribe an existing WAV with `whisper.cpp`:

```bash
bin/lkj once \
  --file sample.wav \
  --model /path/to/ggml-base.en.bin \
  --whisper-bin /path/to/whisper-cli \
  --out stdout
```

Transcribe an existing WAV with Parakeet on this branch:

```bash
bin/lkj once \
  --backend parakeet \
  --file sample.wav \
  --parakeet-command "python3 scripts/parakeet_transcribe.py" \
  --parakeet-model nvidia/parakeet-tdt-0.6b-v2 \
  --parakeet-device cuda \
  --out stdout
```

Parakeet is optional and requires a Python environment with PyTorch and NVIDIA NeMo installed. The Go binary does not depend on Python unless `--backend parakeet` is selected.

Record microphone audio first, then transcribe it:

```bash
bin/lkj once \
  --seconds 5 \
  --model /path/to/ggml-base.en.bin \
  --whisper-bin /path/to/whisper-cli \
  --out stdout
```

Choose a recorder input device when the platform default is wrong:

```bash
bin/lkj once --seconds 5 --device default --model /path/to/ggml-base.en.bin
```

Send transcript to an agent HTTP endpoint:

```bash
bin/lkj once \
  --file sample.wav \
  --model /path/to/ggml-base.en.bin \
  --out http \
  --url http://localhost:8765/input
```

HTTP body:

```json
{"text":"transcribed text"}
```

## Commands

```bash
lkj version
lkj once --file input.wav --model model.bin --out stdout
lkj doctor
```

`once --seconds` records microphone audio to a temporary WAV before transcription.

## Config

Default path:

```text
~/.config/lkj/config.json
```

Example:

```json
{
  "stt_backend": "whispercpp",
  "whisper_bin": "whisper-cli",
  "model_path": "models/ggml-base.en.bin",
  "parakeet_command": "python3 scripts/parakeet_transcribe.py",
  "parakeet_model": "nvidia/parakeet-tdt-0.6b-v2",
  "parakeet_device": "cuda",
  "parakeet_offline": true,
  "record_device": "default",
  "output": "stdout",
  "http_url": "http://localhost:8765/input"
}
```

CLI flags override config.

## Architecture

```text
cmd/lkj             CLI
internal/config     JSON config
internal/audio      recorder interface and wav source
internal/stt        transcriber interface + whisper.cpp and optional Parakeet backends
internal/output     sinks: stdout/file/http/clipboard later
internal/pipeline   orchestration
```

Core interfaces:

```go
type Transcriber interface {
    Transcribe(ctx context.Context, wavPath string) (string, error)
}

type Sink interface {
    Send(ctx context.Context, text string) error
}
```

## Roadmap

See [ROADMAP.md](ROADMAP.md).

Frontend/UX notes live in [docs/frontend.md](docs/frontend.md).
