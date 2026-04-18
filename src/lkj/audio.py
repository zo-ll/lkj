from __future__ import annotations

import threading
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
    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels

        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._recording = False
        self._stream: sd.InputStream | None = None

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        del frames, time
        if status:
            return

        with self._lock:
            if self._recording:
                self._frames.append(indata.copy())

    def start(self) -> None:
        if self._stream is not None:
            return

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def close(self) -> None:
        if self._stream is None:
            return

        self._stream.stop()
        self._stream.close()
        self._stream = None

    def begin_capture(self) -> None:
        with self._lock:
            self._frames = []
            self._recording = True

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
        audio = sd.rec(frames, samplerate=self.sample_rate, channels=1, dtype="float32")
        sd.wait()
        return np.squeeze(audio, axis=1).astype(np.float32)
