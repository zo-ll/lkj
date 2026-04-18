from __future__ import annotations

import tempfile
import threading
import time
from pathlib import Path

from pynput import keyboard

from .asr import ParakeetTranscriber
from .audio import MicrophoneRecorder, trim_silence, write_wav
from .config import AppConfig
from .notify import send_notification
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


NO_VOICE_AUTO_STOP_MIN_SECONDS = 6.0


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

        self._start_hotkey = _normalize_hotkey(config.start_hotkey)
        stop_hotkey = config.stop_hotkey.strip()
        self._stop_hotkey = _normalize_hotkey(stop_hotkey) if stop_hotkey else None
        if self._stop_hotkey == self._start_hotkey:
            self._stop_hotkey = None

        self._is_recording = False
        self._busy = False
        self._lock = threading.Lock()
        self._recording_started_at: float | None = None

    def _process_audio(self, audio_path: Path) -> None:
        text = self.transcriber.transcribe_file(audio_path)
        if not text:
            print("No speech detected")
            send_notification("LKJ", "No speech detected")
            return

        copied = copy_to_clipboard(text)
        append_transcript(self.config.transcript_log_path, text)
        if copied:
            print("Transcript copied to clipboard")
            send_notification("LKJ", "Transcription copied")
        else:
            print("Transcription ready, but clipboard copy failed")
            send_notification("LKJ", "Transcription ready (clipboard unavailable)")

    def _start_capture(self) -> None:
        with self._lock:
            if self._busy:
                print("Busy transcribing, wait")
                return
            if self._is_recording:
                return

            self.recorder.begin_capture(silence_threshold=self.config.silence_threshold)
            self._is_recording = True
            self._recording_started_at = time.monotonic()
        print("Recording started")
        send_notification("LKJ", "Recording started")

    def _stop_capture(self, reason: str) -> None:
        with self._lock:
            if self._busy or not self._is_recording:
                return

            self._is_recording = False
            self._busy = True
            self._recording_started_at = None

        if reason == "silence":
            print("Recording stopped automatically. Transcribing...")
        else:
            print("Recording stopped. Transcribing...")
        send_notification("LKJ", "Recording stopped")

        raw_audio = self.recorder.end_capture()
        raw_duration = len(raw_audio) / float(self.config.sample_rate)
        trimmed_audio = trim_silence(raw_audio, threshold=self.config.silence_threshold)
        trimmed_duration = len(trimmed_audio) / float(self.config.sample_rate)

        audio = trimmed_audio
        if (
            trimmed_duration < self.config.min_seconds
            and raw_duration >= self.config.min_seconds
        ):
            audio = raw_audio

        duration = len(audio) / float(self.config.sample_rate)
        if duration < self.config.min_seconds:
            with self._lock:
                self._busy = False
            print("Audio too short")
            send_notification("LKJ", "Audio too short, try again")
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
            with self._lock:
                self._busy = False

    def _check_auto_stop(self) -> None:
        with self._lock:
            if self._busy or not self._is_recording:
                return
            started_at = self._recording_started_at

        has_voice, last_voice_time, _last_peak = self.recorder.capture_activity()
        now = time.monotonic()

        if has_voice and last_voice_time is not None:
            silent_for = now - last_voice_time
            if silent_for >= self.config.auto_stop_silence_seconds:
                self._stop_capture(reason="silence")
            return

        if started_at is None:
            return

        no_voice_timeout = max(
            NO_VOICE_AUTO_STOP_MIN_SECONDS,
            self.config.auto_stop_silence_seconds * 4.0,
        )
        if now - started_at >= no_voice_timeout:
            self._stop_capture(reason="silence")

    def _on_start_hotkey(self) -> None:
        try:
            with self._lock:
                is_recording = self._is_recording

            if not is_recording:
                self._start_capture()
                return

            if self._stop_hotkey is None:
                self._stop_capture(reason="toggle")
        except Exception as exc:
            with self._lock:
                self._is_recording = False
                self._busy = False
            print(f"Hotkey handler error: {exc}")

    def _on_stop_hotkey(self) -> None:
        try:
            self._stop_capture(reason="manual")
        except Exception as exc:
            with self._lock:
                self._is_recording = False
                self._busy = False
            print(f"Hotkey handler error: {exc}")

    def run(self) -> None:
        self.recorder.start()
        if self._stop_hotkey is None:
            print(
                f"Ready. Press {self.config.start_hotkey} to start/stop recording. Ctrl+C to exit."
            )
        else:
            print(
                f"Ready. Start: {self.config.start_hotkey}, stop: {self.config.stop_hotkey}. Ctrl+C to exit."
            )

        bindings: dict[str, object] = {self._start_hotkey: self._on_start_hotkey}
        if self._stop_hotkey is not None:
            bindings[self._stop_hotkey] = self._on_stop_hotkey

        listener = keyboard.GlobalHotKeys(bindings)
        listener.start()

        try:
            while True:
                self._check_auto_stop()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping")
        finally:
            with self._lock:
                is_recording = self._is_recording
                self._is_recording = False
                self._busy = False
                self._recording_started_at = None

            if is_recording:
                self.recorder.end_capture()
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
    audio = trim_silence(audio, threshold=config.silence_threshold)

    if len(audio) / float(config.sample_rate) < config.min_seconds:
        print("Audio too short")
        send_notification("LKJ", "Audio too short, try again")
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
        send_notification("LKJ", "No speech detected")
        return

    copied = copy_to_clipboard(text)
    append_transcript(config.transcript_log_path, text)
    if copied:
        print("Transcript copied to clipboard")
        send_notification("LKJ", "Transcription copied")
    else:
        print("Transcription ready, but clipboard copy failed")
        send_notification("LKJ", "Transcription ready (clipboard unavailable)")
