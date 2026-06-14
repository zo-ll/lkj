package stt

import (
	"reflect"
	"testing"
)

func TestParakeetCommandArgs(t *testing.T) {
	p := Parakeet{
		Command:   "python3 scripts/parakeet_transcribe.py",
		ModelName: "nvidia/parakeet-tdt-0.6b-v2",
		Device:    "cpu",
		Offline:   true,
	}
	name, args, err := p.commandArgs("/tmp/in.wav")
	if err != nil {
		t.Fatal(err)
	}
	if name != "python3" {
		t.Fatalf("name = %q, want python3", name)
	}
	want := []string{"scripts/parakeet_transcribe.py", "--file", "/tmp/in.wav", "--model", "nvidia/parakeet-tdt-0.6b-v2", "--device", "cpu", "--offline"}
	if !reflect.DeepEqual(args, want) {
		t.Fatalf("args = %#v, want %#v", args, want)
	}
}

func TestParakeetCommandArgsDefaults(t *testing.T) {
	p := Parakeet{Command: "parakeet-helper"}
	name, args, err := p.commandArgs("/tmp/in.wav")
	if err != nil {
		t.Fatal(err)
	}
	if name != "parakeet-helper" {
		t.Fatalf("name = %q, want parakeet-helper", name)
	}
	want := []string{"--file", "/tmp/in.wav", "--model", "nvidia/parakeet-tdt-0.6b-v2", "--device", "cuda"}
	if !reflect.DeepEqual(args, want) {
		t.Fatalf("args = %#v, want %#v", args, want)
	}
}

func TestParakeetCommandArgsRequiresCommand(t *testing.T) {
	_, _, err := (Parakeet{}).commandArgs("/tmp/in.wav")
	if err == nil {
		t.Fatal("expected error")
	}
}
