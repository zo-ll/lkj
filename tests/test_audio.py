from __future__ import annotations

import struct
import wave
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import numpy as np
import pytest

from lkj.audio import trim_silence, write_wav


class TestTrimSilence:
    def test_empty_array_returns_empty(self) -> None:
        audio = np.array([], dtype=np.float32)
        result = trim_silence(audio)
        assert result.size == 0

    def test_all_silence_returns_empty(self) -> None:
        audio = np.zeros(16000, dtype=np.float32) + 0.001  # below default 0.01
        result = trim_silence(audio, threshold=0.01)
        assert result.size == 0

    def test_trims_leading_silence(self) -> None:
        audio = np.array([0.0, 0.0, 1.0, 0.5, 0.0], dtype=np.float32)
        result = trim_silence(audio, threshold=0.01)
        assert result[0] == 1.0

    def test_trims_trailing_silence(self) -> None:
        audio = np.array([1.0, 0.5, 0.0, 0.0], dtype=np.float32)
        result = trim_silence(audio, threshold=0.01)
        assert result[-1] == 0.5

    def test_keeps_middle_content(self) -> None:
        audio = np.array([0.0, 0.0, 1.0, 0.8, 0.6, 0.0, 0.0], dtype=np.float32)
        result = trim_silence(audio, threshold=0.01)
        assert len(result) == 3
        assert result[0] == 1.0
        assert result[1] == 0.8
        assert result[2] == 0.6

    def test_custom_threshold(self) -> None:
        audio = np.array([0.0, 0.05, 1.0, 0.05, 0.0], dtype=np.float32)
        result = trim_silence(audio, threshold=0.1)
        assert len(result) == 1
        assert result[0] == 1.0

    def test_stereo_converted_to_mono_elsewhere(self) -> None:
        """trim_silence works on 1D arrays; stereo must be mixed before calling."""
        mono = np.array([0.0, 0.1, 1.0, 0.1, 0.0], dtype=np.float32)
        result = trim_silence(mono, threshold=0.05)
        assert len(result) == 3
        assert result[0] == 0.1
        assert result[1] == 1.0
        assert result[2] == 0.1


class TestWriteWav:
    def test_writes_valid_wav(self) -> None:
        audio = np.sin(np.linspace(0, 440 * np.pi * 2, 16000)).astype(np.float32)
        with NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
        try:
            write_wav(path, audio, 16000)
            with wave.open(str(path), "rb") as wf:
                assert wf.getnchannels() == 1
                assert wf.getframerate() == 16000
                assert wf.getsampwidth() == 2  # 16-bit
                frames = wf.readframes(wf.getnframes())
        finally:
            path.unlink(missing_ok=True)

    def test_clipping(self) -> None:
        audio = np.array([2.0, -3.0, 0.5], dtype=np.float32)
        with NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
        try:
            write_wav(path, audio, 16000)
            with wave.open(str(path), "rb") as wf:
                raw = wf.readframes(wf.getnframes())
            samples = struct.unpack(f"<{len(raw)//2}h", raw)
            # np.clip to [-1,1] then *32767: -1.0 * 32767 = -32767 (int16 min is -32768)
            assert samples[0] == 32767  # clipped to max
            assert samples[1] <= -32767  # clipped to near min
            assert samples[2] > 0  # unclipped
        finally:
            path.unlink(missing_ok=True)

    def test_roundtrip_audio_preserved(self) -> None:
        original = (np.random.rand(8000).astype(np.float32) - 0.5) * 0.8
        with NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
        try:
            write_wav(path, original, 16000)
            with wave.open(str(path), "rb") as wf:
                raw = wf.readframes(wf.getnframes())
            pcm = np.frombuffer(raw, dtype=np.int16)
            restored = pcm.astype(np.float32) / 32767.0
            max_diff = np.max(np.abs(original - restored))
            assert max_diff < 0.01  # quantization error within 1%
        finally:
            path.unlink(missing_ok=True)
