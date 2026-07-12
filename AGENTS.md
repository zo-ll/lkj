# Agent handoff: lkj

## Current direction

`lkj` is a Go rewrite of an old Python prototype.

Project identity:

> Tiny local voice input bridge for any agent/tool/runtime.

Core flow:

```text
trigger -> record audio -> local STT -> route transcript to sink
```

Important constraints:

- Do not make `lkj` depend on `oi` or any specific agent runtime.
- Do not frame it as Go-agents-only.
- Integration should be protocol-first: HTTP, WebSocket, stdout/stdin, files, subprocess pipes.
- CPU-only support is first-class.
- `whisper.cpp` is the first target backend.
- Frontend must stay separate from core pipeline.

## Current implementation

Language: Go

Module:

```text
github.com/zo-ll/lkj
```

Current files:

```text
cmd/lkj             CLI
internal/audio      audio source interface; existing WAV and command-backed recorders
internal/config     JSON config loader
internal/stt        Transcriber interface; whisper.cpp subprocess backend
internal/output     Sink interface; stdout/file/HTTP/clipboard/type sinks and notifications
internal/pipeline   source -> transcriber -> sink orchestration
internal/daemon     local socket daemon and toggle state machine
```

Working command shape:

```bash
go build -o bin/lkj ./cmd/lkj

bin/lkj once \
  --file sample.wav \
  --model /path/to/ggml-base.en.bin \
  --whisper-bin /path/to/whisper-cli \
  --out stdout
```

`once --seconds` records through ffmpeg, arecord, or SoX. `start` launches the
background daemon; `toggle` starts/stops an utterance and routes its transcript.

## Verified commands

Before handoff, this worked:

```bash
go test ./...
go build -o bin/lkj ./cmd/lkj
./bin/lkj version
./bin/lkj doctor
```

## Docs to read first

1. `README.md` - project identity and usage.
2. `ROADMAP.md` - milestones.
3. `docs/frontend.md` - frontend/hotkey/UI considerations.
4. GitHub issues - current work queue.

## Current GitHub issues

Known issues created:

- #2 Define STT backend abstraction
- #3 Add whisper.cpp backend
- #4 Define output target abstraction
- #5 Add HTTP webhook output for agent integrations
- #6 Plan cross-platform desktop support
- #7 Implement Go microphone recording
- #8 Design generic agent integration contracts
- #9 Design frontend modes and trigger architecture
- #10 Implement listen mode with push-to-talk semantics
- #11 Evaluate frontend wrapper options

Some early issues (#2-#5) overlap with scaffold work and may need closing/updating after review.

## Best next tasks

Recommended next task:

1. Improve device listing and input diagnostics.
2. Add keyboard-layout-aware active typing.
3. Improve whisper.cpp structured output parsing.
4. Add tests for CLI error and setup paths.

Alternative next task:

1. Improve `whisper.cpp` backend output parsing.
2. Document installing/building whisper.cpp.
3. Add model path discovery/config helpers.

Frontend task later:

1. Implement `lkj listen`.
2. Add hotkey abstraction.
3. Support hold-to-talk and toggle-to-talk.
4. Keep platform-specific hotkey code isolated.

## Design notes

Keep these layers separate:

```text
frontend trigger layer
core record/transcribe/route pipeline
output sink layer
```

Do not bake GUI, tray, hotkeys, or any one agent protocol into the core.

The core should be usable from:

- CLI
- daemon/listen mode
- local HTTP server
- future web UI
- future native wrapper
- arbitrary external agents/tools

## Frontend stance

Likely UX direction:

- CLI first.
- Daemon + global hotkey for daily use.
- Local server API for agents/tools.
- Local web UI for first visual frontend.
- Tauri/Wails/Fyne decision later.

Recommended hotkey behavior:

- hold-to-talk default if feasible.
- toggle-to-talk as option.
- cancel current recording action.

## Avoid

- Reintroducing Python stack as primary implementation.
- Making Parakeet/NVIDIA required.
- Making `oi` a dependency.
- Making only Go agents first-class.
- Starting with GUI before core recording/STT/sink pipeline works.
