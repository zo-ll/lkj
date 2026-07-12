# lkj

Tiny local voice input bridge for agents.

`lkj` is being rewritten in Go. The old Python/Linux/Parakeet prototype is kept in git history, but the project direction is now:

```text
microphone or wav -> local STT backend -> transcript -> agent/output sink
```

Designed as a standalone tool: agents can consume its transcripts over generic sinks like stdout, HTTP, WebSocket, or stdin. No specific agent runtime should be required.

## Goals

- CPU-only support as a first-class path.
- Go binary, no Python environment.
- Local speech-to-text by default.
- `whisper.cpp` backend first.
- `ggml-tiny.en.bin` is the recommended first model on memory-constrained machines.
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
- Command-backed microphone recording with `ffmpeg`, `arecord`, or SoX `rec`.
- Output sink interface.
- stdout, file, and HTTP sinks.
- Pipeline for `wav -> transcript -> sink`.
- `setup` command for local config.
- `doctor` checks for runtime dependencies.
- Basic silence/music-caption suppression for Whisper hallucinations.
- Background daemon with local `toggle`, `cancel`, `status`, and `stop` controls.
- Clipboard output on Linux, macOS, and Windows.
- Desktop notifications for recording, transcription, clipboard delivery, and errors.
- Optional active-window typing on Linux through `/dev/uinput`.

Not implemented yet:

- push-to-talk hotkeys.
- clipboard sink.
- generic agent adapters.
- bundled whisper.cpp binaries/models.

Microphone recording is implemented through local recorder commands. Prefer `ffmpeg` for cross-platform use, or install a platform fallback:

- `ffmpeg` on Linux/macOS/Windows.
- `arecord` on Linux.
- `rec` from SoX.

## Quick start

Build:

```bash
go build -o bin/lkj ./cmd/lkj
```

Install for the current user:

```bash
make install
```

This installs `lkj` to `~/.local/bin/lkj` by default. Make sure `~/.local/bin` is on `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
lkj version
```

Use a custom install directory:

```bash
LKJ_INSTALL_DIR=/custom/bin make install
```

Uninstall:

```bash
make uninstall
```

Update by pulling the repo and running `make install` again.

Transcribe an existing WAV with `whisper.cpp`:

```bash
bin/lkj once \
  --file sample.wav \
  --model /path/to/ggml-tiny.en.bin \
  --whisper-bin /path/to/whisper-cli \
  --threads 2 \
  --out stdout
```

Write a local config using discovered paths:

```bash
bin/lkj setup
```

Check dependencies and config:

```bash
bin/lkj doctor
```

Optionally test microphone capture during doctor:

```bash
bin/lkj doctor --record-test 2
```

Record microphone audio first, then transcribe it:

```bash
bin/lkj once --seconds 5
```

## Voice input daemon

Start `lkj` in the background. The daemon records from the configured device,
transcribes locally, and copies the result to the clipboard:

```bash
lkj start
lkj status
```

Toggle once to start recording and again to stop, transcribe, and copy:

```bash
lkj toggle
# speak
lkj toggle
```

Cancel the current recording without transcribing, or stop the daemon:

```bash
lkj cancel
lkj stop
```

`lkj listen` runs the same service in the foreground for debugging. Daemon logs
are written to `~/.cache/lkj/daemon.log`. The control socket defaults to
`$XDG_RUNTIME_DIR/lkj.sock`; override it with `--socket` or `LKJ_SOCKET`.

### Bind a global toggle shortcut

On KDE Plasma:

1. Open **System Settings → Keyboard → Shortcuts**.
2. Add a new command/application shortcut.
3. Set its command to `/home/az/.local/bin/lkj toggle`.
4. Assign `Ctrl+Alt+B`.

Start the daemon once after login with `lkj start`, press the shortcut, speak,
and press it again. Notifications show each state change. When the completion
notification appears, paste the transcript anywhere with `Ctrl+V`.

Clipboard is the daemon default. To restore direct active-window typing, start
it with `lkj start --out type`.

On Linux, optional active typing uses the kernel virtual-input device directly and adds
no package dependency. `lkj doctor` reports whether `/dev/uinput` is writable.
The current key mapping follows a US keyboard layout; non-ASCII text uses the
standard Linux Unicode-entry sequence where the focused toolkit supports it.

Send transcript to an agent HTTP endpoint:

```bash
bin/lkj once \
  --file sample.wav \
  --model /path/to/ggml-tiny.en.bin \
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
lkj once --seconds 5
lkj start
lkj toggle
lkj status
lkj cancel
lkj stop
lkj listen
lkj setup
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
  "model_path": "models/ggml-tiny.en.bin",
  "threads": 2,
  "record_device": "default",
  "output": "stdout",
  "http_url": "http://localhost:8765/input"
}
```

CLI flags override config.

Use `threads` / `--threads` to limit `whisper.cpp` CPU usage on constrained machines. Start with `ggml-tiny.en.bin` and a low thread count like `2`. Larger models such as `base.en` may be too heavy on memory-constrained systems.

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

Frontend/UX notes live in [docs/frontend.md](docs/frontend.md).
