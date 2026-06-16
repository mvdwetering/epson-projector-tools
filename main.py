#!/usr/bin/env python3
"""
Epson projector emulator — multi-transport entry point.

Starts three concurrent transports (serial TCP, ESC/VP.net TCP, HTTP stub)
all sharing one emulated projector state, with an interactive Textual TUI.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from projector.model import load_model
from projector.state import ProjectorState
from projector.power import PowerSequencer
from transports.http import PasswordStore
from ui.app import EmulatorApp, EmulatorRuntimeConfig


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Epson projector emulator (serial TCP / ESC/VP.net / HTTP)."
    )
    parser.add_argument(
        "--model",
        default="TW3200",
        help="Model name (file in models/) or path to a JSON file. Default: TW3200",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host interface to bind all transports to. Default: 0.0.0.0",
    )
    parser.add_argument(
        "--serial-port",
        type=int,
        default=12345,
        help="TCP port for serial/ESC/VP21 transport. Default: 12345",
    )
    parser.add_argument(
        "--vpnet-port",
        type=int,
        default=3629,
        help="TCP port for ESC/VP.net transport. Default: 3629",
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=8080,
        help="TCP port for HTTP transport. Default: 8080",
    )
    parser.add_argument(
        "--password",
        action="store_true",
        help="Start with password authentication enabled on all network transports (ESC/VP.net and HTTP). Default password: emulatorpassword. Use TUI keys to toggle auth and change password at runtime.",
    )
    parser.add_argument(
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Logging level (goes to stderr). Default: WARNING",
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    # Resolve model path: bare name -> models/<name>.json, otherwise treat as path.
    model_path = Path(args.model)
    if not model_path.suffix:
        model_path = Path(__file__).parent / "models" / f"{args.model}.json"

    model = load_model(model_path)
    state = ProjectorState(model)

    sequencer = PowerSequencer()

    password_store = PasswordStore("emulatorpassword", enabled=args.password)
    runtime_config = EmulatorRuntimeConfig(
        host=args.host,
        serial_port=args.serial_port,
        vpnet_port=args.vpnet_port,
        http_port=args.http_port,
        models_dir=Path(__file__).parent / "models",
    )

    app = EmulatorApp(
        state=state,
        model=model,
        transports=None,
        runtime_config=runtime_config,
        password_store=password_store,
        power_sequencer=sequencer,
    )
    app.run()


if __name__ == "__main__":
    main()
