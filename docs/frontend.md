# Frontend considerations

`lkj` should support multiple frontend styles. The core should stay protocol-first and frontend-agnostic.

Core flow:

```text
trigger -> record -> transcribe locally -> route transcript
```

Triggers can come from:

- CLI command
- global hotkey
- HTTP request
- tray/menu-bar button
- future wake word
- future frontend wrapper

## Reference UX patterns

Apps in the WhisperFlow/open-whisper space usually follow one of two patterns.

### Hotkey dictation pattern

Common for daily voice input:

```text
background daemon -> global hotkey -> record -> transcribe -> paste/type/send
```

Typical features:

- background daemon
- global push-to-talk hotkey
- hold-to-talk or toggle-to-talk
- small status overlay while recording/transcribing
- tray/menu-bar settings
- transcript inserted into active app or sent to configured target

This is likely the best daily UX for `lkj`.

### GUI transcription pattern

Common for simple Whisper frontends:

```text
open app -> choose file/mic -> transcribe -> copy/export
```

Typical features:

- model picker
- input device picker
- record button
- file transcription
- transcript history
- copy/export actions

Useful, but less agent-native.

## Proposed frontend modes

### 1. CLI mode

Required baseline for scripts and agents.

```bash
lkj once --file input.wav --out stdout
lkj once --seconds 5 --out http --url http://localhost:8765/input
```

### 2. Daemon + hotkey mode

Best daily workflow.

```bash
lkj listen --hotkey alt+space --out clipboard
lkj listen --hotkey alt+space --out http --url http://localhost:8765/input
```

Recommended behavior:

- hold `alt+space` to record
- release to stop and transcribe
- `esc` cancels current recording
- support toggle mode as config option

### 3. Local server mode

Best generic agent integration.

```bash
lkj serve --addr localhost:8765
```

Possible API:

```text
POST /listen       start one recording session
POST /transcribe   transcribe provided audio/file
GET  /events       stream recording/transcription events
GET  /health       status
```

### 4. Local web UI

Good first visual frontend because it is cross-platform and simple.

```bash
lkj serve --ui
```

Possible UI:

- current state: idle / recording / transcribing
- selected backend/model
- selected output sink
- microphone test
- trigger test
- config editor
- transcript history

### 5. Native wrapper later

Options:

- Tauri: strongest cross-platform desktop/tray packaging, adds Rust/JS stack.
- Wails: Go-friendly desktop wrapper with web UI.
- Fyne: pure Go GUI, simpler but less polished.

Native wrapper should talk to `lkj` core through local API or library calls. It should not define the core architecture.

## Design rule

Do not bake hotkeys, tray, or GUI into the core pipeline.

Keep these separate:

```text
frontend trigger layer
core record/transcribe/route pipeline
output sink layer
```

That keeps `lkj` usable with any agent, any runtime, and any future UI.
