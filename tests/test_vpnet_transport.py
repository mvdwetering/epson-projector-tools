from __future__ import annotations

import asyncio
import struct
import unittest
from pathlib import Path

from projector.model import load_model
from projector.state import ProjectorState
from transports.vpnet import VpnetTransport

_MAGIC = b"ESC/VP.net"
_VERSION = 0x10
_TYPE_CONNECT = 0x03
_HEADER_SIZE = 16


def _make_connect_packet() -> bytes:
    return _MAGIC + struct.pack("BBHBB", _VERSION, _TYPE_CONNECT, 0, 0x00, 0)


class VpnetTransportIdleTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        model_path = Path(__file__).resolve().parents[1] / "models" / "eh_tw3200.yaml"
        self.model = load_model(model_path)
        self.state = ProjectorState(self.model)

    async def _start_server(self, idle_timeout_seconds: float) -> None:
        self.transport = VpnetTransport(
            self.state,
            self.model,
            host="127.0.0.1",
            port=0,
            idle_timeout_seconds=idle_timeout_seconds,
        )
        self.server = await asyncio.start_server(
            self.transport._handle_client,
            self.transport._host,
            self.transport._port,
        )
        self.host, self.port = self.server.sockets[0].getsockname()[:2]

    async def asyncTearDown(self) -> None:
        if hasattr(self, "server"):
            self.server.close()
            await self.server.wait_closed()

    async def _connect_and_handshake(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        reader, writer = await asyncio.open_connection(self.host, self.port)
        writer.write(_make_connect_packet())
        await writer.drain()
        resp = await asyncio.wait_for(reader.readexactly(_HEADER_SIZE), timeout=0.5)
        self.assertEqual(resp[:10], _MAGIC)
        self.assertEqual(resp[14], 0x20)
        return reader, writer

    async def test_idle_session_disconnects_after_timeout(self) -> None:
        log_events: list[tuple[str, str, str]] = []
        self.state.add_command_observer(lambda transport, cmd, response: log_events.append((transport, cmd, response)))
        await self._start_server(idle_timeout_seconds=0.08)
        reader, writer = await self._connect_and_handshake()

        eof = await asyncio.wait_for(reader.read(1), timeout=0.5)
        self.assertEqual(eof, b"")
        self.assertIn(
            (
                "vpnet",
                "connection closed by emulator (inactivity timeout)",
                "IDLE_TIMEOUT",
            ),
            log_events,
        )

        writer.close()
        await writer.wait_closed()

    async def test_inbound_activity_resets_timeout_window(self) -> None:
        await self._start_server(idle_timeout_seconds=0.2)
        reader, writer = await self._connect_and_handshake()

        await asyncio.sleep(0.08)
        writer.write(b"PWR?\r")
        await writer.drain()
        resp1 = await asyncio.wait_for(reader.readuntil(b":"), timeout=0.5)
        self.assertIn(b"PWR=", resp1)

        await asyncio.sleep(0.08)
        writer.write(b"PWR?\r")
        await writer.drain()
        resp2 = await asyncio.wait_for(reader.readuntil(b":"), timeout=0.5)
        self.assertIn(b"PWR=", resp2)

        await asyncio.sleep(0.24)
        eof = await asyncio.wait_for(reader.read(1), timeout=0.5)
        self.assertEqual(eof, b"")

        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    unittest.main()
