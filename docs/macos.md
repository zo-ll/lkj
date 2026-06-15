# macOS backend scaffold

macOS desktop integration should stay behind `internal/desktop` so the core pipeline remains platform-neutral.

Current scaffold:

- `desktop.New()` selects a backend by build tag.
- macOS backend name: `macos`.
- Unsupported/non-macOS backend name: `unsupported`.
- Capability reporting is exposed through `lkj platform`.
- macOS clipboard support is implemented through `pbcopy`.
- Text injection, global hotkeys, tray/menu-bar, notifications, and microphone setup are placeholders returning `ErrNotImplemented`.

Current macOS audio path is the existing recorder path:

```text
ffmpeg -f avfoundation -i <device> ...
```

Default device is `:0`. Real devices can be listed with:

```bash
ffmpeg -f avfoundation -list_devices true -i ""
```

macOS permissions to account for later:

- Microphone permission for recording.
- Accessibility permission for type-into-active-app / global event taps.
- Automation permission if AppleScript or app control is used.

Future macOS work:

- replace `pbcopy` with native clipboard only if needed
- add CGEvent/Accessibility-based type-into-active-app sink
- add global hotkey provider
- add menu-bar/tray support behind the same backend boundary
- add avfoundation device listing command

Design rule: macOS code must not leak into pipeline/STT/output abstractions except through small interfaces.
