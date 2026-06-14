#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import gc
import inspect
import os
import re
import sys
from pathlib import Path
from typing import Any


FILLER_PATTERN = re.compile(
    r"(?i)(?<!\w)(?:uh-huh|uh+m+|umm+|uh+|um+|ah+|er+|erm+|hmm+|mm+|mhm+)(?:[,.!?;:]+)?(?!\w)"
)


def strip_fillers(text: str) -> str:
    cleaned = FILLER_PATTERN.sub(" ", text)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([\(\[\{])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def normalize_output(raw: Any, remove_fillers: bool) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        text = raw.strip()
        return strip_fillers(text) if remove_fillers else text
    if isinstance(raw, list):
        if not raw:
            return ""
        return normalize_output(raw[0], remove_fillers)
    if hasattr(raw, "text"):
        text = str(raw.text).strip()
        return strip_fillers(text) if remove_fillers else text
    if hasattr(raw, "pred_text"):
        text = str(raw.pred_text).strip()
        return strip_fillers(text) if remove_fillers else text
    text = str(raw).strip()
    return strip_fillers(text) if remove_fillers else text


def is_cuda_oom(exc: RuntimeError) -> bool:
    return "out of memory" in str(exc).lower()


def transcribe(path: Path, model_name: str, device: str, offline: bool, remove_fillers: bool) -> str:
    if offline:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    import torch
    from nemo.collections.asr.models import ASRModel

    target_device = device
    if device == "cuda" and not torch.cuda.is_available():
        target_device = "cpu"

    try:
        model = ASRModel.from_pretrained(
            model_name=model_name,
            map_location=torch.device(target_device),
        )
    except RuntimeError as exc:
        if target_device != "cuda" or not is_cuda_oom(exc):
            raise
        model = ASRModel.from_pretrained(
            model_name=model_name,
            map_location=torch.device("cpu"),
        )
    model.eval()

    transcribe_fn = model.transcribe
    params = inspect.signature(transcribe_fn).parameters
    kwargs: dict[str, object] = {"batch_size": 1, "verbose": False}
    if "audio" in params:
        kwargs["audio"] = [str(path)]
    else:
        kwargs["paths2audio_files"] = [str(path)]
    if "use_lhotse" in params:
        kwargs["use_lhotse"] = False
    if "num_workers" in params:
        kwargs["num_workers"] = 0

    output = model.transcribe(**kwargs)
    text = normalize_output(output, remove_fillers)

    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe a WAV file with NVIDIA Parakeet through NeMo.")
    parser.add_argument("--file", required=True, help="WAV file path")
    parser.add_argument("--model", default="nvidia/parakeet-tdt-0.6b-v2", help="Parakeet model name")
    parser.add_argument("--device", default="cuda", help="cuda or cpu")
    parser.add_argument("--offline", action="store_true", help="force offline Hugging Face/Transformers mode")
    parser.add_argument("--keep-fillers", action="store_true", help="do not remove filler words")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"audio file does not exist: {path}", file=sys.stderr)
        return 2

    with contextlib.redirect_stdout(sys.stderr):
        text = transcribe(
            path=path,
            model_name=args.model,
            device=args.device,
            offline=args.offline,
            remove_fillers=not args.keep_fillers,
        )
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
