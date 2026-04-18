from __future__ import annotations

import shutil
import subprocess
import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import messagebox, ttk

from .config import DEFAULT_CONFIG_PATH, load_config, save_config


SYSTEM_DEFAULT_LABEL = "system default"


class SettingsWindow:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = load_config(config_path=self.config_path)

        self.root = tk.Tk()
        self.root.title("LKJ Settings")
        self.root.resizable(False, False)

        self._status_var = tk.StringVar(value=f"Config file: {self.config_path}")

        self._model_name_var = tk.StringVar(value=self.config.model_name)
        self._device_var = tk.StringVar(value=self.config.device)
        self._input_device_options, self._input_device_map = _discover_input_devices()
        self._input_device_var = tk.StringVar(
            value=self._label_for_input_device(self.config.input_device)
        )
        self._preload_model_var = tk.BooleanVar(value=self.config.preload_model)
        self._unload_model_after_var = tk.StringVar(
            value=str(self.config.unload_model_after_seconds)
        )
        self._daemon_poll_var = tk.StringVar(value=str(self.config.daemon_poll_seconds))
        self._sample_rate_var = tk.StringVar(value=str(self.config.sample_rate))
        self._channels_var = tk.StringVar(value=str(self.config.channels))
        self._start_hotkey_var = tk.StringVar(value=self.config.start_hotkey)
        self._stop_hotkey_var = tk.StringVar(value=self.config.stop_hotkey)
        self._min_seconds_var = tk.StringVar(value=str(self.config.min_seconds))
        self._auto_stop_silence_var = tk.StringVar(
            value=str(self.config.auto_stop_silence_seconds)
        )
        self._silence_threshold_var = tk.StringVar(
            value=str(self.config.silence_threshold)
        )
        self._offline_only_var = tk.BooleanVar(value=self.config.offline_only)
        self._transcript_log_var = tk.StringVar(
            value=str(self.config.transcript_log_path)
        )

        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=14)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        self._add_entry(frame, 0, "Model", self._model_name_var)
        self._add_entry(frame, 1, "Device", self._device_var)
        self._add_input_device_selector(frame, 2)
        self._add_entry(frame, 3, "Sample rate", self._sample_rate_var)
        self._add_entry(frame, 4, "Channels", self._channels_var)
        self._add_entry(frame, 5, "Start hotkey", self._start_hotkey_var)
        self._add_entry(frame, 6, "Stop hotkey", self._stop_hotkey_var)
        self._add_entry(frame, 7, "Min seconds", self._min_seconds_var)
        self._add_entry(frame, 8, "Auto-stop silence", self._auto_stop_silence_var)
        self._add_entry(frame, 9, "Silence threshold", self._silence_threshold_var)
        self._add_entry(frame, 10, "Unload model idle", self._unload_model_after_var)
        self._add_entry(frame, 11, "Daemon poll", self._daemon_poll_var)
        self._add_entry(frame, 12, "Transcript log", self._transcript_log_var)

        preload = ttk.Checkbutton(
            frame,
            text="Preload ASR model on startup",
            variable=self._preload_model_var,
        )
        preload.grid(row=13, column=0, columnspan=2, sticky="w", pady=(6, 4))

        offline = ttk.Checkbutton(
            frame,
            text="Offline only",
            variable=self._offline_only_var,
        )
        offline.grid(row=14, column=0, columnspan=2, sticky="w", pady=(2, 4))

        note = ttk.Label(
            frame,
            text="If daemon is installed, Save automatically restarts it.",
        )
        note.grid(row=15, column=0, columnspan=2, sticky="w", pady=(0, 8))

        button_row = ttk.Frame(frame)
        button_row.grid(row=16, column=0, columnspan=2, sticky="e")

        save_button = ttk.Button(button_row, text="Save", command=self._save)
        save_button.grid(row=0, column=0, padx=(0, 6))

        close_button = ttk.Button(button_row, text="Close", command=self.root.destroy)
        close_button.grid(row=0, column=1)

        status = ttk.Label(frame, textvariable=self._status_var)
        status.grid(row=17, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _add_entry(
        self,
        frame: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> None:
        widget = ttk.Label(frame, text=label)
        widget.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)

        entry = ttk.Entry(frame, textvariable=variable, width=48)
        entry.grid(row=row, column=1, sticky="ew", pady=2)

    def _add_input_device_selector(self, frame: ttk.Frame, row: int) -> None:
        widget = ttk.Label(frame, text="Input device")
        widget.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)

        self._input_device_combo = ttk.Combobox(
            frame,
            textvariable=self._input_device_var,
            values=self._input_device_options,
            width=48,
        )
        self._input_device_combo.grid(row=row, column=1, sticky="ew", pady=2)

        refresh = ttk.Button(frame, text="Refresh", command=self._refresh_input_devices)
        refresh.grid(row=row, column=2, sticky="w", padx=(6, 0), pady=2)

    def _label_for_input_device(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return SYSTEM_DEFAULT_LABEL

        if normalized.isdigit():
            prefix = f"{normalized}:"
            for label in self._input_device_options:
                if label.startswith(prefix):
                    return label

        for label, mapped in self._input_device_map.items():
            if mapped == normalized:
                return label

        return normalized

    def _resolve_input_device(self) -> str:
        selected = self._input_device_var.get().strip()
        if not selected or selected == SYSTEM_DEFAULT_LABEL:
            return ""

        mapped = self._input_device_map.get(selected)
        if mapped is not None:
            return mapped

        prefix = selected.split(":", 1)[0].strip()
        if prefix.isdigit():
            return prefix

        return selected

    def _refresh_input_devices(self) -> None:
        current = self._resolve_input_device()
        self._input_device_options, self._input_device_map = _discover_input_devices()
        self._input_device_combo.configure(values=self._input_device_options)
        self._input_device_var.set(self._label_for_input_device(current))
        self._status_var.set("Input device list refreshed")

    def _save(self) -> None:
        try:
            sample_rate = int(self._sample_rate_var.get().strip())
            channels = int(self._channels_var.get().strip())
            min_seconds = float(self._min_seconds_var.get().strip())
            auto_stop_silence_seconds = float(self._auto_stop_silence_var.get().strip())
            silence_threshold = float(self._silence_threshold_var.get().strip())
            unload_model_after_seconds = float(
                self._unload_model_after_var.get().strip()
            )
            daemon_poll_seconds = float(self._daemon_poll_var.get().strip())
        except ValueError:
            messagebox.showerror(
                "Invalid input", "Numeric fields must contain valid numbers."
            )
            return

        start_hotkey = self._start_hotkey_var.get().strip()
        if not start_hotkey:
            messagebox.showerror("Invalid input", "Start hotkey cannot be empty.")
            return

        if sample_rate <= 0 or channels <= 0:
            messagebox.showerror(
                "Invalid input", "Sample rate and channels must be > 0."
            )
            return

        if min_seconds < 0 or auto_stop_silence_seconds <= 0:
            messagebox.showerror(
                "Invalid input",
                "Min seconds must be >= 0 and auto-stop silence must be > 0.",
            )
            return

        if silence_threshold < 0:
            messagebox.showerror("Invalid input", "Silence threshold must be >= 0.")
            return

        if unload_model_after_seconds < 0:
            messagebox.showerror(
                "Invalid input",
                "Unload model idle seconds must be >= 0.",
            )
            return

        if daemon_poll_seconds <= 0:
            messagebox.showerror(
                "Invalid input",
                "Daemon poll must be > 0 seconds.",
            )
            return

        updated = replace(
            self.config,
            model_name=self._model_name_var.get().strip(),
            device=self._device_var.get().strip(),
            input_device=self._resolve_input_device(),
            preload_model=bool(self._preload_model_var.get()),
            unload_model_after_seconds=unload_model_after_seconds,
            daemon_poll_seconds=daemon_poll_seconds,
            sample_rate=sample_rate,
            channels=channels,
            start_hotkey=start_hotkey,
            stop_hotkey=self._stop_hotkey_var.get().strip(),
            min_seconds=min_seconds,
            auto_stop_silence_seconds=auto_stop_silence_seconds,
            silence_threshold=silence_threshold,
            offline_only=bool(self._offline_only_var.get()),
            transcript_log_path=Path(
                self._transcript_log_var.get().strip()
            ).expanduser(),
        )

        path = save_config(updated, config_path=self.config_path)
        self.config = updated

        restarted = _restart_daemon_if_installed()
        if restarted:
            self._status_var.set(f"Saved to {path}. Daemon restarted.")
        else:
            self._status_var.set(f"Saved to {path}.")

    def run(self) -> None:
        self.root.mainloop()


def _restart_daemon_if_installed() -> bool:
    if shutil.which("systemctl") is not None:
        try:
            probe = subprocess.run(
                ["systemctl", "--user", "cat", "lkj-daemon.service"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if probe.returncode == 0:
                restart = subprocess.run(
                    ["systemctl", "--user", "restart", "lkj-daemon.service"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return restart.returncode == 0
        except Exception:
            return False

    launcher = Path.home() / ".local" / "bin" / "lkj"
    if not launcher.exists() or shutil.which("pgrep") is None:
        return False

    pattern = "\\.local/bin/lkj daemon"
    probe = subprocess.run(
        ["pgrep", "-f", pattern],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode != 0:
        return False

    if shutil.which("pkill") is not None:
        subprocess.run(
            ["pkill", "-f", pattern],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    subprocess.Popen(
        [str(launcher), "daemon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def run_settings_window(config_path: Path | None = None) -> None:
    window = SettingsWindow(config_path=config_path)
    window.run()


def _discover_input_devices() -> tuple[list[str], dict[str, str]]:
    options = [SYSTEM_DEFAULT_LABEL]
    mapping = {SYSTEM_DEFAULT_LABEL: ""}

    try:
        import sounddevice as sd

        default_input: int | None = None
        default_device = sd.default.device
        if isinstance(default_device, (list, tuple)) and default_device:
            if default_device[0] is not None:
                default_input = int(default_device[0])
        elif isinstance(default_device, int):
            default_input = default_device

        devices = sd.query_devices()
        for index, device in enumerate(devices):
            input_channels = int(device.get("max_input_channels", 0) or 0)
            if input_channels <= 0:
                continue

            name = str(device.get("name", f"device {index}"))
            sample_rate = int(float(device.get("default_samplerate", 0) or 0))
            label = f"{index}: {name} ({input_channels}ch @ {sample_rate}Hz)"
            if default_input is not None and index == default_input:
                label = f"{label} [default]"

            options.append(label)
            mapping[label] = name
    except Exception:
        pass

    return options, mapping
