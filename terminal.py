from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional

from client.base import AbstractProjectorClient
from client.serial import SerialClient
from client.vpnet import VpnetClient
from client.http import HttpClient
from projector.model import load_model, ModelDef


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
        return VpnetClient(host, port)
    if protocol == "http":
        return HttpClient(host, port, password)
    raise ValueError(f"Unknown protocol: {protocol!r}")


def _args_sufficient(args: argparse.Namespace) -> bool:
    """Return True if enough CLI args are present to skip the connect dialog."""
    if not args.host:
        return False
    if not args.protocol:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Epson projector interactive terminal")
    parser.add_argument("--protocol", choices=["serial", "vpnet", "http"], default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None,
                        help="Override default port (serial=12345, vpnet=3629, http=80). "
                             "Use 8080 when targeting the local emulator over HTTP.")
    parser.add_argument("--password", default="", help="HTTP Digest password")
    parser.add_argument("--model", default=None, help="Path to model YAML (optional)")
    args = parser.parse_args()

    model: Optional[ModelDef] = None
    if args.model:
        try:
            model = load_model(args.model)
        except Exception as exc:
            print(f"Warning: could not load model '{args.model}': {exc}", file=sys.stderr)

    # Determine initial client (None = show connect dialog first)
    client: Optional[AbstractProjectorClient] = None
    initial_params: Optional[dict] = None

    if _args_sufficient(args):
        protocol = args.protocol
        port = args.port if args.port is not None else _DEFAULT_PORTS[protocol]
        client = _build_client(protocol, args.host, port, args.password)
        initial_params = {
            "protocol": protocol,
            "host": args.host,
            "port": port,
            "password": args.password,
        }

    # Import here to avoid Textual startup cost during arg parse errors
    from ui.terminal_app import TerminalApp

    app = TerminalApp(
        client=client,
        model=model,
        initial_params=initial_params,
    )
    app.run()


if __name__ == "__main__":
    main()
