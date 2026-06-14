package stt

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os/exec"
	"strings"
)

// Parakeet calls an optional external helper that transcribes one WAV file.
type Parakeet struct {
	Command   string
	ModelName string
	Device    string
	Offline   bool
}

func (p Parakeet) Transcribe(ctx context.Context, wavPath string) (string, error) {
	name, args, err := p.commandArgs(wavPath)
	if err != nil {
		return "", err
	}

	cmd := exec.CommandContext(ctx, name, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		msg := strings.TrimSpace(stderr.String())
		if msg == "" {
			msg = strings.TrimSpace(stdout.String())
		}
		return "", fmt.Errorf("parakeet failed: %w: %s", err, msg)
	}
	return strings.TrimSpace(stdout.String()), nil
}

func (p Parakeet) commandArgs(wavPath string) (string, []string, error) {
	if wavPath == "" {
		return "", nil, errors.New("wav path is empty")
	}
	fields := strings.Fields(p.Command)
	if len(fields) == 0 {
		return "", nil, errors.New("parakeet command is empty")
	}
	model := p.ModelName
	if model == "" {
		model = "nvidia/parakeet-tdt-0.6b-v2"
	}
	device := p.Device
	if device == "" {
		device = "cuda"
	}

	args := append([]string{}, fields[1:]...)
	args = append(args, "--file", wavPath, "--model", model, "--device", device)
	if p.Offline {
		args = append(args, "--offline")
	}
	return fields[0], args, nil
}
