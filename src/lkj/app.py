from __future__ import annotations

import tempfile
import time
from pathlib import Path

from pynput import keyboard

from .asr import ParakeetTranscriber
from .audio import MicrophoneRecorder, trim_silence, write_wav
from .config import AppConfig
from .output import append_transcript, copy_to_clipboard


HOTKEY_TOKEN_MAP = {
    "alt": "<alt>",
    "ctrl": "<ctrl>",
    "control": "<ctrl>",
    "shift": "<shift>",
    "cmd": "<cmd>",
    "super": "<cmd>",
    "space": "<space>",
    "enter": "<enter>",
    "return": "<enter>",
    "esc": "<esc>",
    "escape": "<esc>",
    "tab": "<tab>",
}


def _normalize_hotkey(push_key: str) -> str:
    parsed: list[str] = []
    for token in push_key.strip().lower().split("+"):
        token = token.strip()
        if not token:
            continue

        if token in HOTKEY_TOKEN_MAP:
            parsed.append(HOTKEY_TOKEN_MAP[token])
            continue

        if token.startswith("<") and token.endswith(">"):
            parsed.append(token)
            continue

        if token.startswith("f") and token[1:].isdigit():
            parsed.append(f"<{token}>")
            continue

        if len(token) == 1:
            parsed.append(token)
            continue

        raise ValueError(f"Unsupported hotkey token: {token}")

    if not parsed:
        raise ValueError("Hotkey is empty")

    return "+".join(parsed)


class PushToTalkApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.recorder = MicrophoneRecorder(
            sample_rate=config.sample_rate, channels=config.channels
        )
        self.transcriber = ParakeetTranscriber(
            model_name=config.model_name,
            device=config.device,
            offline_only=config.offline_only,
        )

        self._hotkey = _normalize_hotkey(config.push_key)
        self._is_recording = False
        self._busy = False

    def _process_audio(self, audio_path: Path) -> None:
        text = self.transcriber.transcribe_file(audio_path)
        if not text:
            print("No speech detected")
            return

        copy_to_clipboard(text)
        append_transcript(self.config.transcript_log_path, text)
        print(f"Transcript copied: {text}")

    def _toggle_capture(self) -> None:
        if self._busy:
            print("Busy transcribing, wait")
            return

        if not self._is_recording:
            self.recorder.begin_capture()
            self._is_recording = True
            print("Recording started")
            return

        self._is_recording = False
        self._busy = True
        print("Recording stopped. Transcribing...")

        audio = self.recorder.end_capture()
        audio = trim_silence(audio)

        duration = len(audio) / float(self.config.sample_rate)
        if duration < self.config.min_seconds:
            self._busy = False
            print("Audio too short")
            return

        with tempfile.NamedTemporaryFile(
            prefix="lkj_", suffix=".wav", delete=False
        ) as handle:
            path = Path(handle.name)

        try:
            write_wav(path, audio, self.config.sample_rate)
            self._process_audio(path)
        finally:
            path.unlink(missing_ok=True)
            self._busy = False

    def _on_hotkey(self) -> None:
        try:
            self._toggle_capture()
        except Exception as exc:
            self._is_recording = False
            self._busy = False
            print(f"Hotkey handler error: {exc}")

    def run(self) -> None:
        print(f"Loading model: {self.config.model_name}")
        self.transcriber.load()

        self.recorder.start()
        print(f"Press {self.config.push_key} to start/stop recording. Ctrl+C to exit.")

        listener = keyboard.GlobalHotKeys({self._hotkey: self._on_hotkey})
        listener.start()

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping")
        finally:
            if self._is_recording:
                self.recorder.end_capture()
                self._is_recording = False
            listener.stop()
            self.recorder.close()


def transcribe_once(config: AppConfig, seconds: float) -> None:
    recorder = MicrophoneRecorder(
        sample_rate=config.sample_rate, channels=config.channels
    )
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

    with tempfile.NamedTemporaryFile(
        prefix="lkj_once_", suffix=".wav", delete=False
    ) as handle:
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
