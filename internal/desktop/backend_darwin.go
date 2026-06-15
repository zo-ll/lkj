//go:build darwin

package desktop

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
)

type macOSBackend struct{}

func New() Backend {
	return macOSBackend{}
}

func (macOSBackend) Name() string {
	return "macos"
}

func (macOSBackend) Capabilities() Capabilities {
	return Capabilities{
		Clipboard:       true,
		TypeText:        false,
		GlobalHotkey:    false,
		Notifications:   false,
		Tray:            false,
		MicrophoneSetup: false,
	}
}

func (macOSBackend) SetClipboard(ctx context.Context, text string) error {
	cmd := exec.CommandContext(ctx, "pbcopy")
	cmd.Stdin = bytes.NewBufferString(text)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		if stderr.Len() > 0 {
			return fmt.Errorf("set macos clipboard: %w: %s", err, stderr.String())
		}
		return fmt.Errorf("set macos clipboard: %w", err)
	}
	return nil
}

func (macOSBackend) TypeText(ctx context.Context, text string) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return ErrNotImplemented
}

func (macOSBackend) ListenHotkey(ctx context.Context, spec string, events chan<- HotkeyEvent) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return ErrNotImplemented
}
