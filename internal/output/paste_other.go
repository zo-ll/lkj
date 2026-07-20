//go:build !linux

package output

import (
	"context"
	"errors"
	"fmt"
	"os/exec"
	"runtime"
)

func pasteShortcut(ctx context.Context) error {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.CommandContext(ctx, "osascript", "-e", `tell application "System Events" to keystroke "v" using command down`)
	case "windows":
		cmd = exec.CommandContext(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", `Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("^v")`)
	default:
		return fmt.Errorf("paste output is not supported on %s", runtime.GOOS)
	}
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("send paste shortcut with %s: %w: %s", cmd.Path, err, output)
	}
	return nil
}

func newPasteShortcut() (func(context.Context) error, error) {
	if err := checkPasteShortcut(); err != nil {
		return nil, err
	}
	return pasteShortcut, nil
}

func checkPasteShortcut() error {
	switch runtime.GOOS {
	case "darwin":
		_, err := exec.LookPath("osascript")
		return err
	case "windows":
		_, err := exec.LookPath("powershell.exe")
		return err
	default:
		return errors.New("paste output is unavailable")
	}
}

func newPasteSender() (func(context.Context, string) error, error) {
	pressShortcut, err := newPasteShortcut()
	if err != nil {
		return nil, err
	}
	if err := CheckClipboard(); err != nil {
		return nil, err
	}
	return func(ctx context.Context, text string) error {
		if err := (Clipboard{}).Send(ctx, text); err != nil {
			return err
		}
		if err := pressShortcut(ctx); err != nil {
			return fmt.Errorf("paste transcript into focused application: %w", err)
		}
		return nil
	}, nil
}

func pasteText(ctx context.Context, text string) error {
	send, err := newPasteSender()
	if err != nil {
		return err
	}
	return send(ctx, text)
}

func checkPaste() error {
	_, err := newPasteSender()
	return err
}
