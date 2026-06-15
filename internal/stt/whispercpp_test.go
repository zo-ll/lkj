package stt

import "testing"

func TestWhisperCPPArgsIncludesThreads(t *testing.T) {
	w := WhisperCPP{ModelPath: "model.bin", Language: "en", Threads: 2, ExtraArgs: []string{"--foo"}}
	got := w.args("input.wav")
	want := []string{"-m", "model.bin", "-f", "input.wav", "-nt", "-np", "-l", "en", "-t", "2", "--foo"}
	assertStringSliceEqual(t, got, want)
}

func TestWhisperCPPArgsOmitsNonPositiveThreads(t *testing.T) {
	w := WhisperCPP{ModelPath: "model.bin", Threads: 0}
	got := w.args("input.wav")
	want := []string{"-m", "model.bin", "-f", "input.wav", "-nt", "-np"}
	assertStringSliceEqual(t, got, want)
}

func assertStringSliceEqual(t *testing.T, got, want []string) {
	t.Helper()
	if len(got) != len(want) {
		t.Fatalf("args = %#v, want %#v", got, want)
	}
	for i := range got {
		if got[i] != want[i] {
			t.Fatalf("args = %#v, want %#v", got, want)
		}
	}
}

func TestCleanWhisperOutputSkipsAudioLogs(t *testing.T) {
	raw := "read_audio_data: reading audio data from '/tmp/lkj.wav' ...\nread_audio_data: trying to decode with miniaudio\n"
	if got := cleanWhisperOutput(raw); got != "" {
		t.Fatalf("cleanWhisperOutput() = %q, want empty", got)
	}
}

func TestCleanWhisperOutputSkipsSilenceHallucinations(t *testing.T) {
	for _, raw := range []string{"(dramatic music)", "[Music]", "*applause*", "silence"} {
		if got := cleanWhisperOutput(raw); got != "" {
			t.Fatalf("cleanWhisperOutput(%q) = %q, want empty", raw, got)
		}
	}
}

func TestCleanWhisperOutputKeepsSpeech(t *testing.T) {
	raw := "[00:00:00.000 --> 00:00:02.000] hello world"
	if got := cleanWhisperOutput(raw); got != "hello world" {
		t.Fatalf("cleanWhisperOutput() = %q, want hello world", got)
	}
}
