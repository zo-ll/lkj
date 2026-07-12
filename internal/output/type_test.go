package output

import (
	"errors"
	"reflect"
	"testing"
)

func TestTypingCommandPrefersWtypeOnWayland(t *testing.T) {
	got, err := typingCommand("linux", true, foundCommands("wtype", "xdotool"), "hello world")
	if err != nil {
		t.Fatal(err)
	}
	want := typeCommand{name: "wtype", args: []string{"hello world"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("command = %#v, want %#v", got, want)
	}
}

func TestTypingCommandUsesXdotoolOnX11(t *testing.T) {
	got, err := typingCommand("linux", false, foundCommands("xdotool"), "hello; $USER")
	if err != nil {
		t.Fatal(err)
	}
	want := typeCommand{name: "xdotool", args: []string{"type", "--clearmodifiers", "--delay", "0", "--", "hello; $USER"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("command = %#v, want %#v", got, want)
	}
}

func TestTypingCommandReportsMissingLinuxTools(t *testing.T) {
	_, err := typingCommand("linux", true, foundCommands(), "hello")
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestLinuxKey(t *testing.T) {
	tests := []struct {
		input rune
		code  int
		shift bool
		ok    bool
	}{
		{'a', 30, false, true},
		{'A', 30, true, true},
		{'!', 2, true, true},
		{' ', 57, false, true},
		{'é', 0, false, false},
	}
	for _, test := range tests {
		code, shift, ok := linuxKey(test.input)
		if code != test.code || shift != test.shift || ok != test.ok {
			t.Errorf("linuxKey(%q) = (%d, %t, %t), want (%d, %t, %t)", test.input, code, shift, ok, test.code, test.shift, test.ok)
		}
	}
}

func foundCommands(names ...string) func(string) (string, error) {
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
