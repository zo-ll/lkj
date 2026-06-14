# lkj roadmap

`lkj` is now a Go rewrite: a tiny local speech-to-text bridge for agents.

## Milestone 1: Go foundation

- [x] Replace Python prototype with Go module scaffold.
- [x] Define STT backend interface.
- [x] Define output sink interface.
- [x] Add `whisper.cpp` subprocess backend.
- [x] Add optional Parakeet subprocess backend on separate branch.
- [x] Add stdout/file/HTTP sinks.
- [x] Add basic CLI.
- [x] Add tests for CLI/config/pipeline.

## Milestone 2: CPU-only whisper.cpp path

- [ ] Document installing/building whisper.cpp.
- [ ] Add model discovery/config helpers.
- [ ] Add model download helper or docs.
- [ ] Improve transcript parsing from whisper.cpp output.
- [ ] Support quiet JSON/text output modes if available.

## Branch: optional Parakeet backend

- [x] Keep Parakeet off `main` while the core matures.
- [x] Add Go subprocess backend contract for Parakeet.
- [x] Add optional Python/NeMo helper script.
- [ ] Smoke test with an installed Parakeet environment.
- [ ] Decide later whether this backend remains a branch, external helper, or documented plugin path.

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

- [ ] Add `lkj listen` loop.
- [ ] Add push-to-talk abstraction.
- [ ] Add hold-to-talk and toggle-to-talk modes.
- [ ] Add cancel-current-recording action.
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

- Clipboard and type-into-active-app sinks.
- Tray/desktop wrapper.
- Bundled whisper.cpp binaries.
- Optional GPU acceleration.
- Wake word / streaming transcription.
