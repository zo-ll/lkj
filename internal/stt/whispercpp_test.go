package stt

import "testing"

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
