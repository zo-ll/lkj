from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pyperclip


_CLIP_OWNER: subprocess.Popen[str] | None = None
_CLIP_OWNER_LOCK = threading.Lock()


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


def _stop_clip_owner() -> None:
    global _CLIP_OWNER

    if _CLIP_OWNER is None:
        return

    if _CLIP_OWNER.poll() is None:
        _CLIP_OWNER.terminate()
        try:
            _CLIP_OWNER.wait(timeout=0.2)
        except Exception:
            _CLIP_OWNER.kill()
    _CLIP_OWNER = None


def _copy_with_owner_process(command: list[str], text: str) -> bool:
    global _CLIP_OWNER

    with _CLIP_OWNER_LOCK:
        _stop_clip_owner()

        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                start_new_session=True,
            )
        except Exception:
            return False

        try:
            assert proc.stdin is not None
            proc.stdin.write(text)
            proc.stdin.close()
        except Exception:
            proc.terminate()
            return False

        time.sleep(0.05)
        code = proc.poll()
        if code not in (None, 0):
            return False

        _CLIP_OWNER = proc
        return True


def copy_to_clipboard(text: str) -> bool:
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
        if _copy_with_owner_process(["wl-copy", "--foreground"], text):
            return True

    if os.environ.get("DISPLAY") and shutil.which("xclip"):
        if _copy_with_owner_process(
            ["xclip", "-selection", "clipboard", "-loops", "1"],
            text,
        ):
            return True

    if os.environ.get("DISPLAY") and shutil.which("xsel"):
        if _copy_with_command(["xsel", "--clipboard", "--input", "--keep"], text):
            return True

    try:
        pyperclip.copy(text)
        return True
    except Exception:
        pass

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
