package pipeline

import (
	"context"
	"strings"

	"github.com/zo-ll/lkj/internal/audio"
	"github.com/zo-ll/lkj/internal/output"
	"github.com/zo-ll/lkj/internal/stt"
)

type Pipeline struct {
	Source      audio.Source
	Transcriber stt.Transcriber
	Sink        output.Sink
}

func (p Pipeline) Run(ctx context.Context) (string, error) {
	wavPath, err := p.Source.WAV(ctx)
	if err != nil {
		return "", err
	}
	if temporary, ok := p.Source.(audio.TemporarySource); ok {
		defer temporary.RemoveWAV(wavPath)
	}

	text, err := p.Transcriber.Transcribe(ctx, wavPath)
	if err != nil {
		return "", err
	}
	text = strings.TrimSpace(text)
	if text == "" {
		return "", nil
	}

	if err := p.Sink.Send(ctx, text); err != nil {
		return "", err
	}
	return text, nil
}
