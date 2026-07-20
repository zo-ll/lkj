# lkj roadmap

`lkj` is now a Go rewrite: a tiny local speech-to-text bridge for agents.

## Milestone 1: Go foundation

- [x] Replace Python prototype with Go module scaffold.
- [x] Define STT backend interface.
- [x] Define output sink interface.
- [x] Add `whisper.cpp` subprocess backend.
- [x] Add stdout/file/HTTP sinks.
- [x] Add basic CLI.
- [x] Add tests for CLI/config/pipeline.
- [x] Add `setup` command for local config.
- [x] Add `doctor` dependency checks.

## Milestone 2: CPU-only whisper.cpp path

- [ ] Document installing/building whisper.cpp.
- [x] Add model discovery/config helpers.
- [x] Add tiny-model-first docs.
- [x] Suppress common silence/music hallucinations.
- [ ] Add model download helper or docs.
- [ ] Improve broader transcript parsing from whisper.cpp output.
- [ ] Support quiet JSON/text output modes if available.

## Milestone 3: Audio capture

- [x] Add cross-platform recorder interface.
- [x] Implement command-backed microphone recording to WAV.
- [x] Add `lkj once --seconds N`.
- [x] Add recorder device config/CLI override.
- [ ] Add device listing.
- [ ] Add input level/diagnostics.

## Milestone 4: Agent sinks

- [ ] Stabilize HTTP sink contract.
- [ ] Add WebSocket/event sink.
- [ ] Design generic agent integration contracts.
- [ ] Add generic stdin/terminal sink.
- [ ] Add examples for talking to coding agents.

## Milestone 5: Daemon/listen mode

- [x] Add `lkj listen` daemon.
- [x] Add local daemon control protocol.
- [ ] Add hold-to-talk abstraction.
- [x] Add toggle-to-talk mode.
- [x] Add cancel-current-recording action.
- [x] Add desktop state notifications.
- [ ] Add platform-specific hotkey providers later.
- [ ] Add `lkj serve` local API.

## Milestone 6: Frontend/UX exploration

- [ ] Keep core frontend-agnostic: triggers should call the same record/transcribe/route pipeline.
- [ ] Design CLI mode as baseline frontend.
- [ ] Design daemon + hotkey mode for daily use.
- [ ] Design local server mode for agents/tools.
- [ ] Evaluate local web UI for config/status.
- [ ] Evaluate native wrapper options: Tauri, Wails, Fyne.
- [ ] Decide whether tray/menu-bar and overlay belong in first desktop release.

See [docs/frontend.md](docs/frontend.md).

## Milestone 7: Protocol-first integration

- [ ] Stabilize generic integration protocols before exposing language-specific APIs.
- [ ] Support any agent/tool/runtime through HTTP, WebSocket, stdout/stdin, files, or subprocess pipes.
- [ ] Keep Go package API optional, not the primary integration path.

## Later

- [x] Clipboard sink.
- [x] Add keyboard-layout-safe active insertion through the Wayland RemoteDesktop portal.
- Tray/desktop wrapper.
- Bundled whisper.cpp binaries.
- Optional GPU acceleration.
- Wake word / streaming transcription.
