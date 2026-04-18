from __future__ import annotations

import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write


def trim_silence(audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
    if audio.size == 0:
        return audio

    signal = np.abs(audio)
    mask = signal >= threshold

    if not np.any(mask):
        return np.array([], dtype=np.float32)

    start = int(np.argmax(mask))
    end = int(len(mask) - np.argmax(mask[::-1]))
    return audio[start:end]


def write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    wav_write(str(path), sample_rate, pcm)


class MicrophoneRecorder:
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        input_device: str = "",
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.input_device = input_device.strip()

        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._recording = False
        self._stream: sd.InputStream | None = None
        self._silence_threshold = 0.01
        self._has_voice = False
        self._last_voice_time: float | None = None
        self._last_peak = 0.0

    def _resolve_input_device(self) -> int | None:
        target = self.input_device.strip()
        if not target:
            return None

        try:
            devices = sd.query_devices()
        except Exception:
            return None

        input_indexes = [
            index
            for index, device in enumerate(devices)
            if int(device.get("max_input_channels", 0) or 0) > 0
        ]
        if not input_indexes:
            return None

        parsed = target
        if ":" in parsed:
            parsed = parsed.split(":", 1)[0].strip()

        if parsed.isdigit():
            index = int(parsed)
            if index in input_indexes:
                return index

        normalized = target.lower()
        for index in input_indexes:
            name = str(devices[index].get("name", ""))
            if name.lower() == normalized:
                return index

        for index in input_indexes:
            name = str(devices[index].get("name", ""))
            if normalized in name.lower() or name.lower() in normalized:
                return index

        return None

    def _open_stream(self, device: int | None) -> sd.InputStream:
        return sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
            device=device,
        )

    def _callback(self, indata: np.ndarray, frames: int, callback_time, status) -> None:
        del frames, callback_time
        if status:
            return

        with self._lock:
            if self._recording:
                frame = indata.copy()
                self._frames.append(frame)

                if frame.size > 0:
                    level = float(np.sqrt(np.mean(np.square(frame, dtype=np.float32))))
                else:
                    level = 0.0

                self._last_peak = level
                threshold = self._silence_threshold
                if self._has_voice:
                    threshold *= 0.60

                if level >= threshold:
                    self._has_voice = True
                    self._last_voice_time = time.monotonic()

    def start(self) -> None:
        if self._stream is not None:
            return

        device = self._resolve_input_device()
        try:
            self._stream = self._open_stream(device)
        except Exception:
            self._stream = self._open_stream(None)

        self._stream.start()

    def close(self) -> None:
        if self._stream is None:
            return

        self._stream.stop()
        self._stream.close()
        self._stream = None

    def begin_capture(self, silence_threshold: float = 0.01) -> None:
        with self._lock:
            self._frames = []
            self._silence_threshold = max(float(silence_threshold), 0.0)
            self._has_voice = False
            self._last_voice_time = None
            self._last_peak = 0.0
            self._recording = True

    def capture_activity(self) -> tuple[bool, float | None, float]:
        with self._lock:
            return self._has_voice, self._last_voice_time, self._last_peak

    def end_capture(self) -> np.ndarray:
        with self._lock:
            self._recording = False
            if not self._frames:
                return np.array([], dtype=np.float32)

            merged = np.concatenate(self._frames, axis=0)

        if merged.ndim == 2:
            merged = np.mean(merged, axis=1)

        return merged.astype(np.float32)

    def record_blocking(self, seconds: float) -> np.ndarray:
        frames = int(seconds * self.sample_rate)
        device = self._resolve_input_device()

        try:
            audio = sd.rec(
                frames,
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                device=device,
            )
        except Exception:
            audio = sd.rec(
                frames,
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
            )

        sd.wait()
        return np.squeeze(audio, axis=1).astype(np.float32)
