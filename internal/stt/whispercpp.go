package stt

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os/exec"
	"regexp"
	"strings"
)

// WhisperCPP calls whisper.cpp's CLI as a subprocess.
type WhisperCPP struct {
	Bin       string
	ModelPath string
	Language  string
	ExtraArgs []string
}

func (w WhisperCPP) Transcribe(ctx context.Context, wavPath string) (string, error) {
	if w.Bin == "" {
		return "", errors.New("whisper.cpp binary path is empty")
	}
	if w.ModelPath == "" {
		return "", errors.New("whisper.cpp model path is empty")
	}
	if wavPath == "" {
		return "", errors.New("wav path is empty")
	}

	args := []string{"-m", w.ModelPath, "-f", wavPath, "-nt", "-np"}
	if w.Language != "" {
		args = append(args, "-l", w.Language)
	}
	args = append(args, w.ExtraArgs...)

	cmd := exec.CommandContext(ctx, w.Bin, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		msg := strings.TrimSpace(stderr.String())
		if msg == "" {
			msg = strings.TrimSpace(stdout.String())
		}
		return "", fmt.Errorf("whisper.cpp failed: %w: %s", err, msg)
	}

	text := cleanWhisperOutput(stdout.String())
	if text == "" {
		text = cleanWhisperOutput(stderr.String())
	}
	return text, nil
}

var timestampLine = regexp.MustCompile(`(?m)^\s*\[[^\]]+\]\s*`)

func cleanWhisperOutput(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return ""
	}
	raw = timestampLine.ReplaceAllString(raw, "")
	lines := strings.Split(raw, "\n")
	kept := make([]string, 0, len(lines))
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "whisper_") || strings.HasPrefix(line, "main:") {
			continue
		}
		kept = append(kept, line)
	}
	return strings.Join(kept, " ")
}
