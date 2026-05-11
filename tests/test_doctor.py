from __future__ import annotations

import sys
import types
from unittest.mock import patch

import pytest

from lkj.config import AppConfig
from lkj.doctor import (
    Check,
    _check_python,
    _check_torch_cuda,
    _check_microphone,
    _check_hotkey,
    _check_model,
    run_doctor,
)


class TestCheckPython:
    def test_supported_version(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "version_info", (3, 10, 0))
        check = _check_python()
        assert check.ok is True
        assert "3.10" in check.detail

    def test_too_old(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "version_info", (3, 9, 0))
        check = _check_python()
        assert check.ok is False

    def test_too_new(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "version_info", (3, 13, 0))
        check = _check_python()
        assert check.ok is False


class TestCheckTorchCuda:
    def test_cuda_available(self) -> None:
        fake_torch = types.SimpleNamespace(
            __version__="2.5.0",
            cuda=types.SimpleNamespace(
                is_available=lambda: True,
                get_device_name=lambda i: "NVIDIA GeForce RTX 4090",
            ),
        )
        with patch.dict(sys.modules, {"torch": fake_torch}):
            check = _check_torch_cuda()
            assert check.ok is True
            assert "4090" in check.detail

    def test_cuda_unavailable(self) -> None:
        fake_torch = types.SimpleNamespace(
            __version__="2.5.0",
            cuda=types.SimpleNamespace(is_available=lambda: False),
        )
        with patch.dict(sys.modules, {"torch": fake_torch}):
            check = _check_torch_cuda()
            assert check.ok is False
            assert "cuda=False" in check.detail

    def test_torch_import_fails(self) -> None:
        with patch.dict(sys.modules, {"torch": None}):
            with patch("lkj.doctor.importlib", create=True):
                check = _check_torch_cuda()
                assert check.ok is False


class TestCheckMicrophone:
    def test_input_devices_present(self) -> None:
        fake_sd = types.SimpleNamespace(
            query_devices=lambda: [
                {"max_input_channels": 2, "name": "mic1"},
                {"max_input_channels": 0, "name": "speakers"},
                {"max_input_channels": 1, "name": "mic2"},
            ]
        )
        with patch.dict(sys.modules, {"sounddevice": fake_sd}):
            check = _check_microphone()
            assert check.ok is True
            assert "input devices=2" in check.detail

    def test_no_input_devices(self) -> None:
        fake_sd = types.SimpleNamespace(
            query_devices=lambda: [
                {"max_input_channels": 0, "name": "speakers"},
            ]
        )
        with patch.dict(sys.modules, {"sounddevice": fake_sd}):
            check = _check_microphone()
            assert check.ok is False
            assert "input devices=0" in check.detail


class TestCheckHotkey:
    def test_pynput_available(self) -> None:
        fake_pynput = types.ModuleType("pynput")
        fake_pynput.keyboard = types.ModuleType("pynput.keyboard")
        with patch.dict(sys.modules, {"pynput": fake_pynput, "pynput.keyboard": fake_pynput.keyboard}):
            check = _check_hotkey()
            assert check.ok is True


class TestCheckModel:
    def test_skip_without_warmup(self) -> None:
        cfg = AppConfig(model_name="fake/model")
        check = _check_model(cfg, warmup=False)
        assert check.ok is True
        assert "skipped" in check.detail


class TestRunDoctor:
    def test_all_pass(self) -> None:
        fake_torch = types.SimpleNamespace(
            __version__="2.5.0",
            cuda=types.SimpleNamespace(
                is_available=lambda: True,
                get_device_name=lambda i: "NVIDIA RTX 4090",
            ),
        )
        fake_sd = types.SimpleNamespace(
            query_devices=lambda: [{"max_input_channels": 1, "name": "mic"}]
        )
        fake_pynput = types.ModuleType("pynput")
        fake_pynput.keyboard = types.ModuleType("pynput.keyboard")

        with patch.dict(sys.modules, {
            "torch": fake_torch,
            "sounddevice": fake_sd,
            "pynput": fake_pynput,
            "pynput.keyboard": fake_pynput.keyboard,
        }):
            code = run_doctor(AppConfig(), warmup=False)
            assert code == 0

    def test_some_fail(self) -> None:
        """Python version too old causes failure."""
        fake_torch = types.SimpleNamespace(
            __version__="2.5.0",
            cuda=types.SimpleNamespace(is_available=lambda: False),
        )
        fake_sd = types.SimpleNamespace(
            query_devices=lambda: [{"max_input_channels": 0, "name": "speakers"}]
        )
        saved_vi = sys.version_info
        saved_torch = sys.modules.get("torch")
        saved_sd = sys.modules.get("sounddevice")
        try:
            sys.version_info = (3, 9, 0)  # type: ignore[assignment]
            sys.modules["torch"] = fake_torch
            sys.modules["sounddevice"] = fake_sd
            code = run_doctor(AppConfig(), warmup=False)
            assert code == 1
        finally:
            sys.version_info = saved_vi  # type: ignore[assignment]
            for name, saved in (("torch", saved_torch), ("sounddevice", saved_sd)):
                if saved is not None:
                    sys.modules[name] = saved
                elif name in sys.modules:
                    del sys.modules[name]
