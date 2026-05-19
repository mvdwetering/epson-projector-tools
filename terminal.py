from __future__ import annotations

import argparse
import sys
from typing import Optional

from client.base import AbstractProjectorClient
from client.serial import SerialClient
from client.vpnet import VpnetClient
from client.http import HttpClient


_DEFAULT_PORTS = {"serial": 12345, "vpnet": 3629, "http": 80}


def _build_client(
    protocol: str,
    host: str,
    port: int,
    password: str = "",
) -> AbstractProjectorClient:
    if protocol == "serial":
        return SerialClient(host, port)
    if protocol == "vpnet":
        return VpnetClient(host, port, password=password)
    if protocol == "http":
        return HttpClient(host, port, password)
    raise ValueError(f"Unknown protocol: {protocol!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Epson projector interactive terminal")
    parser.add_argument(
        "preset_name",
        nargs="?",
        default=None,
        help="Named preset to connect to immediately (skips all dialogs)",
    )
    args = parser.parse_args()

    client: Optional[AbstractProjectorClient] = None
    initial_params: Optional[dict] = None

    if args.preset_name is not None:
        from client.presets import find_preset
        preset = find_preset(args.preset_name)
        if preset is None:
            print(f"Error: preset '{args.preset_name}' not found.", file=sys.stderr)
            sys.exit(1)
        protocol = preset["protocol"]
        host = preset["host"]
        port = preset["port"]
        password = preset.get("password", "")
        client = _build_client(protocol, host, port, password)
        initial_params = preset

    # Import here to avoid Textual startup cost during arg parse errors
    from ui.terminal_app import TerminalApp

    app = TerminalApp(client=client, initial_params=initial_params)
    app.run()


if __name__ == "__main__":
    main()
