from __future__ import annotations

import sys
from unittest.mock import patch, Mock

import pytest

from lkj.cli import _build_parser, _resolve_config


class TestBuildParser:
    def test_default_command_is_none(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.command is None

    def test_gui_command(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["gui"])
        assert args.command == "gui"

    def test_daemon_command(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["daemon"])
        assert args.command == "daemon"

    def test_run_alias(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["run"])
        assert args.command == "run"

    def test_once_command(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["once", "--seconds", "10.5"])
        assert args.command == "once"
        assert args.seconds == 10.5

    def test_once_default_seconds(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["once"])
        assert args.seconds == 5.0

    def test_doctor_command(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["doctor"])
        assert args.command == "doctor"
        assert args.warmup is False

    def test_doctor_warmup_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["doctor", "--warmup"])
        assert args.warmup is True

    def test_global_options(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--device", "cpu", "--offline"])
        assert args.device == "cpu"
        assert args.offline is True

    def test_offline_online_mutually_exclusive(self) -> None:
        """Both flags can be set but _resolve_config handles priority."""
        parser = _build_parser()
        args = parser.parse_args(["--offline", "--online", "doctor"])
        assert args.offline is True
        assert args.online is True

    def test_unknown_command_raises(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["unknown"])


class TestResolveConfig:
    def test_no_arguments_returns_defaults(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([])
        cfg = _resolve_config(args)
        assert cfg.model_name == "nvidia/parakeet-tdt-0.6b-v2"

    def test_cli_device_override(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--device", "cpu"])
        cfg = _resolve_config(args)
        assert cfg.device == "cpu"

    def test_offline_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--offline"])
        cfg = _resolve_config(args)
        assert cfg.offline_only is True

    def test_online_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--online"])
        cfg = _resolve_config(args)
        assert cfg.offline_only is False

    def test_online_wins_over_offline(self) -> None:
        """If both flags are set, --online (last processed) wins."""
        parser = _build_parser()
        args = parser.parse_args(["--offline", "--online"])
        cfg = _resolve_config(args)
        assert cfg.offline_only is False

    def test_push_key_suppressed_from_help(self) -> None:
        parser = _build_parser()
        help_text = parser.format_help()
        assert "--push-key" not in help_text

    def test_model_override(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--model", "nvidia/canary-1b"])
        cfg = _resolve_config(args)
        assert cfg.model_name == "nvidia/canary-1b"

    def test_input_device_override(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--input-device", "pulse"])
        cfg = _resolve_config(args)
        assert cfg.input_device == "pulse"

    def test_start_hotkey_override(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--start-hotkey", "ctrl+a"])
        cfg = _resolve_config(args)
        assert cfg.start_hotkey == "ctrl+a"


class TestMain:
    def test_gui_dispatches(self, monkeypatch) -> None:
        """Patch the lazy-imported run_settings_window at the source."""
        mock_gui = Mock()
        # tkinter may not be installed; mock the gui module entirely
        sys.modules["tkinter"] = Mock()
        sys.modules["tkinter.ttk"] = Mock()
        monkeypatch.setattr("lkj.gui.run_settings_window", mock_gui)
        import lkj.cli
        original_argv = sys.argv[:]
        try:
            sys.argv = ["lkj"]
            lkj.cli.main()
            mock_gui.assert_called_once()
        finally:
            sys.argv = original_argv

    def test_doctor_dispatches(self, monkeypatch) -> None:
        """Patch the lazy-imported run_doctor at the source."""
        mock_doctor = Mock(return_value=0)
        monkeypatch.setattr("lkj.doctor.run_doctor", mock_doctor)
        import lkj.cli
        original_argv = sys.argv[:]
        try:
            sys.argv = ["lkj", "doctor"]
            with pytest.raises(SystemExit):
                lkj.cli.main()
            mock_doctor.assert_called_once()
        finally:
            sys.argv = original_argv
