from __future__ import annotations

import sys
from unittest.mock import Mock

import pytest

# sounddevice needs PortAudio, not available in test env
sys.modules.setdefault("sounddevice", Mock())
sys.modules.setdefault("torch", Mock())
sys.modules.setdefault("nemo", Mock())
sys.modules.setdefault("nemo.collections", Mock())
sys.modules.setdefault("nemo.collections.asr", Mock())
sys.modules.setdefault("nemo.collections.asr.models", Mock())

from lkj.app import _normalize_hotkey  # noqa: E402


class TestNormalizeHotkey:
    def test_simple_alt_space(self) -> None:
        assert _normalize_hotkey("alt+space") == "<alt>+<space>"

    def test_ctrl_shift_letter(self) -> None:
        assert _normalize_hotkey("ctrl+shift+a") == "<ctrl>+<shift>+a"

    def test_single_letter(self) -> None:
        assert _normalize_hotkey("a") == "a"

    def test_control_synonym(self) -> None:
        assert _normalize_hotkey("control+x") == "<ctrl>+x"

    def test_super_synonym(self) -> None:
        assert _normalize_hotkey("super+space") == "<cmd>+<space>"

    def test_cmd_synonym(self) -> None:
        assert _normalize_hotkey("cmd+c") == "<cmd>+c"

    def test_enter_synonym(self) -> None:
        assert _normalize_hotkey("alt+enter") == "<alt>+<enter>"

    def test_return_synonym(self) -> None:
        assert _normalize_hotkey("ctrl+return") == "<ctrl>+<enter>"

    def test_escape(self) -> None:
        assert _normalize_hotkey("esc") == "<esc>"

    def test_escape_full_word(self) -> None:
        assert _normalize_hotkey("escape") == "<esc>"

    def test_tab(self) -> None:
        assert _normalize_hotkey("ctrl+tab") == "<ctrl>+<tab>"

    def test_function_keys(self) -> None:
        assert _normalize_hotkey("f12") == "<f12>"
        assert _normalize_hotkey("ctrl+f5") == "<ctrl>+<f5>"

    def test_already_bracketed_passed_through(self) -> None:
        assert _normalize_hotkey("<alt>+<space>") == "<alt>+<space>"

    def test_case_insensitive(self) -> None:
        assert _normalize_hotkey("CTRL+SHIFT+A") == "<ctrl>+<shift>+a"

    def test_strips_whitespace(self) -> None:
        assert _normalize_hotkey("  ctrl + alt + space  ") == "<ctrl>+<alt>+<space>"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="Hotkey is empty"):
            _normalize_hotkey("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="Hotkey is empty"):
            _normalize_hotkey("   ")

    def test_unknown_token_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported hotkey token"):
            _normalize_hotkey("foo+bar")

    def test_multi_key_combo(self) -> None:
        result = _normalize_hotkey("ctrl+alt+shift+s")
        assert result == "<ctrl>+<alt>+<shift>+s"


class TestNormalizeHotkeyEdgeCases:
    def test_plus_sign_only_is_empty(self) -> None:
        """Multiple + signs between tokens collapse."""
        with pytest.raises(ValueError, match="Hotkey is empty"):
            _normalize_hotkey("+++")

    def test_trailing_plus_ignored(self) -> None:
        """Trailing separator after token is fine."""
        result = _normalize_hotkey("alt+")
        assert result == "<alt>"

    def test_leading_plus_handled(self) -> None:
        result = _normalize_hotkey("+alt")
        assert result == "<alt>"

    def test_f_key_edge(self) -> None:
        """f0 is technically parsed as a function key; non-numeric suffix fails."""
        result = _normalize_hotkey("f0")
        assert result == "<f0>"  # parsed as function key
        with pytest.raises(ValueError, match="Unsupported hotkey token"):
            _normalize_hotkey("fx")  # f + non-digit fails


class TestPushToTalkAppInit:
    def test_config_flow(self) -> None:
        """Integration: app can be constructed without loading real models."""
        from lkj.config import AppConfig
        from lkj.app import PushToTalkApp

        cfg = AppConfig(
            start_hotkey="alt+space",
            stop_hotkey="alt+escape",
            device="cpu",
        )
        app = PushToTalkApp(cfg)
        assert app._start_hotkey == "<alt>+<space>"
        assert app._stop_hotkey == "<alt>+<esc>"

    def test_duplicate_start_and_stop_ignores_stop(self) -> None:
        from lkj.config import AppConfig
        from lkj.app import PushToTalkApp

        cfg = AppConfig(
            start_hotkey="alt+space",
            stop_hotkey="alt+space",
        )
        app = PushToTalkApp(cfg)
        assert app._stop_hotkey is None

    def test_empty_stop_hotkey_yields_none(self) -> None:
        from lkj.config import AppConfig
        from lkj.app import PushToTalkApp

        cfg = AppConfig(
            start_hotkey="alt+space",
            stop_hotkey="",
        )
        app = PushToTalkApp(cfg)
        assert app._stop_hotkey is None
