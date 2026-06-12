package output

import "context"

// Sink receives final transcripts.
type Sink interface {
	Send(ctx context.Context, text string) error
}
