package config

import "testing"

func TestDefault(t *testing.T) {
	cfg := Default()
	if cfg.STTBackend != "whispercpp" {
		t.Fatalf("STTBackend = %q", cfg.STTBackend)
	}
	if cfg.Output != "stdout" {
		t.Fatalf("Output = %q", cfg.Output)
	}
}
