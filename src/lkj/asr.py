from __future__ import annotations

import inspect
import os
import threading
import gc
import re
import tempfile
import wave
from pathlib import Path
from typing import Any


FILLER_PATTERN = re.compile(
    r"(?i)(?<!\w)(?:uh-huh|uh+m+|umm+|uh+|um+|ah+|er+|erm+|hmm+|mm+|mhm+)(?:[,.!?;:]+)?(?!\w)"
)


def _strip_fillers(text: str) -> str:
    cleaned = FILLER_PATTERN.sub(" ", text)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([\(\[\{])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _is_cuda_oom(exc: RuntimeError) -> bool:
    return "out of memory" in str(exc).lower()


class ParakeetTranscriber:
    def __init__(
        self,
        model_name: str,
        device: str = "cuda",
        offline_only: bool = True,
        remove_fillers: bool = True,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.offline_only = offline_only
        self.remove_fillers = remove_fillers
        self._model: Any | None = None
        self._loaded_device: str | None = None
        self._load_lock = threading.Lock()

    def load(self) -> None:
        if self._model is not None:
            return

        with self._load_lock:
            if self._model is not None:
                return

            if self.offline_only:
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

            import torch
            from nemo.collections.asr.models import ASRModel

            target_device = self.device
            if self.device == "cuda" and not torch.cuda.is_available():
                target_device = "cpu"

            try:
                self._model = ASRModel.from_pretrained(
                    model_name=self.model_name,
                    map_location=torch.device(target_device),
                )
                self._loaded_device = target_device
            except RuntimeError as exc:
                if target_device != "cuda" or not _is_cuda_oom(exc):
                    raise
                self._model = ASRModel.from_pretrained(
                    model_name=self.model_name,
                    map_location=torch.device("cpu"),
                )
                self._loaded_device = "cpu"
            self._model.eval()

    def is_loaded(self) -> bool:
        with self._load_lock:
            return self._model is not None

    def unload(self) -> None:
        with self._load_lock:
            if self._model is None:
                return
            self._model = None
            self._loaded_device = None

        gc.collect()

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            return

    def warmup(self, sample_rate: int = 16000) -> None:
        frame_count = max(1, int(sample_rate * 0.15))
        with tempfile.NamedTemporaryFile(
            prefix="lkj_warmup_", suffix=".wav", delete=False
        ) as handle:
            path = Path(handle.name)

        try:
            with wave.open(str(path), "wb") as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(sample_rate)
                stream.writeframes(b"\x00\x00" * frame_count)

            self.transcribe_file(path)
        finally:
            path.unlink(missing_ok=True)

    @property
    def loaded_device(self) -> str | None:
        with self._load_lock:
            return self._loaded_device

    def _normalize_output(self, raw: Any) -> str:
        if raw is None:
            return ""

        if isinstance(raw, str):
            text = raw.strip()
            return _strip_fillers(text) if self.remove_fillers else text

        if isinstance(raw, list):
            if not raw:
                return ""
            return self._normalize_output(raw[0])

        if hasattr(raw, "text"):
            text = str(raw.text).strip()
            return _strip_fillers(text) if self.remove_fillers else text

        if hasattr(raw, "pred_text"):
            text = str(raw.pred_text).strip()
            return _strip_fillers(text) if self.remove_fillers else text

        text = str(raw).strip()
        return _strip_fillers(text) if self.remove_fillers else text

    def transcribe_file(self, path: Path) -> str:
        self.load()
        assert self._model is not None

        transcribe_fn = self._model.transcribe
        params = inspect.signature(transcribe_fn).parameters

        kwargs: dict[str, object] = {
            "batch_size": 1,
            "verbose": False,
        }
        if "audio" in params:
            kwargs["audio"] = [str(path)]
        else:
            kwargs["paths2audio_files"] = [str(path)]

        if "use_lhotse" in params:
            kwargs["use_lhotse"] = False
        if "num_workers" in params:
            kwargs["num_workers"] = 0

        output = transcribe_fn(**kwargs)
        return self._normalize_output(output)
