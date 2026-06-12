package output

import (
	"context"
	"os"
	"strings"
	"time"
)

type File struct {
	Path string
}

func (f File) Send(ctx context.Context, text string) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	line := time.Now().Format(time.RFC3339) + " " + strings.TrimSpace(text) + "\n"
	file, err := os.OpenFile(f.Path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer file.Close()
	_, err = file.WriteString(line)
	return err
}
