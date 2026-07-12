package audio

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"runtime"
)

// Session is a microphone recording that runs until Stop is called.
type Session struct {
	path   string
	tool   string
	cmd    *exec.Cmd
	stderr bytes.Buffer
	done   chan error
}

// Start begins recording microphone audio to a temporary WAV file.
func Start(ctx context.Context, device string) (*Session, error) {
	tmp, err := os.CreateTemp("", "lkj-*.wav")
	if err != nil {
		return nil, err
	}
	path := tmp.Name()
	if err := tmp.Close(); err != nil {
		os.Remove(path)
		return nil, err
	}

	rec, err := findRecorder(runtime.GOOS, path, 0, device, exec.LookPath)
	if err != nil {
		os.Remove(path)
		return nil, err
	}
	s := &Session{path: path, tool: rec.Name, done: make(chan error, 1)}
	s.cmd = exec.CommandContext(ctx, rec.Name, rec.Args...)
	s.cmd.Stderr = &s.stderr
	if err := s.cmd.Start(); err != nil {
		os.Remove(path)
		return nil, fmt.Errorf("start audio recording with %s: %w", rec.Name, err)
	}
	go func() { s.done <- s.cmd.Wait() }()
	return s, nil
}

// Stop ends recording and returns the temporary WAV path. The caller owns the
// returned file and must remove it when transcription is complete.
func (s *Session) Stop(ctx context.Context) (string, error) {
	select {
	case err := <-s.done:
		s.remove()
		return "", s.commandError("audio recorder stopped unexpectedly", err)
	default:
	}

	if err := s.cmd.Process.Signal(os.Interrupt); err != nil {
		_ = s.cmd.Process.Kill()
	}
	select {
	case <-s.done:
	case <-ctx.Done():
		_ = s.cmd.Process.Kill()
		<-s.done
		s.remove()
		return "", ctx.Err()
	}

	info, err := os.Stat(s.path)
	if err != nil {
		s.remove()
		return "", err
	}
	if info.Size() == 0 {
		s.remove()
		return "", fmt.Errorf("record audio with %s: output wav is empty", s.tool)
	}
	return s.path, nil
}

// Cancel stops the recorder and removes any partial audio.
func (s *Session) Cancel() {
	if s == nil || s.cmd == nil || s.cmd.Process == nil {
		return
	}
	_ = s.cmd.Process.Kill()
	<-s.done
	s.remove()
}

func (s *Session) remove() { _ = os.Remove(s.path) }

func (s *Session) commandError(prefix string, err error) error {
	message := s.stderr.String()
	if err == nil {
		if message == "" {
			return errors.New(prefix)
		}
		return fmt.Errorf("%s: %s", prefix, message)
	}
	if message != "" {
		return fmt.Errorf("%s: %w: %s", prefix, err, message)
	}
	return fmt.Errorf("%s: %w", prefix, err)
}
