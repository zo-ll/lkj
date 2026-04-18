from __future__ import annotations

import inspect
import os
import threading
from pathlib import Path
from typing import Any


class ParakeetTranscriber:
    def __init__(
        self, model_name: str, device: str = "cuda", offline_only: bool = True
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.offline_only = offline_only
        self._model: Any | None = None
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

            self._model = ASRModel.from_pretrained(
                model_name=self.model_name,
                map_location=torch.device(target_device),
            )
            self._model.eval()

    def _normalize_output(self, raw: Any) -> str:
        if raw is None:
            return ""

        if isinstance(raw, str):
            return raw.strip()

        if isinstance(raw, list):
            if not raw:
                return ""
            return self._normalize_output(raw[0])

        if hasattr(raw, "text"):
            return str(raw.text).strip()

        if hasattr(raw, "pred_text"):
            return str(raw.pred_text).strip()

        return str(raw).strip()

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
