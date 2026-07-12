package output

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"testing"
	"time"
)

func TestClipboardCommandPrefersWayland(t *testing.T) {
	got, err := clipboardCommand("linux", clipboardCommands("wl-copy", "xclip"))
	if err != nil {
		t.Fatal(err)
	}
	want := clipboardCmd{name: "wl-copy"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("command = %#v, want %#v", got, want)
	}
}

func TestRunClipboardDoesNotWaitForForkedOwner(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("shell helper is Unix-only")
	}
	script := filepath.Join(t.TempDir(), "clipboard-owner")
	if err := os.WriteFile(script, []byte("#!/bin/sh\n(sleep 2) &\nexit 0\n"), 0o700); err != nil {
		t.Fatal(err)
	}
	started := time.Now()
	if err := runClipboard(context.Background(), clipboardCmd{name: script}, "text"); err != nil {
		t.Fatal(err)
	}
	if elapsed := time.Since(started); elapsed > time.Second {
		t.Fatalf("clipboard send waited for forked owner: %s", elapsed)
	}
}

func TestClipboardCommandFallsBackToXsel(t *testing.T) {
	got, err := clipboardCommand("linux", clipboardCommands("xsel"))
	if err != nil {
		t.Fatal(err)
	}
	want := clipboardCmd{name: "xsel", args: []string{"--clipboard", "--input"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("command = %#v, want %#v", got, want)
	}
}

func TestClipboardCommandReportsMissingTool(t *testing.T) {
	if _, err := clipboardCommand("linux", clipboardCommands()); err == nil {
		t.Fatal("expected error")
	}
}

func clipboardCommands(names ...string) func(string) (string, error) {
	found := make(map[string]bool, len(names))
	for _, name := range names {
		found[name] = true
	}
	return func(name string) (string, error) {
		if found[name] {
			return "/bin/" + name, nil
		}
		return "", errors.New("not found")
	}
}
