from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from client.base import AbstractProjectorClient, ClientNotConnectedError, StateCallback

logger = logging.getLogger(__name__)

_BACKOFF_SCHEDULE = [1, 2, 4, 8, 16, 30]  # seconds; last value is the cap


async def _read_until_colon(reader: asyncio.StreamReader) -> str:
    """Read bytes until ':' (the ESC/VP21 response terminator) and return decoded string."""
    data = bytearray()
    while True:
        byte = await reader.read(1)
        if not byte:
            raise asyncio.IncompleteReadError(bytes(data), None)
        data += byte
        if byte == b":":
            break
    return data.decode("utf-8", errors="replace")


class SerialClient(AbstractProjectorClient):
    """
    ESC/VP21 client over a raw TCP connection (serial-over-TCP).

    Commands are sent as ``CMD\\r``.  Responses are read until ``:``.
    Auto-reconnects on connection loss using exponential backoff.
    """

    def __init__(
        self,
        host: str,
        port: int,
        on_state_change: Optional[StateCallback] = None,
        connect_timeout: float = 5.0,
    ) -> None:
        super().__init__(on_state_change)
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._send_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # AbstractProjectorClient interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Connect to the projector. Starts auto-reconnect background task."""
        await self._do_connect()
        # Start the reconnect watcher if not already running
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def disconnect(self) -> None:
        """Close the connection and stop auto-reconnect."""
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
        """Send a command and return (response, duration_ms)."""
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
                logger.warning("serial: recv error: %s", exc)
                self._connected = False
                self._notify("reconnecting", 1, _BACKOFF_SCHEDULE[0])
                raise ClientNotConnectedError("Connection lost during receive") from exc
            duration_ms = (time.monotonic() - t0) * 1000
            return response, duration_ms

    @property
    def connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _do_connect(self) -> None:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._connect_timeout,
            )
            self._reader = reader
            self._writer = writer
            self._connected = True
            logger.info("serial: connected to %s:%s", self._host, self._port)
            self._notify("connected")
        except (OSError, asyncio.TimeoutError) as exc:
            self._connected = False
            logger.debug("serial: connect failed: %s", exc)
            raise

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
        """Background task: watch for disconnection and auto-reconnect."""
        # First, monitor for connection loss while connected
        while True:
            # Wait until we notice we've lost the connection
            while self._connected:
                await asyncio.sleep(0.5)
            # Connection is lost — notify and start backoff retries
            logger.info("serial: connection lost, starting reconnect")
            attempt = 0
            while not self._connected:
                idx = min(attempt, len(_BACKOFF_SCHEDULE) - 1)
                wait = _BACKOFF_SCHEDULE[idx]
                self._notify("reconnecting", attempt + 1, wait)
                logger.debug("serial: reconnect attempt %d, waiting %ds", attempt + 1, wait)
                await asyncio.sleep(wait)
                try:
                    await self._close_socket()
                    await self._do_connect()
                except Exception:
                    attempt += 1
