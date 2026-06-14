package audio

import (
	"reflect"
	"testing"
)

func TestRecorderForToolFFmpegLinux(t *testing.T) {
	rec, err := recorderForTool("linux", "ffmpeg", "/tmp/in.wav", 2.5, "")
	if err != nil {
		t.Fatal(err)
	}
	want := recorderCommand{Name: "ffmpeg", Args: []string{"-hide_banner", "-loglevel", "error", "-y", "-f", "pulse", "-i", "default", "-t", "2.5", "-ar", "16000", "-ac", "1", "/tmp/in.wav"}}
	if !reflect.DeepEqual(rec, want) {
		t.Fatalf("recorder command = %#v, want %#v", rec, want)
	}
}

func TestRecorderForToolFFmpegLinuxWithDevice(t *testing.T) {
	rec, err := recorderForTool("linux", "ffmpeg", "/tmp/in.wav", 2.5, "alsa_input.usb-mic")
	if err != nil {
		t.Fatal(err)
	}
	want := recorderCommand{Name: "ffmpeg", Args: []string{"-hide_banner", "-loglevel", "error", "-y", "-f", "pulse", "-i", "alsa_input.usb-mic", "-t", "2.5", "-ar", "16000", "-ac", "1", "/tmp/in.wav"}}
	if !reflect.DeepEqual(rec, want) {
		t.Fatalf("recorder command = %#v, want %#v", rec, want)
	}
}

func TestRecorderForToolARecordLinuxWithDevice(t *testing.T) {
	rec, err := recorderForTool("linux", "arecord", "/tmp/in.wav", 1.2, "hw:1,0")
	if err != nil {
		t.Fatal(err)
	}
	want := recorderCommand{Name: "arecord", Args: []string{"-q", "-d", "2", "-f", "S16_LE", "-r", "16000", "-c", "1", "-D", "hw:1,0", "/tmp/in.wav"}}
	if !reflect.DeepEqual(rec, want) {
		t.Fatalf("recorder command = %#v, want %#v", rec, want)
	}
}

func TestRecorderForToolFFmpegWindows(t *testing.T) {
	rec, err := recorderForTool("windows", "ffmpeg", `C:\Temp\in.wav`, 2, "")
	if err != nil {
		t.Fatal(err)
	}
	want := recorderCommand{Name: "ffmpeg", Args: []string{"-hide_banner", "-loglevel", "error", "-y", "-f", "dshow", "-i", "audio=default", "-t", "2", "-ar", "16000", "-ac", "1", `C:\Temp\in.wav`}}
	if !reflect.DeepEqual(rec, want) {
		t.Fatalf("recorder command = %#v, want %#v", rec, want)
	}
}

func TestFindRecorderPrefersFFmpegOnLinux(t *testing.T) {
	rec, err := findRecorder("linux", "/tmp/in.wav", 1, "", func(name string) (string, error) {
		return "/usr/bin/" + name, nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if rec.Name != "ffmpeg" {
		t.Fatalf("recorder = %q, want ffmpeg", rec.Name)
	}
}

func TestRecorderForToolRecRejectsDevice(t *testing.T) {
	_, err := recorderForTool("linux", "rec", "/tmp/in.wav", 1, "mic")
	if err == nil {
		t.Fatal("expected error")
	}
}
