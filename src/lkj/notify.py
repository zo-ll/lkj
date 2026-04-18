from __future__ import annotations

import shutil
import subprocess


def send_notification(title: str, message: str) -> None:
    if shutil.which("notify-send") is None:
        return

    try:
        subprocess.run(
            ["notify-send", title, message],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return
