package audio

import (
	"context"
	"errors"
)

// Source produces a WAV file path for transcription.
type Source interface {
	WAV(ctx context.Context) (string, error)
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
}

func (r Recorder) WAV(ctx context.Context) (string, error) {
	select {
	case <-ctx.Done():
		return "", ctx.Err()
	default:
	}
	return "", errors.New("microphone recording not implemented yet; use --file input.wav")
}
