package config

import (
	"path/filepath"
	"testing"
)

func TestDefault(t *testing.T) {
	cfg := Default()
	if cfg.STTBackend != "whispercpp" {
		t.Fatalf("STTBackend = %q", cfg.STTBackend)
	}
	if cfg.Output != "stdout" {
		t.Fatalf("Output = %q", cfg.Output)
	}
}

func TestSaveAndLoad(t *testing.T) {
	path := filepath.Join(t.TempDir(), "lkj", "config.json")
	want := Config{
		STTBackend:   "whispercpp",
		WhisperBin:   "/tmp/whisper-cli",
		ModelPath:    "/tmp/ggml-tiny.en.bin",
		Threads:      2,
		RecordDevice: "default",
		Output:       "stdout",
	}
	if err := Save(path, want); err != nil {
		t.Fatal(err)
	}
	got, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	if got != want {
		t.Fatalf("Load() = %#v, want %#v", got, want)
	}
}
