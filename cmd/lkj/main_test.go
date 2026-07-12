package main

import "testing"

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
