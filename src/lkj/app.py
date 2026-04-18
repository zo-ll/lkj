from __future__ import annotations

import tempfile
import threading
import time
from pathlib import Path

import numpy as np
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
AUTO_STOP_ACTIVITY_MIN_THRESHOLD = 0.004
MAX_RECORDING_SECONDS = 120.0
MIN_DAEMON_POLL_SECONDS = 0.05
LOW_AUDIO_PEAK = 0.08
TARGET_AUDIO_PEAK = 0.25
MAX_AUTO_GAIN = 30.0


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
            sample_rate=config.sample_rate,
            channels=config.channels,
            input_device=config.input_device,
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
        self._last_model_use_at: float | None = None

    def _mark_model_use(self) -> None:
        with self._lock:
            self._last_model_use_at = time.monotonic()

    def _publish_transcript(self, text: str) -> None:
        copied = copy_to_clipboard(text)
        append_transcript(self.config.transcript_log_path, text)
        if copied:
            print("Transcript copied to clipboard")
            send_notification("LKJ", "Transcription copied")
        else:
            print("Transcription ready, but clipboard copy failed")
            send_notification("LKJ", "Transcription ready (clipboard unavailable)")

    def _transcribe_audio(self, audio: np.ndarray) -> str:
        candidates: list[np.ndarray] = [audio.astype(np.float32)]
        peak = float(np.max(np.abs(audio))) if audio.size > 0 else 0.0

        if 0.0 < peak < LOW_AUDIO_PEAK:
            gain = min(MAX_AUTO_GAIN, TARGET_AUDIO_PEAK / peak)
            boosted = np.clip(audio * gain, -1.0, 1.0).astype(np.float32)
            candidates.append(boosted)

        for candidate in candidates:
            with tempfile.NamedTemporaryFile(
                prefix="lkj_", suffix=".wav", delete=False
            ) as handle:
                path = Path(handle.name)

            try:
                write_wav(path, candidate, self.config.sample_rate)
                self._mark_model_use()
                text = self.transcriber.transcribe_file(path)
                self._mark_model_use()
            finally:
                path.unlink(missing_ok=True)

            if text:
                return text

        return ""

    def _start_capture(self) -> None:
        with self._lock:
            if self._busy:
                print("Busy transcribing, wait")
                return
            if self._is_recording:
                return

            self.recorder.begin_capture(
                silence_threshold=max(
                    self.config.silence_threshold,
                    AUTO_STOP_ACTIVITY_MIN_THRESHOLD,
                )
            )
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
        elif reason == "timeout":
            print("Recording auto-stopped at time limit. Transcribing...")
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

        try:
            text = self._transcribe_audio(audio)
            if not text:
                print("No speech detected")
                send_notification("LKJ", "No speech detected")
                return

            self._publish_transcript(text)
        except Exception as exc:
            print(f"Transcription failed: {exc}")
            send_notification("LKJ", "Transcription failed")
        finally:
            with self._lock:
                self._busy = False

    def _check_auto_stop(self) -> None:
        if not self.config.auto_stop_enabled:
            return

        with self._lock:
            if self._busy or not self._is_recording:
                return
            started_at = self._recording_started_at

        has_voice, last_voice_time, _last_peak = self.recorder.capture_activity()
        now = time.monotonic()

        if started_at is not None and now - started_at >= MAX_RECORDING_SECONDS:
            self._stop_capture(reason="timeout")
            return

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

    def _check_model_idle_unload(self) -> None:
        timeout = self.config.unload_model_after_seconds
        if timeout <= 0:
            return

        with self._lock:
            if self._busy or self._is_recording:
                return
            last_use = self._last_model_use_at

        if last_use is None:
            return

        if time.monotonic() - last_use < timeout:
            return

        if not self.transcriber.is_loaded():
            with self._lock:
                self._last_model_use_at = None
            return

        self.transcriber.unload()
        with self._lock:
            self._last_model_use_at = None
        print("ASR model unloaded after idle")

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

        if self.config.preload_model:
            print("Loading ASR model...")
            try:
                self.transcriber.load()
                self._mark_model_use()
                print("ASR model ready")
            except Exception as exc:
                print(f"ASR preload failed: {exc}")

        if self._stop_hotkey is None:
            mode = (
                "auto-stop enabled"
                if self.config.auto_stop_enabled
                else "manual stop mode"
            )
            print(
                f"Ready ({mode}). Press {self.config.start_hotkey} to start/stop recording. Ctrl+C to exit."
            )
        else:
            mode = (
                "auto-stop enabled"
                if self.config.auto_stop_enabled
                else "manual stop mode"
            )
            print(
                f"Ready ({mode}). Start: {self.config.start_hotkey}, stop: {self.config.stop_hotkey}. Ctrl+C to exit."
            )

        bindings: dict[str, object] = {self._start_hotkey: self._on_start_hotkey}
        if self._stop_hotkey is not None:
            bindings[self._stop_hotkey] = self._on_stop_hotkey

        listener = keyboard.GlobalHotKeys(bindings)
        listener.start()

        try:
            while True:
                self._check_auto_stop()
                self._check_model_idle_unload()
                time.sleep(
                    max(MIN_DAEMON_POLL_SECONDS, self.config.daemon_poll_seconds)
                )
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
        sample_rate=config.sample_rate,
        channels=config.channels,
        input_device=config.input_device,
    )
    transcriber = ParakeetTranscriber(
        model_name=config.model_name,
        device=config.device,
        offline_only=config.offline_only,
    )

    print(f"Recording {seconds:.1f}s...")
    raw_audio = recorder.record_blocking(seconds=seconds)
    trimmed_audio = trim_silence(raw_audio, threshold=config.silence_threshold)
    audio = trimmed_audio

    raw_duration = len(raw_audio) / float(config.sample_rate)
    trimmed_duration = len(trimmed_audio) / float(config.sample_rate)
    if trimmed_duration < config.min_seconds and raw_duration >= config.min_seconds:
        audio = raw_audio

    if len(audio) / float(config.sample_rate) < config.min_seconds:
        print("Audio too short")
        send_notification("LKJ", "Audio too short, try again")
        return

    candidates: list[np.ndarray] = [audio.astype(np.float32)]
    peak = float(np.max(np.abs(audio))) if audio.size > 0 else 0.0
    if 0.0 < peak < LOW_AUDIO_PEAK:
        gain = min(MAX_AUTO_GAIN, TARGET_AUDIO_PEAK / peak)
        boosted = np.clip(audio * gain, -1.0, 1.0).astype(np.float32)
        candidates.append(boosted)

    text = ""
    for candidate in candidates:
        with tempfile.NamedTemporaryFile(
            prefix="lkj_once_", suffix=".wav", delete=False
        ) as handle:
            path = Path(handle.name)

        try:
            write_wav(path, candidate, config.sample_rate)
            text = transcriber.transcribe_file(path)
        finally:
            path.unlink(missing_ok=True)

        if text:
            break

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
