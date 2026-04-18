from __future__ import annotations

import tempfile
import time
from pathlib import Path

from pynput import keyboard

from .asr import ParakeetTranscriber
from .audio import MicrophoneRecorder, trim_silence, write_wav
from .config import AppConfig
from .output import append_transcript, copy_to_clipboard


def _resolve_push_key(push_key: str) -> keyboard.Key | keyboard.KeyCode:
    key_name = push_key.strip().lower()

    if len(key_name) == 1:
        return keyboard.KeyCode.from_char(key_name)

    match = getattr(keyboard.Key, key_name, None)
    if match is None:
        raise ValueError(f"Unsupported key: {push_key}")

    return match


def _key_matches(
    candidate: keyboard.Key | keyboard.KeyCode,
    expected: keyboard.Key | keyboard.KeyCode,
) -> bool:
    if isinstance(expected, keyboard.KeyCode):
        if not isinstance(candidate, keyboard.KeyCode):
            return False
        return candidate.char == expected.char

    return candidate == expected


class PushToTalkApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.recorder = MicrophoneRecorder(sample_rate=config.sample_rate, channels=config.channels)
        self.transcriber = ParakeetTranscriber(
            model_name=config.model_name,
            device=config.device,
            offline_only=config.offline_only,
        )

        self._expected_key = _resolve_push_key(config.push_key)
        self._is_pressed = False
        self._busy = False

    def _process_audio(self, audio_path: Path) -> None:
        text = self.transcriber.transcribe_file(audio_path)
        if not text:
            print("No speech detected")
            return

        copy_to_clipboard(text)
        append_transcript(self.config.transcript_log_path, text)
        print(f"Transcript copied: {text}")

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if self._busy:
            return

        if self._is_pressed:
            return

        if not _key_matches(key, self._expected_key):
            return

        self._is_pressed = True
        self.recorder.begin_capture()
        print("Recording...")

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if not self._is_pressed:
            return

        if not _key_matches(key, self._expected_key):
            return

        self._is_pressed = False
        self._busy = True

        audio = self.recorder.end_capture()
        audio = trim_silence(audio)

        duration = len(audio) / float(self.config.sample_rate)
        if duration < self.config.min_seconds:
            self._busy = False
            print("Audio too short")
            return

        with tempfile.NamedTemporaryFile(prefix="lkj_", suffix=".wav", delete=False) as handle:
            path = Path(handle.name)

        try:
            write_wav(path, audio, self.config.sample_rate)
            self._process_audio(path)
        finally:
            path.unlink(missing_ok=True)
            self._busy = False

    def run(self) -> None:
        print(f"Loading model: {self.config.model_name}")
        self.transcriber.load()

        self.recorder.start()
        print(f"Hold {self.config.push_key} to talk. Ctrl+C to exit.")

        listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        listener.start()

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping")
        finally:
            listener.stop()
            self.recorder.close()


def transcribe_once(config: AppConfig, seconds: float) -> None:
    recorder = MicrophoneRecorder(sample_rate=config.sample_rate, channels=config.channels)
    transcriber = ParakeetTranscriber(
        model_name=config.model_name,
        device=config.device,
        offline_only=config.offline_only,
    )

    print(f"Recording {seconds:.1f}s...")
    audio = recorder.record_blocking(seconds=seconds)
    audio = trim_silence(audio)

    if len(audio) / float(config.sample_rate) < config.min_seconds:
        print("Audio too short")
        return

    with tempfile.NamedTemporaryFile(prefix="lkj_once_", suffix=".wav", delete=False) as handle:
        path = Path(handle.name)

    try:
        write_wav(path, audio, config.sample_rate)
        text = transcriber.transcribe_file(path)
    finally:
        path.unlink(missing_ok=True)

    if not text:
        print("No speech detected")
        return

    copy_to_clipboard(text)
    append_transcript(config.transcript_log_path, text)
    print(f"Transcript copied: {text}")
