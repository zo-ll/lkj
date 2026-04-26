from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from lkj.asr import ParakeetTranscriber


class ParakeetTranscriberFallbackTest(unittest.TestCase):
    def test_common_filler_variants_are_removed(self) -> None:
        cases = {
            "uhm, hello": "hello",
            "umm I think so": "I think so",
            "uh-huh, yes": "yes",
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                transcriber = ParakeetTranscriber(model_name="fake/model")
                self.assertEqual(transcriber._normalize_output(raw), expected)

    def test_transcribe_file_falls_back_to_cpu_after_cuda_oom(self) -> None:
        calls: list[str] = []

        class FakeDevice:
            def __init__(self, kind: str) -> None:
                self.type = kind

        class FakeModel:
            def eval(self) -> None:
                return None

            def transcribe(
                self,
                paths2audio_files: list[str],
                batch_size: int,
                verbose: bool,
            ) -> list[str]:
                return ["hello world"]

        def from_pretrained(model_name: str, map_location: FakeDevice) -> FakeModel:
            calls.append(map_location.type)
            if map_location.type == "cuda":
                raise RuntimeError("CUDA out of memory")
            return FakeModel()

        fake_torch = types.SimpleNamespace(
            device=lambda kind: FakeDevice(kind),
            cuda=types.SimpleNamespace(is_available=lambda: True),
        )
        fake_asr_model = types.SimpleNamespace(from_pretrained=from_pretrained)

        nemo_modules = {
            "nemo": types.ModuleType("nemo"),
            "nemo.collections": types.ModuleType("nemo.collections"),
            "nemo.collections.asr": types.ModuleType("nemo.collections.asr"),
            "nemo.collections.asr.models": types.SimpleNamespace(ASRModel=fake_asr_model),
        }

        with tempfile.NamedTemporaryFile(suffix=".wav") as handle:
            with patch.dict(
                sys.modules,
                {"torch": fake_torch, **nemo_modules},
                clear=False,
            ):
                text = ParakeetTranscriber(
                    model_name="fake/model",
                    device="cuda",
                ).transcribe_file(Path(handle.name))

        self.assertEqual(text, "hello world")
        self.assertEqual(calls, ["cuda", "cpu"])

    def test_loaded_device_reports_cpu_after_cuda_oom_fallback(self) -> None:
        class FakeDevice:
            def __init__(self, kind: str) -> None:
                self.type = kind

        class FakeModel:
            def eval(self) -> None:
                return None

            def transcribe(
                self,
                paths2audio_files: list[str],
                batch_size: int,
                verbose: bool,
            ) -> list[str]:
                return ["hello world"]

        def from_pretrained(model_name: str, map_location: FakeDevice) -> FakeModel:
            if map_location.type == "cuda":
                raise RuntimeError("CUDA out of memory")
            return FakeModel()

        fake_torch = types.SimpleNamespace(
            device=lambda kind: FakeDevice(kind),
            cuda=types.SimpleNamespace(is_available=lambda: True),
        )
        fake_asr_model = types.SimpleNamespace(from_pretrained=from_pretrained)

        nemo_modules = {
            "nemo": types.ModuleType("nemo"),
            "nemo.collections": types.ModuleType("nemo.collections"),
            "nemo.collections.asr": types.ModuleType("nemo.collections.asr"),
            "nemo.collections.asr.models": types.SimpleNamespace(ASRModel=fake_asr_model),
        }

        with tempfile.NamedTemporaryFile(suffix=".wav") as handle:
            with patch.dict(
                sys.modules,
                {"torch": fake_torch, **nemo_modules},
                clear=False,
            ):
                transcriber = ParakeetTranscriber(
                    model_name="fake/model",
                    device="cuda",
                )
                transcriber.transcribe_file(Path(handle.name))

        self.assertEqual(transcriber.loaded_device, "cpu")


if __name__ == "__main__":
    unittest.main()
