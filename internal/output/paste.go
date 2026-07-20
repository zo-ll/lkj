package output

import (
	"context"
)

// Paste inserts a transcript into the focused application using the platform's
// layout-aware input mechanism.
type Paste struct{}

type preparedPaste struct {
	send func(context.Context, string) error
}

// NewPaste resolves the platform helper when the daemon starts so a missing
// desktop integration fails early instead of after an utterance is recorded.
func NewPaste() (Sink, error) {
	send, err := newPasteSender()
	if err != nil {
		return nil, err
	}
	return preparedPaste{send: send}, nil
}

func (Paste) Send(ctx context.Context, text string) error {
	return pasteText(ctx, text)
}

func (p preparedPaste) Send(ctx context.Context, text string) error {
	return p.send(ctx, text)
}

func CheckPaste() error {
	return checkPaste()
}
