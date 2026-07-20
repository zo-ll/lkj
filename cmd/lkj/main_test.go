package main

import (
	"context"
	"errors"
	"reflect"
	"testing"

	"github.com/zo-ll/lkj/internal/daemon"
)

func TestDaemonSocketArg(t *testing.T) {
	tests := []struct {
		args []string
		want string
	}{
		{[]string{"--socket", "/tmp/custom.sock"}, "/tmp/custom.sock"},
		{[]string{"--out", "type", "--socket=/tmp/custom.sock"}, "/tmp/custom.sock"},
	}
	for _, test := range tests {
		if got := daemonSocketArg(test.args); got != test.want {
			t.Fatalf("daemonSocketArg(%q) = %q, want %q", test.args, got, test.want)
		}
	}
}

func TestToggleStartsDaemonOnDemand(t *testing.T) {
	requests := 0
	var startArgs []string
	send := func(context.Context, string, string) (daemon.Response, error) {
		requests++
		if requests == 1 {
			return daemon.Response{}, errors.New("daemon is not running")
		}
		return daemon.Response{State: "recording"}, nil
	}
	start := func(args []string) error {
		startArgs = args
		return nil
	}

	response, err := sendDaemonCommand("toggle", "/tmp/lkj-test.sock", send, start)
	if err != nil {
		t.Fatal(err)
	}
	if response.State != "recording" {
		t.Fatalf("state = %q, want recording", response.State)
	}
	if requests != 2 {
		t.Fatalf("requests = %d, want 2", requests)
	}
	if want := []string{"--socket", "/tmp/lkj-test.sock"}; !reflect.DeepEqual(startArgs, want) {
		t.Fatalf("start args = %q, want %q", startArgs, want)
	}
}

func TestStatusDoesNotStartDaemon(t *testing.T) {
	started := false
	sendErr := errors.New("daemon is not running")
	_, err := sendDaemonCommand("status", "/tmp/lkj-test.sock", func(context.Context, string, string) (daemon.Response, error) {
		return daemon.Response{}, sendErr
	}, func([]string) error {
		started = true
		return nil
	})
	if !errors.Is(err, sendErr) {
		t.Fatalf("error = %v, want %v", err, sendErr)
	}
	if started {
		t.Fatal("status started the daemon")
	}
}
