package audio

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"math"
	"os"
	"os/exec"
	"runtime"
	"strconv"
)

// Source produces a WAV file path for transcription.
type Source interface {
	WAV(ctx context.Context) (string, error)
}

// TemporarySource owns the WAV it produces. The pipeline removes the file
// after every run, including transcription and sink failures.
type TemporarySource interface {
	Source
	RemoveWAV(path string) error
}

type ExistingWAV struct {
	Path string
}

func (e ExistingWAV) WAV(ctx context.Context) (string, error) {
	select {
	case <-ctx.Done():
		return "", ctx.Err()
	default:
	}
	if e.Path == "" {
		return "", errors.New("wav file path is empty")
	}
	return e.Path, nil
}

type Recorder struct {
	Seconds float64
	Device  string
}

func (Recorder) RemoveWAV(path string) error {
	return os.Remove(path)
}

func (r Recorder) WAV(ctx context.Context) (string, error) {
	select {
	case <-ctx.Done():
		return "", ctx.Err()
	default:
	}
	if r.Seconds <= 0 {
		return "", errors.New("recording seconds must be greater than zero")
	}

	tmp, err := os.CreateTemp("", "lkj-*.wav")
	if err != nil {
		return "", err
	}
	wavPath := tmp.Name()
	if err := tmp.Close(); err != nil {
		os.Remove(wavPath)
		return "", err
	}

	rec, err := findRecorder(runtime.GOOS, wavPath, r.Seconds, r.Device, exec.LookPath)
	if err != nil {
		os.Remove(wavPath)
		return "", err
	}

	var stderr bytes.Buffer
	cmd := exec.CommandContext(ctx, rec.Name, rec.Args...)
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		os.Remove(wavPath)
		if stderr.Len() > 0 {
			return "", fmt.Errorf("record audio with %s: %w: %s", rec.Name, err, stderr.String())
		}
		return "", fmt.Errorf("record audio with %s: %w", rec.Name, err)
	}

	info, err := os.Stat(wavPath)
	if err != nil {
		return "", err
	}
	if info.Size() == 0 {
		os.Remove(wavPath)
		return "", fmt.Errorf("record audio with %s: output wav is empty", rec.Name)
	}
	return wavPath, nil
}

type recorderCommand struct {
	Name string
	Args []string
}

func findRecorder(goos, wavPath string, seconds float64, device string, lookPath func(string) (string, error)) (recorderCommand, error) {
	tools := []string{"ffmpeg", "rec"}
	if goos == "linux" {
		tools = []string{"ffmpeg", "arecord", "rec"}
	}
	for _, tool := range tools {
		if _, err := lookPath(tool); err == nil {
			return recorderForTool(goos, tool, wavPath, seconds, device)
		}
	}
	return recorderCommand{}, errors.New("no supported recorder found; install ffmpeg, arecord, or sox/rec")
}

func recorderForTool(goos, tool, wavPath string, seconds float64, device string) (recorderCommand, error) {
	secondsText := strconv.FormatFloat(seconds, 'f', -1, 64)
	switch tool {
	case "ffmpeg":
		args := []string{"-hide_banner", "-loglevel", "error", "-y"}
		switch goos {
		case "linux":
			args = append(args, "-f", "pulse", "-i", valueOrDefault(device, "default"))
		case "darwin":
			args = append(args, "-f", "avfoundation", "-i", valueOrDefault(device, ":0"))
		case "windows":
			args = append(args, "-f", "dshow", "-i", windowsAudioDevice(device))
		default:
			return recorderCommand{}, fmt.Errorf("ffmpeg recorder is not configured for %s", goos)
		}
		if seconds > 0 {
			args = append(args, "-t", secondsText)
		}
		args = append(args, "-ar", "16000", "-ac", "1", wavPath)
		return recorderCommand{Name: tool, Args: args}, nil
	case "arecord":
		if goos != "linux" {
			return recorderCommand{}, errors.New("arecord recorder is only supported on linux")
		}
		args := []string{"-q"}
		if seconds > 0 {
			duration := strconv.Itoa(int(math.Ceil(seconds)))
			args = append(args, "-d", duration)
		}
		args = append(args, "-f", "S16_LE", "-r", "16000", "-c", "1")
		if device != "" {
			args = append(args, "-D", device)
		}
		args = append(args, wavPath)
		return recorderCommand{Name: tool, Args: args}, nil
	case "rec":
		if device != "" {
			return recorderCommand{}, errors.New("rec recorder does not support record_device; use ffmpeg or arecord")
		}
		args := []string{"-q", "-r", "16000", "-c", "1", "-b", "16", wavPath}
		if seconds > 0 {
			args = append(args, "trim", "0", secondsText)
		}
		return recorderCommand{Name: tool, Args: args}, nil
	default:
		return recorderCommand{}, fmt.Errorf("unsupported recorder %q", tool)
	}
}

func valueOrDefault(value, fallback string) string {
	if value != "" {
		return value
	}
	return fallback
}

func windowsAudioDevice(device string) string {
	if device == "" {
		return "audio=default"
	}
	if len(device) >= len("audio=") && device[:len("audio=")] == "audio=" {
		return device
	}
	return "audio=" + device
}
