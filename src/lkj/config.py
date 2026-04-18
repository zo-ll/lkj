from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "lkj" / "config.json"
DEFAULT_LOG_PATH = Path.home() / ".local" / "share" / "lkj" / "transcripts.log"


@dataclass(slots=True)
class AppConfig:
    model_name: str = "nvidia/parakeet-tdt-0.6b-v2"
    device: str = "cuda"
    sample_rate: int = 16000
    channels: int = 1
    push_key: str = "alt+space"
    min_seconds: float = 0.20
    offline_only: bool = True
    transcript_log_path: Path = DEFAULT_LOG_PATH


def _from_dict(data: dict[str, object]) -> AppConfig:
    config = AppConfig()

    if "model_name" in data:
        config.model_name = str(data["model_name"])
    if "device" in data:
        config.device = str(data["device"])
    if "sample_rate" in data:
        config.sample_rate = int(data["sample_rate"])
    if "channels" in data:
        config.channels = int(data["channels"])
    if "push_key" in data:
        config.push_key = str(data["push_key"])
    if "min_seconds" in data:
        config.min_seconds = float(data["min_seconds"])
    if "offline_only" in data:
        config.offline_only = bool(data["offline_only"])
    if "transcript_log_path" in data:
        config.transcript_log_path = Path(str(data["transcript_log_path"])).expanduser()

    return config


def load_config(
    config_path: Path | None = None,
    model_name: str | None = None,
    device: str | None = None,
    push_key: str | None = None,
    sample_rate: int | None = None,
    offline_only: bool | None = None,
) -> AppConfig:
    path = config_path or DEFAULT_CONFIG_PATH

    config = AppConfig()
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        config = _from_dict(payload)

    if model_name is not None:
        config = replace(config, model_name=model_name)
    if device is not None:
        config = replace(config, device=device)
    if push_key is not None:
        config = replace(config, push_key=push_key)
    if sample_rate is not None:
        config = replace(config, sample_rate=sample_rate)
    if offline_only is not None:
        config = replace(config, offline_only=offline_only)

    return config
