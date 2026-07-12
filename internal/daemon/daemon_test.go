package daemon

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"
)

type fakeRecording struct{ path string }

func (f *fakeRecording) Stop(context.Context) (string, error) { return f.path, nil }
func (f *fakeRecording) Cancel()                              {}

type fakeTranscriber struct{ text string }

func (f fakeTranscriber) Transcribe(context.Context, string) (string, error) { return f.text, nil }

type fakeSink struct{ text chan string }

func (f fakeSink) Send(_ context.Context, text string) error {
	f.text <- text
	return nil
}

func TestServerToggleFlow(t *testing.T) {
	dir := t.TempDir()
	wav := filepath.Join(dir, "recording.wav")
	if err := os.WriteFile(wav, []byte("wav"), 0o600); err != nil {
		t.Fatal(err)
	}
	socket := filepath.Join(dir, "lkj.sock")
	delivered := make(chan string, 1)
	notifications := make(chan string, 8)
	server := &Server{
		Socket:      socket,
		Transcriber: fakeTranscriber{text: "hello computer"},
		Sink:        fakeSink{text: delivered},
		StartRecording: func(context.Context, string) (Recording, error) {
			return &fakeRecording{path: wav}, nil
		},
		Notify: func(summary, _ string) { notifications <- summary },
	}
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- server.Serve(ctx) }()
	waitForSocket(t, socket)

	response, err := Send(context.Background(), socket, "toggle")
	if err != nil {
		t.Fatal(err)
	}
	if response.State != "recording" {
		t.Fatalf("start state = %q, want recording", response.State)
	}
	if got := waitForNotification(t, notifications, "Recording"); got != "Recording" {
		t.Fatalf("notification = %q", got)
	}
	response, err = Send(context.Background(), socket, "toggle")
	if err != nil {
		t.Fatal(err)
	}
	if response.State != "idle" || response.Text != "hello computer" {
		t.Fatalf("stop response = %#v", response)
	}
	if got := <-delivered; got != "hello computer" {
		t.Fatalf("delivered = %q", got)
	}
	if _, err := os.Stat(wav); !os.IsNotExist(err) {
		t.Fatalf("temporary recording was not removed: %v", err)
	}

	cancel()
	if err := <-done; err != nil {
		t.Fatal(err)
	}
}

func waitForNotification(t *testing.T, notifications <-chan string, want string) string {
	t.Helper()
	deadline := time.After(2 * time.Second)
	for {
		select {
		case got := <-notifications:
			if got == want {
				return got
			}
		case <-deadline:
			t.Fatalf("notification %q not received", want)
		}
	}
}

func waitForSocket(t *testing.T, path string) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if _, err := os.Stat(path); err == nil {
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatal("daemon socket was not created")
}
