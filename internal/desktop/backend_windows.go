//go:build windows

package desktop

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
)

type windowsBackend struct{}

func New() Backend {
	return windowsBackend{}
}

func (windowsBackend) Name() string {
	return "windows"
}

func (windowsBackend) Capabilities() Capabilities {
	return Capabilities{
		Clipboard:       true,
		TypeText:        false,
		GlobalHotkey:    false,
		Notifications:   false,
		Tray:            false,
		MicrophoneSetup: false,
	}
}

func (windowsBackend) SetClipboard(ctx context.Context, text string) error {
	cmd := exec.CommandContext(ctx, "powershell.exe", "-NoProfile", "-Command", "Set-Clipboard -Value ([Console]::In.ReadToEnd())")
	cmd.Stdin = bytes.NewBufferString(text)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		if stderr.Len() > 0 {
			return fmt.Errorf("set windows clipboard: %w: %s", err, stderr.String())
		}
		return fmt.Errorf("set windows clipboard: %w", err)
	}
	return nil
}

func (windowsBackend) TypeText(ctx context.Context, text string) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return ErrNotImplemented
}

func (windowsBackend) ListenHotkey(ctx context.Context, spec string, events chan<- HotkeyEvent) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return ErrNotImplemented
}
