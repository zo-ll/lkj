//go:build !linux

package output

import (
	"context"
	"errors"
)

func typeLinux(context.Context, string) error {
	return errors.New("Linux virtual keyboard is unavailable")
}
