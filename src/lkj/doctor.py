from __future__ import annotations

import platform
import sys
from dataclasses import dataclass

from .asr import ParakeetTranscriber
from .config import AppConfig


@dataclass(slots=True)
class Check:
    name: str
    ok: bool
    detail: str


def _print(check: Check) -> None:
    marker = "OK" if check.ok else "FAIL"
    print(f"[{marker}] {check.name}: {check.detail}")


def _check_python() -> Check:
    major, minor = sys.version_info[:2]
    ok = major == 3 and 10 <= minor <= 12
    detail = f"{platform.python_version()} (need 3.10-3.12 for NeMo ASR)"
    return Check(name="python", ok=ok, detail=detail)


def _check_torch_cuda() -> Check:
    try:
        import torch
    except Exception as exc:  # pragma: no cover
        return Check(name="torch", ok=False, detail=f"import failed: {exc}")

    cuda_ok = torch.cuda.is_available()
    detail = f"torch={torch.__version__}, cuda={cuda_ok}"
    if cuda_ok:
        detail = f"{detail}, device={torch.cuda.get_device_name(0)}"

    return Check(name="cuda", ok=cuda_ok, detail=detail)


def _check_microphone() -> Check:
    try:
        import sounddevice as sd
    except Exception as exc:  # pragma: no cover
        return Check(name="microphone", ok=False, detail=f"sounddevice import failed: {exc}")

    devices = sd.query_devices()
    has_input = any(device.get("max_input_channels", 0) > 0 for device in devices)
    detail = f"input devices={sum(1 for d in devices if d.get('max_input_channels', 0) > 0)}"
    return Check(name="microphone", ok=has_input, detail=detail)


def _check_hotkey() -> Check:
    try:
        from pynput import keyboard  # noqa: F401
    except Exception as exc:  # pragma: no cover
        return Check(name="hotkey", ok=False, detail=f"pynput import failed: {exc}")

    return Check(name="hotkey", ok=True, detail="pynput import ok")


def _check_model(config: AppConfig, warmup: bool) -> Check:
    if not warmup:
        return Check(name="model", ok=True, detail="skipped (use --warmup to load model)")

    try:
        transcriber = ParakeetTranscriber(
            model_name=config.model_name,
            device=config.device,
            offline_only=config.offline_only,
            remove_fillers=config.remove_fillers,
        )
        transcriber.load()
        loaded_device = transcriber.loaded_device or config.device
        detail = f"loaded {config.model_name} on {loaded_device}"
        if loaded_device != config.device:
            detail = f"{detail} (fallback from {config.device})"
        return Check(name="model", ok=True, detail=detail)
    except Exception as exc:  # pragma: no cover
        return Check(name="model", ok=False, detail=f"load failed: {exc}")


def run_doctor(config: AppConfig, warmup: bool = False) -> int:
    checks = [
        _check_python(),
        _check_torch_cuda(),
        _check_microphone(),
        _check_hotkey(),
        _check_model(config=config, warmup=warmup),
    ]

    for check in checks:
        _print(check)

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"Doctor finished with {len(failed)} failing checks")
        return 1

    print("Doctor finished: all checks passed")
    return 0
