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
            "uh, what?": "what?",
            "um hello": "hello",
            "ah I see": "I see",
            "er, maybe": "maybe",
            "hmm interesting": "interesting",
            "uh uh uh testing": "testing",
            "mm yes": "yes",
            "mhm right": "right",
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                transcriber = ParakeetTranscriber(model_name="fake/model")
                self.assertEqual(transcriber._normalize_output(raw), expected)

    def test_filler_removal_preserves_legitimate_words(self) -> None:
        """Words containing filler-like substrings are not removed."""
        cases = {
            "humming bird": "humming bird",
            "humble pie": "humble pie",
            "the umbrella": "the umbrella",
            "hammer time": "hammer time",
            "summer fun": "summer fun",
            "hummus plate": "hummus plate",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                transcriber = ParakeetTranscriber(model_name="fake/model")
                self.assertEqual(transcriber._normalize_output(raw), expected)

    def test_filler_removal_disabled(self) -> None:
        transcriber = ParakeetTranscriber(model_name="fake/model", remove_fillers=False)
        result = transcriber._normalize_output("uh, hello um world")
        self.assertEqual(result, "uh, hello um world")

    def test_normalize_output_with_none(self) -> None:
        transcriber = ParakeetTranscriber(model_name="fake/model")
        self.assertEqual(transcriber._normalize_output(None), "")

    def test_normalize_output_with_empty_string(self) -> None:
        transcriber = ParakeetTranscriber(model_name="fake/model")
        self.assertEqual(transcriber._normalize_output("  "), "")

    def test_normalize_output_with_empty_list(self) -> None:
        transcriber = ParakeetTranscriber(model_name="fake/model")
        self.assertEqual(transcriber._normalize_output([]), "")

    def test_normalize_output_with_list(self) -> None:
        transcriber = ParakeetTranscriber(model_name="fake/model")
        self.assertEqual(transcriber._normalize_output(["  hello world  "]), "hello world")

    def test_normalize_output_via_text_attribute(self) -> None:
        class Fake:
            text = "  hello world  "
        transcriber = ParakeetTranscriber(model_name="fake/model")
        self.assertEqual(transcriber._normalize_output(Fake()), "hello world")

    def test_normalize_output_via_pred_text_attribute(self) -> None:
        class Fake:
            pred_text = "  hello world  "
        transcriber = ParakeetTranscriber(model_name="fake/model")
        self.assertEqual(transcriber._normalize_output(Fake()), "hello world")

    def test_normalize_output_fallback_str(self) -> None:
        transcriber = ParakeetTranscriber(model_name="fake/model")
        self.assertEqual(transcriber._normalize_output(42), "42")

    def test_load_caches_model(self) -> None:
        """Second load() call does not reload."""
        import_count = 0

        class FakeModel:
            def eval(self):
                pass

        def from_pretrained(model_name, map_location):
            nonlocal import_count
            import_count += 1
            return FakeModel()

        fake_torch = types.SimpleNamespace(
            device=lambda kind: types.SimpleNamespace(type=kind),
            cuda=types.SimpleNamespace(is_available=lambda: False),
        )
        fake_asr_model = types.SimpleNamespace(from_pretrained=from_pretrained)
        nemo_modules = {
            "nemo": types.ModuleType("nemo"),
            "nemo.collections": types.ModuleType("nemo.collections"),
            "nemo.collections.asr": types.ModuleType("nemo.collections.asr"),
            "nemo.collections.asr.models": types.SimpleNamespace(ASRModel=fake_asr_model),
        }

        with patch.dict(sys.modules, {"torch": fake_torch, **nemo_modules}, clear=False):
            t = ParakeetTranscriber(model_name="fake/model", device="cpu")
            t.load()
            self.assertEqual(import_count, 1)
            t.load()
            self.assertEqual(import_count, 1)  # cached

    def test_is_loaded_reports_correctly(self) -> None:
        class FakeModel:
            def eval(self):
                pass

        fake_torch = types.SimpleNamespace(
            device=lambda kind: types.SimpleNamespace(type=kind),
            cuda=types.SimpleNamespace(is_available=lambda: False),
        )
        fake_asr_model = types.SimpleNamespace(from_pretrained=lambda model_name, map_location: FakeModel())
        nemo_modules = {
            "nemo": types.ModuleType("nemo"),
            "nemo.collections": types.ModuleType("nemo.collections"),
            "nemo.collections.asr": types.ModuleType("nemo.collections.asr"),
            "nemo.collections.asr.models": types.SimpleNamespace(ASRModel=fake_asr_model),
        }

        with patch.dict(sys.modules, {"torch": fake_torch, **nemo_modules}, clear=False):
            t = ParakeetTranscriber(model_name="fake/model", device="cpu")
            self.assertFalse(t.is_loaded())
            t.load()
            self.assertTrue(t.is_loaded())
            t.unload()
            self.assertFalse(t.is_loaded())

    def test_unload_when_not_loaded_is_noop(self) -> None:
        t = ParakeetTranscriber(model_name="fake/model")
        t.unload()  # should not raise

    def test_offline_mode_sets_env_vars(self) -> None:
        """Offline mode sets HF and Transformers offline env vars."""
        import os
        old_hf = os.environ.pop("HF_HUB_OFFLINE", None)
        old_tr = os.environ.pop("TRANSFORMERS_OFFLINE", None)

        class FakeModel:
            def eval(self):
                pass

        fake_torch = types.SimpleNamespace(
            device=lambda kind: types.SimpleNamespace(type=kind),
            cuda=types.SimpleNamespace(is_available=lambda: False),
        )
        fake_asr_model = types.SimpleNamespace(from_pretrained=lambda model_name, map_location: FakeModel())
        nemo_modules = {
            "nemo": types.ModuleType("nemo"),
            "nemo.collections": types.ModuleType("nemo.collections"),
            "nemo.collections.asr": types.ModuleType("nemo.collections.asr"),
            "nemo.collections.asr.models": types.SimpleNamespace(ASRModel=fake_asr_model),
        }

        with patch.dict(sys.modules, {"torch": fake_torch, **nemo_modules}, clear=False):
            t = ParakeetTranscriber(model_name="fake/model", offline_only=True)
            t.load()

        import os
        self.assertEqual(os.environ.get("HF_HUB_OFFLINE"), "1")
        self.assertEqual(os.environ.get("TRANSFORMERS_OFFLINE"), "1")
        # Restore
        if old_hf is None:
            os.environ.pop("HF_HUB_OFFLINE", None)
        else:
            os.environ["HF_HUB_OFFLINE"] = old_hf
        if old_tr is None:
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
        else:
            os.environ["TRANSFORMERS_OFFLINE"] = old_tr

    def test_cuda_unavailable_falls_back_to_cpu(self) -> None:
        calls: list[str] = []

        class FakeDevice:
            def __init__(self, kind: str) -> None:
                self.type = kind

        class FakeModel:
            def eval(self):
                return None

            def transcribe(self, paths2audio_files, batch_size, verbose):
                return ["hello"]

        def from_pretrained(model_name, map_location):
            calls.append(map_location.type)
            return FakeModel()

        fake_torch = types.SimpleNamespace(
            device=lambda kind: FakeDevice(kind),
            cuda=types.SimpleNamespace(is_available=lambda: False),
        )
        fake_asr_model = types.SimpleNamespace(from_pretrained=from_pretrained)
        nemo_modules = {
            "nemo": types.ModuleType("nemo"),
            "nemo.collections": types.ModuleType("nemo.collections"),
            "nemo.collections.asr": types.ModuleType("nemo.collections.asr"),
            "nemo.collections.asr.models": types.SimpleNamespace(ASRModel=fake_asr_model),
        }

        with tempfile.NamedTemporaryFile(suffix=".wav") as handle:
            with patch.dict(sys.modules, {"torch": fake_torch, **nemo_modules}, clear=False):
                t = ParakeetTranscriber(model_name="fake/model", device="cuda")
                t.transcribe_file(Path(handle.name))

        self.assertEqual(calls, ["cpu"])
        self.assertEqual(t.loaded_device, "cpu")

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
