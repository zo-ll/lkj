package output

import (
	"context"
	"errors"
	"fmt"
	"os/exec"
	"runtime"
	"strings"
)

// Clipboard copies transcripts to the desktop clipboard.
type Clipboard struct{}

func (Clipboard) Send(ctx context.Context, text string) error {
	command, err := clipboardCommand(runtime.GOOS, exec.LookPath)
	if err != nil {
		return err
	}
	return runClipboard(ctx, command, text)
}

func runClipboard(ctx context.Context, command clipboardCmd, text string) error {
	cmd := exec.CommandContext(ctx, command.name, command.args...)
	cmd.Stdin = strings.NewReader(text)
	// Clipboard owners such as wl-copy and xclip fork a child that stays alive
	// while it owns the selection. Leaving os/exec capture pipes attached to
	// that child makes Wait block until the clipboard changes, which leaves the
	// daemon stuck in its transcribing state after the first utterance.
	cmd.Stdout = nil
	cmd.Stderr = nil
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("copy transcript with %s: %w", command.name, err)
	}
	return nil
}

type clipboardCmd struct {
	name string
	args []string
}

func clipboardCommand(goos string, lookPath func(string) (string, error)) (clipboardCmd, error) {
	switch goos {
	case "linux":
		candidates := []clipboardCmd{
			{name: "wl-copy"},
			{name: "xclip", args: []string{"-selection", "clipboard"}},
			{name: "xsel", args: []string{"--clipboard", "--input"}},
		}
		for _, candidate := range candidates {
			if _, err := lookPath(candidate.name); err == nil {
				return candidate, nil
			}
		}
		return clipboardCmd{}, errors.New("clipboard output requires wl-copy, xclip, or xsel")
	case "darwin":
		if _, err := lookPath("pbcopy"); err == nil {
			return clipboardCmd{name: "pbcopy"}, nil
		}
		return clipboardCmd{}, errors.New("clipboard output requires pbcopy")
	case "windows":
		if _, err := lookPath("powershell.exe"); err == nil {
			return clipboardCmd{name: "powershell.exe", args: []string{"-NoProfile", "-NonInteractive", "-Command", "$input | Set-Clipboard"}}, nil
		}
		return clipboardCmd{}, errors.New("clipboard output requires powershell.exe")
	default:
		return clipboardCmd{}, fmt.Errorf("clipboard output is not supported on %s", goos)
	}
}

func CheckClipboard() error {
	_, err := clipboardCommand(runtime.GOOS, exec.LookPath)
	return err
}
