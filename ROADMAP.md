# lkj roadmap

`lkj` is now a Go rewrite: a tiny local speech-to-text bridge for agents.

## Milestone 1: Go foundation

- [x] Replace Python prototype with Go module scaffold.
- [x] Define STT backend interface.
- [x] Define output sink interface.
- [x] Add `whisper.cpp` subprocess backend.
- [x] Add stdout/file/HTTP sinks.
- [x] Add basic CLI.
- [ ] Add tests for CLI/config/pipeline.

## Milestone 2: CPU-only whisper.cpp path

- [ ] Document installing/building whisper.cpp.
- [ ] Add model discovery/config helpers.
- [ ] Add model download helper or docs.
- [ ] Improve transcript parsing from whisper.cpp output.
- [ ] Support quiet JSON/text output modes if available.

## Milestone 3: Audio capture

- [ ] Add cross-platform recorder interface.
- [ ] Implement microphone recording to WAV.
- [ ] Add `lkj once --seconds N`.
- [ ] Add device listing.
- [ ] Add input level/diagnostics.

## Milestone 4: Agent sinks

- [ ] Stabilize HTTP sink contract.
- [ ] Add WebSocket/event sink.
- [ ] Design `oi` integration.
- [ ] Add generic stdin/terminal sink.
- [ ] Add examples for talking to coding agents.

## Milestone 5: Daemon/listen mode

- [ ] Add `lkj listen` loop.
- [ ] Add push-to-talk abstraction.
- [ ] Add platform-specific hotkey providers later.
- [ ] Add `lkj serve` local API.

## Milestone 6: Embeddable package

- [ ] Expose public package API after internals stabilize.
- [ ] Make `lkj` usable as a library by `oi` or other Go agents.
- [ ] Keep CLI as thin wrapper over library.

## Later

- Clipboard and type-into-active-app sinks.
- Tray/desktop wrapper.
- Bundled whisper.cpp binaries.
- Optional GPU acceleration.
- Wake word / streaming transcription.
