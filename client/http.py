from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Optional

import aiohttp

from client.base import AbstractProjectorClient, ClientNotConnectedError, StateCallback

logger = logging.getLogger(__name__)


class HttpClient(AbstractProjectorClient):
    """
    ESC/VP21 client over the Epson HTTP/CGI interface.

    GET commands (ending in ``?``) are routed to ``/cgi-bin/json_query``.
    SET commands are routed to ``/cgi-bin/directsend``.

    Digest authentication is handled by ``aiohttp.DigestAuthMiddleware``
    when a password is provided.

    The ``connected`` property always returns ``True`` because HTTP is stateless.

    The response from ``send()`` is always ESC/VP21 formatted:
      - ``CMD=value\\r:``  for successful GETs
      - ``\\r:``           for successful SETs
      - ``ERR\\r:``        on error
    """

    def __init__(
        self,
        host: str,
        port: int = 80,
        password: str = "",
        on_state_change: Optional[StateCallback] = None,
    ) -> None:
        super().__init__(on_state_change)
        self._host = host
        self._port = port
        self._password = password
        self._session: Optional[aiohttp.ClientSession] = None

    def _base_url(self) -> str:
        if self._port == 80:
            return f"http://{self._host}"
        return f"http://{self._host}:{self._port}"

    def _referer(self) -> str:
        return f"{self._base_url()}/cgi-bin/webconf"

    def _headers(self) -> dict[str, str]:
        return {"Referer": self._referer()}

    async def connect(self) -> None:
        """Probe host:port reachability, then create the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
        # Verify the TCP port is open before reporting connected.
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
        except (OSError, asyncio.TimeoutError) as exc:
            raise ConnectionError(
                f"Cannot reach {self._host}:{self._port}: {exc}"
            ) from exc
        middlewares = []
        if self._password:
            middlewares.append(
                aiohttp.DigestAuthMiddleware(login="EPSONWEB", password=self._password)
            )
        self._session = aiohttp.ClientSession(middlewares=middlewares)
        self._notify("connected")

    async def disconnect(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
        self._notify("disconnected")

    async def send(self, cmd: str) -> tuple[str, float]:
        """Send an ESC/VP21 command via HTTP and return (response, duration_ms)."""
        if self._session is None or self._session.closed:
            raise ClientNotConnectedError("HTTP session not open; call connect() first")

        cmd = cmd.strip()
        base = self._base_url()
        ts = int(time.time() * 1000)
        t0 = time.monotonic()

        if cmd.endswith("?"):
            # GET command -> json_query endpoint
            url = f"{base}/cgi-bin/json_query"
            params = {"jsoncallback": cmd, "_": ts}
            try:
                async with self._session.get(url, params=params, headers=self._headers()) as resp:
                    duration_ms = (time.monotonic() - t0) * 1000
                    if resp.status != 200:
                        logger.warning("http: GET %s returned %s", url, resp.status)
                        return "ERR\r:", duration_ms
                    data = await resp.json(content_type=None)
            except aiohttp.ClientError as exc:
                duration_ms = (time.monotonic() - t0) * 1000
                logger.warning("http: request error: %s", exc)
                return "ERR\r:", duration_ms

            return self._parse_json_response(cmd[:-1], data), duration_ms

        else:
            # SET command -> directsend endpoint
            parts = cmd.split(" ", 1)
            if len(parts) != 2:
                return "ERR\r:", (time.monotonic() - t0) * 1000
            cmd_name, cmd_value = parts
            url = f"{base}/cgi-bin/directsend"
            params = {cmd_name: cmd_value, "_": ts}
            try:
                async with self._session.get(url, params=params, headers=self._headers()) as resp:
                    duration_ms = (time.monotonic() - t0) * 1000
                    if resp.status != 200:
                        logger.warning("http: directsend %s returned %s", url, resp.status)
                        return "ERR\r:", duration_ms
                    return "\r:", duration_ms
            except aiohttp.ClientError as exc:
                duration_ms = (time.monotonic() - t0) * 1000
                logger.warning("http: request error: %s", exc)
                return "ERR\r:", duration_ms

    @property
    def connected(self) -> bool:
        """HTTP is stateless -- always report as connected."""
        return True

    @staticmethod
    def _parse_json_response(cmd_name: str, data: dict) -> str:
        """Convert Epson JSON query response to ESC/VP21 format."""
        try:
            feature = data["projector"]["feature"]
            reply = feature.get("reply", "")
            error = feature.get("error", False)
        except (KeyError, TypeError):
            return "ERR\r:"
        if error or reply == "ERR":
            return "ERR\r:"
        return f"{cmd_name}={reply}\r:"
