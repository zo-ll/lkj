//go:build !darwin

package desktop

import (
	"context"
	"errors"
	"testing"
)

func TestUnsupportedBackendReturnsNotImplemented(t *testing.T) {
	backend := unsupportedBackend{}
	if err := backend.SetClipboard(context.Background(), "hello"); !errors.Is(err, ErrNotImplemented) {
		t.Fatalf("SetClipboard() error = %v, want ErrNotImplemented", err)
	}
	if err := backend.TypeText(context.Background(), "hello"); !errors.Is(err, ErrNotImplemented) {
		t.Fatalf("TypeText() error = %v, want ErrNotImplemented", err)
	}
	if err := backend.ListenHotkey(context.Background(), "alt+space", make(chan<- HotkeyEvent)); !errors.Is(err, ErrNotImplemented) {
		t.Fatalf("ListenHotkey() error = %v, want ErrNotImplemented", err)
	}
}
