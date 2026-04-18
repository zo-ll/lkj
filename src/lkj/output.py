from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pyperclip


def copy_to_clipboard(text: str) -> None:
    pyperclip.copy(text)


def append_transcript(log_path: Path, text: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    line = f"[{stamp}] {text}\n"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)
