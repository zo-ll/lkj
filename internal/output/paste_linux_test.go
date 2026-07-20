//go:build linux

package output

import (
	"context"
	"os"
	"path/filepath"
	"testing"
)

func TestRunEITypeSeparatesTranscriptFromOptions(t *testing.T) {
	dir := t.TempDir()
	helper := filepath.Join(dir, "eitype")
	argsFile := filepath.Join(dir, "args")
	script := "#!/bin/sh\nprintf '%s\\n' \"$#\" \"$1\" \"$2\" > \"$LKJ_EITYPE_ARGS\"\n"
	if err := os.WriteFile(helper, []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("LKJ_EITYPE_ARGS", argsFile)

	if err := runEIType(context.Background(), helper, "-starts-with-dash"); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(argsFile)
	if err != nil {
		t.Fatal(err)
	}
	if want := "2\n--\n-starts-with-dash\n"; string(got) != want {
		t.Fatalf("arguments = %q, want %q", got, want)
	}
}
