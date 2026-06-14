package stt

import "testing"

func TestCleanWhisperOutputSkipsAudioLogs(t *testing.T) {
	raw := "read_audio_data: reading audio data from '/tmp/lkj.wav' ...\nread_audio_data: trying to decode with miniaudio\n"
	if got := cleanWhisperOutput(raw); got != "" {
		t.Fatalf("cleanWhisperOutput() = %q, want empty", got)
	}
}
