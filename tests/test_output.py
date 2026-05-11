from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from lkj.output import append_transcript, copy_to_clipboard, _copy_with_command


class TestCopyWithCommand:
    def test_successful_copy(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = _copy_with_command(["echo"], "hello")
            assert result is True
            mock_run.assert_called_once()
            assert mock_run.call_args[1]["input"] == "hello"

    def test_failed_copy(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = _copy_with_command(["false"], "hello")
            assert result is False

    def test_exception_returns_false(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _copy_with_command(["nonexistent"], "hello")
            assert result is False


class TestCopyToClipboard:
    def test_wayland_preferred(self, monkeypatch) -> None:
        monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
        monkeypatch.delenv("DISPLAY", raising=False)

        called = []

        class FakeStdin:
            def write(self, s):
                pass

            def close(self):
                pass

        class FakeProc:
            def __init__(self, argv, *a, **kw):
                called.append(argv)
                self.stdin = FakeStdin()
                self.returncode = None

            def poll(self):
                return 0

            def terminate(self):
                pass

        with patch("subprocess.Popen", FakeProc):
            with patch("shutil.which", return_value=True):
                result = copy_to_clipboard("test")
                assert result is True
                assert len(called) > 0
                assert called[0][0] == "wl-copy"

    def test_xclip_fallback(self, monkeypatch) -> None:
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.setenv("DISPLAY", ":0")

        called = []

        class FakeStdin:
            def write(self, s):
                pass

            def close(self):
                pass

        class FakeProc:
            def __init__(self, argv, *a, **kw):
                called.append(argv)
                self.stdin = FakeStdin()
                self.returncode = None

            def poll(self):
                return 0

            def terminate(self):
                pass

        with patch("subprocess.Popen", FakeProc):
            with patch("shutil.which", return_value=True):
                result = copy_to_clipboard("test")
                assert result is True
                assert len(called) > 0
                assert called[0][0] == "xclip"

    def test_pyperclip_fallback(self, monkeypatch) -> None:
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.delenv("DISPLAY", raising=False)

        with patch("pyperclip.copy") as mock_copy:
            result = copy_to_clipboard("test")
            assert result is True
            mock_copy.assert_called_once_with("test")

    def test_all_fail_returns_false(self, monkeypatch) -> None:
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.delenv("DISPLAY", raising=False)

        with patch("pyperclip.copy", side_effect=Exception("fail")):
            with patch("shutil.which", return_value=False):
                result = copy_to_clipboard("test")
                assert result is False


class TestAppendTranscript:
    def test_creates_file_with_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "transcripts.log"
            append_transcript(log_path, "hello world")
            content = log_path.read_text()
            assert "hello world" in content
            # Verify timestamp format
            line = content.strip()
            assert line.startswith("[")
            assert "] " in line
            stamp = line.split("]")[0].lstrip("[")
            # Stamp ends with Z; parse its YMD part
            stamp_no_z = stamp.rstrip("Z")
            dt = datetime.strptime(stamp_no_z, "%Y-%m-%d %H:%M:%S")
            assert dt.year >= 2025
            assert 1 <= dt.month <= 12
            assert 1 <= dt.day <= 31

    def test_appends_to_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "transcripts.log"
            log_path.write_text("[2025-01-01 00:00:00Z] old message\n")
            append_transcript(log_path, "new message")
            lines = log_path.read_text().strip().split("\n")
            assert len(lines) == 2
            assert "old message" in lines[0]
            assert "new message" in lines[1]

    def test_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "deep" / "nested" / "transcripts.log"
            append_transcript(log_path, "test")
            assert log_path.exists()
