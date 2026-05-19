from __future__ import annotations

import asyncio
import logging
import struct
import time
from typing import Optional

from client.base import AbstractProjectorClient, ClientNotConnectedError, StateCallback
from client.serial import SerialClient, _read_until_colon, _BACKOFF_SCHEDULE

logger = logging.getLogger(__name__)

# ESC/VP.net protocol constants (must match transports/vpnet.py)
_MAGIC = b"ESC/VP.net"
_VERSION = 0x10
_TYPE_HELLO = 0x01
_TYPE_CONNECT = 0x03
_STATUS_OK = 0x20
_HEADER_SIZE = 16  # 10 (magic) + 1 (ver) + 1 (type) + 2 (reserved) + 1 (status) + 1 (num_headers)


def _make_packet(pkt_type: int) -> bytes:
    return _MAGIC + struct.pack("BBHBb", _VERSION, pkt_type, 0, 0x00, 0)


class VpnetClient(AbstractProjectorClient):
    """
    ESC/VP21 client over the ESC/VP.net binary protocol (port 3629).

    Performs the HELLO/CONNECT handshake then enters the raw ESC/VP21 pipe,
    identical to SerialClient after handshake.  Auto-reconnects (redo handshake)
    on connection loss.
    """

    def __init__(
        self,
        host: str,
        port: int = 3629,
        on_state_change: Optional[StateCallback] = None,
        connect_timeout: float = 5.0,
        password: str = "",
    ) -> None:
        super().__init__(on_state_change)
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout
        self._password = password
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._send_lock = asyncio.Lock()

    async def connect(self) -> None:
        await self._do_connect()
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def disconnect(self) -> None:
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None
        await self._close_socket()
        self._connected = False
        self._notify("disconnected")

    async def send(self, cmd: str) -> tuple[str, float]:
        if not self._connected:
            raise ClientNotConnectedError("Not connected to projector")
        async with self._send_lock:
            if not self._connected:
                raise ClientNotConnectedError("Not connected to projector")
            assert self._writer is not None
            assert self._reader is not None
            payload = (cmd.strip() + "\r").encode("utf-8")
            t0 = time.monotonic()
            self._writer.write(payload)
            await self._writer.drain()
            try:
                response = await asyncio.wait_for(
                    _read_until_colon(self._reader), timeout=10.0
                )
            except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionResetError, OSError) as exc:
                logger.warning("vpnet: recv error: %s", exc)
                self._connected = False
                self._notify("reconnecting", 1, _BACKOFF_SCHEDULE[0])
                raise ClientNotConnectedError("Connection lost during receive") from exc
            duration_ms = (time.monotonic() - t0) * 1000
            return response, duration_ms

    @property
    def connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------

    async def _do_connect(self) -> None:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._connect_timeout,
            )
        except (OSError, asyncio.TimeoutError) as exc:
            self._connected = False
            logger.debug("vpnet: connect failed: %s", exc)
            raise

        try:
            await asyncio.wait_for(self._handshake(reader, writer), timeout=self._connect_timeout)
        except Exception as exc:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            self._connected = False
            logger.debug("vpnet: handshake failed: %s", exc)
            raise ConnectionError(f"ESC/VP.net handshake failed: {exc}") from exc

        self._reader = reader
        self._writer = writer
        self._connected = True
        logger.info("vpnet: connected to %s:%s", self._host, self._port)
        self._notify("connected")

    async def _handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        # Send HELLO
        writer.write(_make_packet(_TYPE_HELLO))
        await writer.drain()
        # Read HELLO response
        hello_resp = await reader.readexactly(_HEADER_SIZE)
        if hello_resp[:10] != _MAGIC or hello_resp[14] != _STATUS_OK:
            raise ConnectionError("HELLO response not OK")
        # Send CONNECT (with password header if configured)
        writer.write(self._make_connect_packet())
        await writer.drain()
        # Read CONNECT response
        connect_resp = await reader.readexactly(_HEADER_SIZE)
        if connect_resp[:10] != _MAGIC:
            raise ConnectionError("CONNECT response invalid")
        status = connect_resp[14]
        if status == 0x41:
            raise ConnectionError("Projector requires a password")
        if status == 0x43:
            raise ConnectionError("Wrong ESC/VP.net password")
        if status != _STATUS_OK:
            raise ConnectionError(f"CONNECT failed (status 0x{status:02x})")

    def _make_connect_packet(self) -> bytes:
        """Build a CONNECT packet, including a Password header when password is set."""
        if not self._password:
            return _make_packet(_TYPE_CONNECT)
        pw_bytes = self._password.encode("ascii")[:16].ljust(16, b"\x00")
        base = _MAGIC + struct.pack("BBHBb", _VERSION, _TYPE_CONNECT, 0, 0x00, 1)
        extra = bytes([0x01, 0x01]) + pw_bytes  # id=Password, attr=Plain, 16 bytes
        return base + extra

    async def _close_socket(self) -> None:
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None

    async def _reconnect_loop(self) -> None:
        while True:
            while self._connected:
                await asyncio.sleep(0.5)
            logger.info("vpnet: connection lost, starting reconnect")
            attempt = 0
            while not self._connected:
                idx = min(attempt, len(_BACKOFF_SCHEDULE) - 1)
                wait = _BACKOFF_SCHEDULE[idx]
                self._notify("reconnecting", attempt + 1, wait)
                logger.debug("vpnet: reconnect attempt %d, waiting %ds", attempt + 1, wait)
                await asyncio.sleep(wait)
                try:
                    await self._close_socket()
                    await self._do_connect()
                except Exception:
                    attempt += 1
