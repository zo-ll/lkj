//go:build linux

package output

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// eitype uses the desktop RemoteDesktop portal and libei. Unlike a raw
// uinput device, this path is supported by compositors such as KWin and uses
// the compositor's active keyboard layout.
func newPasteSender() (func(context.Context, string) error, error) {
	if os.Getenv("WAYLAND_DISPLAY") == "" {
		return nil, errors.New("paste output on Linux currently requires a Wayland session and eitype")
	}
	path, err := findEIType()
	if err != nil {
		return nil, errors.New("paste output requires eitype (install with `cargo install eitype`)")
	}
	// Establish or restore the portal session before recording begins. On the
	// first run this is where the compositor presents its authorization dialog;
	// doing it at daemon startup avoids holding a completed transcript hostage
	// behind a permission prompt.
	authorizeCtx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	if err := runEIType(authorizeCtx, path, ""); err != nil {
		return nil, fmt.Errorf("authorize focused-app insertion: %w", err)
	}
	return func(ctx context.Context, text string) error {
		return runEIType(ctx, path, text)
	}, nil
}

func runEIType(ctx context.Context, path, text string) error {
	cmd := exec.CommandContext(ctx, path, "--", text)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("insert transcript with eitype: %w: %s", err, output)
	}
	return nil
}

func findEIType() (string, error) {
	if path, err := exec.LookPath("eitype"); err == nil {
		return path, nil
	}
	executable, err := os.Executable()
	if err != nil {
		return "", err
	}
	sibling := filepath.Join(filepath.Dir(executable), "eitype")
	info, err := os.Stat(sibling)
	if err != nil || info.IsDir() || info.Mode()&0o111 == 0 {
		return "", errors.New("eitype not found")
	}
	return sibling, nil
}

func pasteText(ctx context.Context, text string) error {
	send, err := newPasteSender()
	if err != nil {
		return err
	}
	return send(ctx, text)
}

func checkPaste() error {
	if os.Getenv("WAYLAND_DISPLAY") == "" {
		return errors.New("paste output on Linux currently requires a Wayland session and eitype")
	}
	_, err := findEIType()
	return err
}
