package output

import (
	"context"
	"fmt"
	"io"
)

type Stdout struct {
	Writer io.Writer
}

func (s Stdout) Send(ctx context.Context, text string) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	_, err := fmt.Fprintln(s.Writer, text)
	return err
}
