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
    start_hotkey: str = "alt+space"
    stop_hotkey: str = ""
    min_seconds: float = 0.20
    auto_stop_silence_seconds: float = 1.2
    silence_threshold: float = 0.005
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
    if "start_hotkey" in data:
        config.start_hotkey = str(data["start_hotkey"])
    elif "push_key" in data:
        config.start_hotkey = str(data["push_key"])
    if "stop_hotkey" in data:
        config.stop_hotkey = str(data["stop_hotkey"])
    if "min_seconds" in data:
        config.min_seconds = float(data["min_seconds"])
    if "auto_stop_silence_seconds" in data:
        config.auto_stop_silence_seconds = float(data["auto_stop_silence_seconds"])
    if "silence_threshold" in data:
        config.silence_threshold = float(data["silence_threshold"])
    if "offline_only" in data:
        config.offline_only = bool(data["offline_only"])
    if "transcript_log_path" in data:
        config.transcript_log_path = Path(str(data["transcript_log_path"])).expanduser()

    return config


def load_config(
    config_path: Path | None = None,
    model_name: str | None = None,
    device: str | None = None,
    start_hotkey: str | None = None,
    stop_hotkey: str | None = None,
    push_key: str | None = None,
    sample_rate: int | None = None,
    offline_only: bool | None = None,
) -> AppConfig:
    path = config_path or DEFAULT_CONFIG_PATH

    config = AppConfig()
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        config = _from_dict(payload)

    if start_hotkey is None and push_key is not None:
        start_hotkey = push_key

    if model_name is not None:
        config = replace(config, model_name=model_name)
    if device is not None:
        config = replace(config, device=device)
    if start_hotkey is not None:
        config = replace(config, start_hotkey=start_hotkey)
    if stop_hotkey is not None:
        config = replace(config, stop_hotkey=stop_hotkey)
    if sample_rate is not None:
        config = replace(config, sample_rate=sample_rate)
    if offline_only is not None:
        config = replace(config, offline_only=offline_only)

    return config


def save_config(config: AppConfig, config_path: Path | None = None) -> Path:
    path = config_path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "model_name": config.model_name,
        "device": config.device,
        "sample_rate": config.sample_rate,
        "channels": config.channels,
        "start_hotkey": config.start_hotkey,
        "stop_hotkey": config.stop_hotkey,
        "min_seconds": config.min_seconds,
        "auto_stop_silence_seconds": config.auto_stop_silence_seconds,
        "silence_threshold": config.silence_threshold,
        "offline_only": config.offline_only,
        "transcript_log_path": str(config.transcript_log_path),
    }

    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
