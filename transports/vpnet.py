from __future__ import annotations

import asyncio
import logging
import struct
from typing import TYPE_CHECKING

from projector.model import ModelDef
from projector.state import ProjectorState
from transports.base import BaseTransport, handle_escvp21_stream

if TYPE_CHECKING:
    from transports.http import PasswordStore

logger = logging.getLogger(__name__)

# ESC/VP.net protocol constants (hardcoded per spec — not model-configurable)
_MAGIC = b"ESC/VP.net"
_VERSION = 0x10
_TYPE_HELLO = 0x01
_TYPE_CONNECT = 0x03
_STATUS_OK = 0x20
_HEADER_SIZE = 16   # 10 (magic) + 1 (ver) + 1 (type) + 2 (reserved) + 1 (status) + 1 (num_headers)
_EXTRA_HEADER_SIZE = 18


def _make_packet(pkt_type: int, status: int, num_headers: int = 0) -> bytes:
    return _MAGIC + struct.pack("BBHBb", _VERSION, pkt_type, 0, status, num_headers)


class VpnetTransport(BaseTransport):
    def __init__(
        self,
        state: ProjectorState,
        model: ModelDef,
        host: str = "0.0.0.0",
        port: int = 3629,
        password_store: PasswordStore | None = None,
    ) -> None:
        self._state = state
        self._model = model
        self._host = host
        self._port = port
        self._password_store = password_store

    async def start(self) -> None:
        server = await asyncio.start_server(
            self._handle_client, self._host, self._port
        )
        logger.info("ESC/VP.net transport listening on %s:%s", self._host, self._port)
        async with server:
            await server.serve_forever()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peer = writer.get_extra_info("peername", ("?", 0))
        try:
            if not await self._handshake(reader, writer):
                return
            await handle_escvp21_stream(reader, writer, self._state, self._model, "vpnet")
        except (asyncio.IncompleteReadError, ConnectionResetError, OSError):
            logger.debug("vpnet: connection closed during handshake from %s", peer)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _handshake(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> bool:
        """Perform HELLO → CONNECT handshake. Returns True on success."""
        # Read first packet
        header = await reader.readexactly(_HEADER_SIZE)
        if header[:10] != _MAGIC:
            logger.warning("vpnet: invalid magic bytes, closing connection")
            return False

        pkt_type = header[11]

        # Optional HELLO exchange
        if pkt_type == _TYPE_HELLO:
            await self._skip_extra_headers(reader, header[15])
            writer.write(_make_packet(_TYPE_HELLO, _STATUS_OK))
            await writer.drain()
            # Read next packet (expected: CONNECT)
            header = await reader.readexactly(_HEADER_SIZE)
            if header[:10] != _MAGIC:
                return False
            pkt_type = header[11]

        if pkt_type != _TYPE_CONNECT:
            logger.warning("vpnet: expected CONNECT (0x03), got 0x%02x", pkt_type)
            return False

        headers = await self._parse_extra_headers(reader, header[15])

        if self._password_store is not None:
            password_header = headers.get(0x01)  # 0x01 = Password identifier
            if password_header is None:
                logger.warning("vpnet: password required but not provided, rejecting")
                writer.write(_make_packet(_TYPE_CONNECT, 0x41))  # Unauthorized
                await writer.drain()
                return False
            _, pw_bytes = password_header
            sent_password = pw_bytes.rstrip(b"\x00").decode("ascii", errors="replace")
            if sent_password != self._password_store.password:
                logger.warning("vpnet: wrong password, rejecting")
                writer.write(_make_packet(_TYPE_CONNECT, 0x43))  # Forbidden
                await writer.drain()
                return False

        writer.write(_make_packet(_TYPE_CONNECT, _STATUS_OK))
        await writer.drain()
        logger.info("vpnet: handshake complete, entering ESC/VP21 pipe")
        return True

    @staticmethod
    async def _parse_extra_headers(
        reader: asyncio.StreamReader, count: int
    ) -> dict[int, tuple[int, bytes]]:
        """Read `count` extra headers and return {header_id: (attribute, 16-byte data)}."""
        result: dict[int, tuple[int, bytes]] = {}
        for _ in range(count):
            data = await reader.readexactly(_EXTRA_HEADER_SIZE)
            hdr_id = data[0]
            hdr_attr = data[1]
            hdr_data = data[2:18]
            result[hdr_id] = (hdr_attr, hdr_data)
        return result

    @staticmethod
    async def _skip_extra_headers(reader: asyncio.StreamReader, count: int) -> None:
        if count > 0:
            await reader.readexactly(count * _EXTRA_HEADER_SIZE)
