from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from lkj.config import AppConfig, _from_dict, load_config, save_config, DEFAULT_LOG_PATH


class TestFromDict:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _from_dict({})
        assert cfg.model_name == "nvidia/parakeet-tdt-0.6b-v2"
        assert cfg.device == "cuda"
        assert cfg.sample_rate == 16000
        assert cfg.start_hotkey == "alt+space"

    def test_populates_all_known_fields(self) -> None:
        raw = {
            "model_name": "nvidia/stt_en_citrinet_512",
            "device": "cpu",
            "input_device": "pulse",
            "preload_model": False,
            "unload_model_after_seconds": 30.0,
            "daemon_poll_seconds": 0.5,
            "sample_rate": 22050,
            "channels": 2,
            "start_hotkey": "ctrl+shift+a",
            "stop_hotkey": "ctrl+shift+z",
            "auto_stop_enabled": True,
            "min_seconds": 1.0,
            "auto_stop_silence_seconds": 2.0,
            "silence_threshold": 0.01,
            "offline_only": False,
            "remove_fillers": False,
            "save_transcripts": True,
            "transcript_log_path": "/tmp/log.txt",
        }
        cfg = _from_dict(raw)
        assert cfg.model_name == "nvidia/stt_en_citrinet_512"
        assert cfg.device == "cpu"
        assert cfg.input_device == "pulse"
        assert cfg.preload_model is False
        assert cfg.unload_model_after_seconds == 30.0
        assert cfg.daemon_poll_seconds == 0.5
        assert cfg.sample_rate == 22050
        assert cfg.channels == 2
        assert cfg.start_hotkey == "ctrl+shift+a"
        assert cfg.stop_hotkey == "ctrl+shift+z"
        assert cfg.auto_stop_enabled is True
        assert cfg.min_seconds == 1.0
        assert cfg.auto_stop_silence_seconds == 2.0
        assert cfg.silence_threshold == 0.01
        assert cfg.offline_only is False
        assert cfg.remove_fillers is False
        assert cfg.save_transcripts is True
        assert cfg.transcript_log_path == Path("/tmp/log.txt")

    def test_push_key_falls_back_to_start_hotkey(self) -> None:
        cfg = _from_dict({"push_key": "alt+x"})
        assert cfg.start_hotkey == "alt+x"

    def test_start_hotkey_overrides_push_key(self) -> None:
        cfg = _from_dict({"push_key": "alt+x", "start_hotkey": "ctrl+y"})
        assert cfg.start_hotkey == "ctrl+y"

    def test_expands_home_in_log_path(self) -> None:
        cfg = _from_dict({"transcript_log_path": "~/logs/lkj.log"})
        assert str(cfg.transcript_log_path).startswith(str(Path.home()))


class TestLoadConfig:
    def test_returns_defaults_when_no_file(self) -> None:
        cfg = load_config(config_path=Path("/nonexistent/path.json"))
        assert cfg.model_name == "nvidia/parakeet-tdt-0.6b-v2"

    def test_loads_from_file(self) -> None:
        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json.dumps({"sample_rate": 8000, "channels": 1}))
            f.flush()
            cfg = load_config(config_path=Path(f.name))
        Path(f.name).unlink(missing_ok=True)
        assert cfg.sample_rate == 8000

    def test_cli_overrides_file(self) -> None:
        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json.dumps({"device": "cuda"}))
            f.flush()
            cfg = load_config(config_path=Path(f.name), device="cpu")
        Path(f.name).unlink(missing_ok=True)
        assert cfg.device == "cpu"

    def test_cli_overrides_offline_only_true(self) -> None:
        cfg = load_config(offline_only=True)
        assert cfg.offline_only is True

    def test_cli_overrides_offline_only_false(self) -> None:
        cfg = load_config(offline_only=False)
        assert cfg.offline_only is False

    def test_push_key_cli_fallthrough(self) -> None:
        cfg = load_config(push_key="alt+p")
        assert cfg.start_hotkey == "alt+p"

    def test_start_hotkey_cli_wins_over_push_key(self) -> None:
        cfg = load_config(start_hotkey="alt+s", push_key="alt+p")
        assert cfg.start_hotkey == "alt+s"


class TestSaveConfig:
    def test_writes_valid_json(self) -> None:
        cfg = AppConfig(sample_rate=44100, min_seconds=0.5)
        with NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = save_config(cfg, config_path=Path(f.name))
        try:
            data = json.loads(Path(path).read_text())
            assert data["sample_rate"] == 44100
            assert data["min_seconds"] == 0.5
            assert "model_name" in data
        finally:
            Path(f.name).unlink(missing_ok=True)

    def test_roundtrip(self) -> None:
        original = AppConfig(
            model_name="nvidia/canary-1b",
            device="cpu",
            input_device="default",
            preload_model=False,
            unload_model_after_seconds=60.0,
            daemon_poll_seconds=0.3,
            sample_rate=22050,
            channels=1,
            start_hotkey="ctrl+shift+r",
            stop_hotkey="ctrl+shift+s",
            auto_stop_enabled=True,
            min_seconds=0.8,
            auto_stop_silence_seconds=2.5,
            silence_threshold=0.005,
            offline_only=False,
            remove_fillers=False,
            save_transcripts=True,
            transcript_log_path=Path("/tmp/lkj.log"),
        )
        with NamedTemporaryFile(suffix=".json", delete=False) as f:
            save_config(original, config_path=Path(f.name))
            loaded = load_config(config_path=Path(f.name))
        Path(f.name).unlink(missing_ok=True)

        assert loaded.model_name == original.model_name
        assert loaded.device == original.device
        assert loaded.input_device == original.input_device
        assert loaded.preload_model == original.preload_model
        assert loaded.unload_model_after_seconds == original.unload_model_after_seconds
        assert loaded.daemon_poll_seconds == original.daemon_poll_seconds
        assert loaded.sample_rate == original.sample_rate
        assert loaded.channels == original.channels
        assert loaded.start_hotkey == original.start_hotkey
        assert loaded.stop_hotkey == original.stop_hotkey
        assert loaded.auto_stop_enabled == original.auto_stop_enabled
        assert loaded.min_seconds == original.min_seconds
        assert loaded.auto_stop_silence_seconds == original.auto_stop_silence_seconds
        assert loaded.silence_threshold == original.silence_threshold
        assert loaded.offline_only == original.offline_only
        assert loaded.remove_fillers == original.remove_fillers
        assert loaded.save_transcripts == original.save_transcripts
        assert loaded.transcript_log_path == original.transcript_log_path


class TestAppConfigDefaults:
    def test_default_transcript_log_path(self) -> None:
        assert AppConfig().transcript_log_path == DEFAULT_LOG_PATH
