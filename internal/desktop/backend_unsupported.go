//go:build !windows

package desktop

import "context"

type unsupportedBackend struct{}

func New() Backend {
	return unsupportedBackend{}
}

func (unsupportedBackend) Name() string {
	return "unsupported"
}

func (unsupportedBackend) Capabilities() Capabilities {
	return Capabilities{}
}

func (unsupportedBackend) SetClipboard(ctx context.Context, text string) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return ErrNotImplemented
}

func (unsupportedBackend) TypeText(ctx context.Context, text string) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return ErrNotImplemented
}

func (unsupportedBackend) ListenHotkey(ctx context.Context, spec string, events chan<- HotkeyEvent) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return ErrNotImplemented
}
