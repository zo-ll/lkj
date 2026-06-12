# lkj roadmap

`lkj` is moving toward a local speech-to-text bridge for AI agents.

## Guiding principles

- Local STT first.
- Cross-platform design, even if Linux works first.
- Backends are replaceable.
- Outputs are replaceable.
- Agent workflows are first-class.
- Keep the core small.

## Milestone 0: Reframe the project

Status: planned / in progress

- Update README and docs with new project direction.
- Keep current Parakeet/Linux implementation documented as prototype.
- Define backend and output abstractions before adding more features.

## Milestone 1: Backend abstraction

Goal: make STT model/runtime pluggable.

Tasks:

- Define a minimal transcriber interface:

  ```python
  class Transcriber:
      def load(self) -> None: ...
      def transcribe_file(self, path) -> str: ...
      def unload(self) -> None: ...
  ```

- Rename current Parakeet implementation into a backend.
- Add config field for backend selection.
- Keep current behavior as default while the project transitions.

Expected result:

```json
{
  "stt_backend": "parakeet"
}
```

## Milestone 2: whisper.cpp backend

Goal: make `lkj` useful without NVIDIA/CUDA.

Tasks:

- Add backend that calls a local `whisper.cpp` binary.
- Add config for binary path and model path.
- Support basic model download instructions.
- Support CPU mode first.
- Later support Metal/CUDA/Vulkan builds where available.

Expected result:

```json
{
  "stt_backend": "whispercpp",
  "whispercpp_binary": "/path/to/whisper-cli",
  "whispercpp_model": "/path/to/ggml-base.en.bin"
}
```

## Milestone 3: Output abstraction

Goal: send transcripts to different targets.

Tasks:

- Define output target interface.
- Move clipboard/log behavior behind output targets.
- Add stdout output.
- Add HTTP webhook output.

Targets:

- clipboard
- transcript log
- stdout
- HTTP webhook
- keyboard typing later
- terminal stdin later

Expected result:

```bash
lkj once --seconds 5 --output stdout
lkj listen --output http --url http://localhost:8765/input
```

## Milestone 4: Agent integrations

Goal: make speaking to agents natural.

Initial integrations:

- generic HTTP agent endpoint
- generic terminal/stdin adapter
- optional adapters for tools like `pi`, `codex`, `aider`, or `opencode`

Possible commands:

```bash
lkj agent -- pi
lkj agent -- codex
lkj listen --output http --url http://localhost:8765/input
```

## Milestone 5: Cross-platform desktop

Goal: support macOS, Windows, and Linux.

Tasks:

- Keep core platform-neutral.
- Isolate hotkeys, typing, tray, and notifications per platform.
- Keep clipboard as universal fallback.
- Decide whether to keep Python packaging or add a Tauri/native wrapper.

Platform concerns:

- macOS: Accessibility permissions, microphone permissions, Metal whisper.cpp builds.
- Windows: microphone permissions, SendInput typing, packaged binaries.
- Linux: Wayland/X11 differences, `wtype`/`ydotool`/`xdotool`.

## Milestone 6: Desktop polish

Goal: make it pleasant as a daily tool.

Tasks:

- Tray/status indicator.
- Recording/transcribing state.
- Input level meter.
- Model manager.
- Backend selector.
- Startup on login.
- Better install/uninstall.

## Future ideas

- Streaming transcription.
- Wake word mode.
- Prefix routing: `agent`, `terminal`, `note`.
- AI cleanup/rewrite mode after transcription.
- Custom vocabulary.
- Local command grammar.
- MCP-style bridge for agents.
