from __future__ import annotations

import argparse
from pathlib import Path

from .config import AppConfig, load_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lkj", description="Local Parakeet voice-to-text"
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="Path to JSON config file"
    )
    parser.add_argument("--model", type=str, default=None, help="Model name")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda or cpu)")
    parser.add_argument(
        "--input-device",
        type=str,
        default=None,
        help="Audio input device (e.g. pulse, default, or name)",
    )
    parser.add_argument(
        "--start-hotkey", type=str, default=None, help="Start recording hotkey"
    )
    parser.add_argument(
        "--stop-hotkey", type=str, default=None, help="Stop recording hotkey"
    )
    parser.add_argument(
        "--push-key",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--sample-rate", type=int, default=None, help="Recording sample rate"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=None,
        help="Enable offline mode for model loading",
    )
    parser.add_argument(
        "--online",
        action="store_true",
        default=None,
        help="Disable offline mode for model loading",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("gui", help="Open settings window")
    subparsers.add_parser("daemon", help="Run background hotkey daemon")
    subparsers.add_parser("run", help="Alias for daemon")

    once = subparsers.add_parser("once", help="Record once and transcribe")
    once.add_argument("--seconds", type=float, default=5.0, help="Seconds to record")

    doctor = subparsers.add_parser("doctor", help="Run environment diagnostics")
    doctor.add_argument(
        "--warmup", action="store_true", help="Load model during diagnostics"
    )

    return parser


def _resolve_config(args: argparse.Namespace) -> AppConfig:
    offline_value = None
    if args.offline:
        offline_value = True
    if args.online:
        offline_value = False

    return load_config(
        config_path=args.config,
        model_name=args.model,
        device=args.device,
        input_device=args.input_device,
        start_hotkey=args.start_hotkey,
        stop_hotkey=args.stop_hotkey,
        push_key=args.push_key,
        sample_rate=args.sample_rate,
        offline_only=offline_value,
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    config = _resolve_config(args)

    if args.command in (None, "gui"):
        from .gui import run_settings_window

        run_settings_window(config_path=args.config)
        return

    if args.command in ("daemon", "run"):
        from .app import PushToTalkApp

        PushToTalkApp(config).run()
        return

    if args.command == "once":
        from .app import transcribe_once

        transcribe_once(config, seconds=args.seconds)
        return

    if args.command == "doctor":
        from .doctor import run_doctor

        code = run_doctor(config, warmup=args.warmup)
        raise SystemExit(code)

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
