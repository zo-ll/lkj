package output

import (
	"context"
	"errors"
)

type Clipboard struct{}

func (Clipboard) Send(ctx context.Context, text string) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return errors.New("clipboard sink not implemented yet")
}
