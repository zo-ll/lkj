package output

import (
	"errors"
	"reflect"
	"testing"
)

func TestClipboardCommandPrefersWayland(t *testing.T) {
	got, err := clipboardCommand("linux", clipboardCommands("wl-copy", "xclip"))
	if err != nil {
		t.Fatal(err)
	}
	want := clipboardCmd{name: "wl-copy"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("command = %#v, want %#v", got, want)
	}
}

func TestClipboardCommandFallsBackToXsel(t *testing.T) {
	got, err := clipboardCommand("linux", clipboardCommands("xsel"))
	if err != nil {
		t.Fatal(err)
	}
	want := clipboardCmd{name: "xsel", args: []string{"--clipboard", "--input"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("command = %#v, want %#v", got, want)
	}
}

func TestClipboardCommandReportsMissingTool(t *testing.T) {
	if _, err := clipboardCommand("linux", clipboardCommands()); err == nil {
		t.Fatal("expected error")
	}
}

func clipboardCommands(names ...string) func(string) (string, error) {
	found := make(map[string]bool, len(names))
	for _, name := range names {
		found[name] = true
	}
	return func(name string) (string, error) {
		if found[name] {
			return "/bin/" + name, nil
		}
		return "", errors.New("not found")
	}
}
