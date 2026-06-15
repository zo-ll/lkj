# Windows backend scaffold

Windows desktop integration should stay behind `internal/desktop` so the core pipeline remains platform-neutral.

Current scaffold:

- `desktop.New()` selects a backend by build tag.
- Windows backend name: `windows`.
- Unsupported/non-Windows backend name: `unsupported`.
- Capability reporting is exposed through `lkj platform`.
- Windows clipboard support is implemented through PowerShell `Set-Clipboard`.
- Windows text injection, global hotkeys, tray, notifications, and microphone setup are placeholders returning `ErrNotImplemented`.

Current Windows audio path is still the existing recorder path:

```text
ffmpeg -f dshow -i audio=<device> ...
```

Future Windows work:

- replace PowerShell clipboard with native Win32 when needed
- add SendInput-based type-into-active-app sink
- add RegisterHotKey-based hotkey provider
- add Windows notification/tray support behind the same backend boundary
- add device listing for DirectShow/WASAPI input devices

Design rule: Windows code must not leak into pipeline/STT/output abstractions except through small interfaces.
