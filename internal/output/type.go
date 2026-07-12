package output

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"runtime"
)

// Type sends text as keyboard input to the currently focused application.
type Type struct{}

func (Type) Send(ctx context.Context, value string) error {
	var nativeErr error
	if runtime.GOOS == "linux" {
		if err := typeLinux(ctx, value); err == nil {
			return nil
		} else {
			nativeErr = err
		}
	}
	command, err := typingCommand(runtime.GOOS, os.Getenv("WAYLAND_DISPLAY") != "", exec.LookPath, value)
	if err != nil {
		if nativeErr != nil {
			return fmt.Errorf("Linux virtual keyboard unavailable (%v); %w", nativeErr, err)
		}
		return err
	}
	cmd := exec.CommandContext(ctx, command.name, command.args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("type transcript with %s: %w: %s", command.name, err, output)
	}
	return nil
}

// CheckType reports whether active-window typing is available without sending
// any keyboard input.
func CheckType() error {
	if runtime.GOOS == "linux" {
		device, err := os.OpenFile("/dev/uinput", os.O_WRONLY, 0)
		if err == nil {
			return device.Close()
		}
	}
	_, err := typingCommand(runtime.GOOS, os.Getenv("WAYLAND_DISPLAY") != "", exec.LookPath, "")
	return err
}

type typeCommand struct {
	name string
	args []string
}

func typingCommand(goos string, wayland bool, lookPath func(string) (string, error), text string) (typeCommand, error) {
	switch goos {
	case "linux":
		if wayland {
			if _, err := lookPath("wtype"); err == nil {
				return typeCommand{name: "wtype", args: []string{text}}, nil
			}
		}
		if _, err := lookPath("xdotool"); err == nil {
			return typeCommand{name: "xdotool", args: []string{"type", "--clearmodifiers", "--delay", "0", "--", text}}, nil
		}
		if _, err := lookPath("wtype"); err == nil {
			return typeCommand{name: "wtype", args: []string{text}}, nil
		}
		return typeCommand{}, errors.New("typing output requires wtype (Wayland) or xdotool (X11)")
	case "darwin":
		if _, err := lookPath("osascript"); err != nil {
			return typeCommand{}, errors.New("typing output requires osascript")
		}
		script := `on run argv
tell application "System Events" to keystroke (item 1 of argv)
end run`
		return typeCommand{name: "osascript", args: []string{"-e", script, text}}, nil
	case "windows":
		if _, err := lookPath("powershell.exe"); err != nil {
			return typeCommand{}, errors.New("typing output requires powershell.exe")
		}
		script := `Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait($args[0])`
		return typeCommand{name: "powershell.exe", args: []string{"-NoProfile", "-NonInteractive", "-Command", script, text}}, nil
	default:
		return typeCommand{}, fmt.Errorf("typing output is not supported on %s", goos)
	}
}
