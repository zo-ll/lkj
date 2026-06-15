package desktop

import (
	"context"
	"errors"
)

var ErrNotImplemented = errors.New("desktop backend feature not implemented")

// Capabilities describes which desktop integration points a platform backend supports.
type Capabilities struct {
	Clipboard       bool
	TypeText        bool
	GlobalHotkey    bool
	Notifications   bool
	Tray            bool
	MicrophoneSetup bool
}

// HotkeyEvent is emitted by future global hotkey providers.
type HotkeyEvent struct {
	Spec   string
	Action string
}

// Backend isolates platform-specific desktop behavior from the core pipeline.
type Backend interface {
	Name() string
	Capabilities() Capabilities
	SetClipboard(ctx context.Context, text string) error
	TypeText(ctx context.Context, text string) error
	ListenHotkey(ctx context.Context, spec string, events chan<- HotkeyEvent) error
}
