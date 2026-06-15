package desktop

import "testing"

func TestNewReturnsBackend(t *testing.T) {
	backend := New()
	if backend == nil {
		t.Fatal("New() returned nil")
	}
	if backend.Name() == "" {
		t.Fatal("backend name is empty")
	}
}
