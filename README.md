# lkj

Tiny local voice input bridge for agents.

`lkj` is being rewritten in Go. The old Python/Linux/Parakeet prototype is kept in git history, but the project direction is now:

```text
microphone or wav -> local STT backend -> transcript -> agent/output sink
```

Designed to pair well with [`oi`](https://github.com/zo-ll/oi): minimal, embeddable, local-first agent tooling.

## Goals

- CPU-only support as a first-class path.
- Go binary, no Python environment.
- Local speech-to-text by default.
- `whisper.cpp` backend first.
- Embeddable Go package for agents.
- CLI/daemon/server before GUI.
- Cross-platform design.

## Current scaffold

Implemented now:

- Go module skeleton.
- CLI entrypoint.
- Config loader.
- STT backend interface.
- `whisper.cpp` subprocess backend.
- Output sink interface.
- stdout, file, and HTTP sinks.
- Pipeline for `wav -> transcript -> sink`.

Not implemented yet:

- live microphone recording.
- push-to-talk hotkeys.
- clipboard sink.
- `oi` integration.
- bundled whisper.cpp binaries/models.

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

`once --seconds` is reserved for upcoming microphone recording.

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
internal/stt        transcriber interface + whisper.cpp backend
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
