from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pyperclip


def _copy_with_command(command: list[str], text: str) -> bool:
    try:
        result = subprocess.run(
            command,
            input=text,
            text=True,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return False

    return result.returncode == 0


def copy_to_clipboard(text: str) -> bool:
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        pass

    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
        if _copy_with_command(["wl-copy"], text):
            return True

    if os.environ.get("DISPLAY") and shutil.which("xclip"):
        if _copy_with_command(["xclip", "-selection", "clipboard"], text):
            return True

    if os.environ.get("DISPLAY") and shutil.which("xsel"):
        if _copy_with_command(["xsel", "--clipboard", "--input"], text):
            return True

    return False


def append_transcript(log_path: Path, text: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    line = f"[{stamp}] {text}\n"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)
