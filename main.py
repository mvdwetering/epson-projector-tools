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
from transports.serial import SerialTransport
from transports.vpnet import VpnetTransport
from transports.http import HttpTransport
from ui.app import EmulatorApp


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Epson projector emulator (serial TCP / ESC/VP.net / HTTP)."
    )
    parser.add_argument(
        "--model",
        default="eh_tw3200",
        help="Model name (file in models/) or path to a YAML file. Default: eh_tw3200",
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
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Logging level (goes to stderr). Default: WARNING",
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    # Resolve model path: bare name → models/<name>.yaml, otherwise treat as path
    model_path = Path(args.model)
    if not model_path.suffix:
        model_path = Path(__file__).parent / "models" / f"{args.model}.yaml"

    model = load_model(model_path)
    state = ProjectorState(model)

    transports = [
        SerialTransport(state, model, host=args.host, port=args.serial_port),
        VpnetTransport(state, model, host=args.host, port=args.vpnet_port),
        HttpTransport(state, model, host=args.host, port=args.http_port),
    ]

    app = EmulatorApp(state=state, model=model, transports=transports)
    app.run()


if __name__ == "__main__":
    main()
