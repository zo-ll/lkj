package stt

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os/exec"
	"regexp"
	"strings"
	"unicode"
)

// WhisperCPP calls whisper.cpp's CLI as a subprocess.
type WhisperCPP struct {
	Bin       string
	ModelPath string
	Language  string
	Threads   int
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

	cmd := exec.CommandContext(ctx, w.Bin, w.args(wavPath)...)
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

func (w WhisperCPP) args(wavPath string) []string {
	args := []string{"-m", w.ModelPath, "-f", wavPath, "-nt", "-np"}
	if w.Language != "" {
		args = append(args, "-l", w.Language)
	}
	if w.Threads > 0 {
		args = append(args, "-t", fmt.Sprintf("%d", w.Threads))
	}
	args = append(args, w.ExtraArgs...)
	return args
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
		if isLikelySilenceHallucination(line) {
			continue
		}
		if strings.HasPrefix(line, "whisper_") || strings.HasPrefix(line, "main:") {
			continue
		}
		if strings.HasPrefix(line, "read_audio_data:") {
			continue
		}
		kept = append(kept, line)
	}
	return strings.Join(kept, " ")
}

func isLikelySilenceHallucination(text string) bool {
	normalized := strings.TrimSpace(strings.ToLower(text))
	normalized = strings.TrimFunc(normalized, func(r rune) bool {
		return unicode.IsSpace(r) || r == '(' || r == ')' || r == '[' || r == ']' || r == '*' || r == '.' || r == '!' || r == '?'
	})
	switch normalized {
	case "", "music", "dramatic music", "background music", "soft music", "silence", "background noise", "noise", "applause", "laughter", "laughs", "inaudible":
		return true
	default:
		return false
	}
}
