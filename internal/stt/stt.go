package stt

import "context"

// Transcriber turns an audio file into text.
type Transcriber interface {
	Transcribe(ctx context.Context, wavPath string) (string, error)
}
