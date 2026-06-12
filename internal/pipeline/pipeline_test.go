package pipeline

import (
	"context"
	"testing"
)

type fakeSource struct{ path string }

func (f fakeSource) WAV(context.Context) (string, error) { return f.path, nil }

type fakeTranscriber struct{ text string }

func (f fakeTranscriber) Transcribe(context.Context, string) (string, error) { return f.text, nil }

type fakeSink struct{ got *string }

func (f fakeSink) Send(ctx context.Context, text string) error {
	*f.got = text
	return nil
}

func TestPipelineRun(t *testing.T) {
	var got string
	p := Pipeline{
		Source:      fakeSource{path: "in.wav"},
		Transcriber: fakeTranscriber{text: " hello "},
		Sink:        fakeSink{got: &got},
	}
	text, err := p.Run(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if text != "hello" || got != "hello" {
		t.Fatalf("text=%q got=%q", text, got)
	}
}
