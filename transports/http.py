from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import secrets

from aiohttp import web

from projector.engine import handle_command
from projector.model import ModelDef
from projector.state import ProjectorState
from transports.base import BaseTransport
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from projector.power import PowerSequencer

logger = logging.getLogger(__name__)


class PasswordStore:
    """Mutable container for the HTTP Digest authentication password."""

    def __init__(self, password: str, enabled: bool = True) -> None:
        self.password = password
        self.enabled = enabled


def _make_digest_middleware(store: PasswordStore):
    """Return an aiohttp middleware that enforces HTTP Digest authentication.

    Protocol parameters match real Epson projectors (captured from device):
      realm  = "Web Control"
      username expected from client = "EPSONWEB"
      algorithm = MD5 (field omitted in WWW-Authenticate, which is the RFC 2617
                  default; the real projector also omits it)
      qop    = "auth"

    Nonce note: real projectors emit a structured nonce of the form
      "<6-hex>:<md5-hash>"  e.g. "29a493:ab6e88cb8c835a1cd6214a1b83e754a4"
    The emulator uses a flat secrets.token_hex(16) instead.  Both are opaque
    strings per RFC 2617; the client echoes back whatever nonce the server sent.
    """
    _REALM = "Web Control"
    _md5 = lambda s: hashlib.md5(s.encode()).hexdigest()  # noqa: E731
    # Mutable cell so the inner function can replace the nonce after each 401.
    state = {"nonce": secrets.token_hex(16)}

    @web.middleware
    async def digest_auth(request: web.Request, handler):
        if not store.enabled:
            return await handler(request)

        # Recompute ha1 per-request so runtime password changes take effect immediately.
        ha1 = _md5(f"EPSONWEB:{_REALM}:{store.password}")
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Digest "):
            # Parse key="quoted" or key=unquoted fields from the Digest header.
            fields: dict[str, str] = {}
            for m in re.finditer(r'(\w+)=(?:"([^"]*)"|([\w:./=-]+))', auth_header):
                fields[m.group(1)] = m.group(2) if m.group(2) is not None else (m.group(3) or "")
            nonce   = fields.get("nonce", "")
            nc      = fields.get("nc", "")
            cnonce  = fields.get("cnonce", "")
            response = fields.get("response", "")
            ha2 = _md5(f"{request.method}:{request.path_qs}")
            expected = _md5(f"{ha1}:{nonce}:{nc}:{cnonce}:auth:{ha2}")
            if expected == response:
                return await handler(request)
        # Challenge: issue new random nonce so each 401 has a fresh nonce.
        state["nonce"] = secrets.token_hex(16)
        raise web.HTTPUnauthorized(
            headers={
                "WWW-Authenticate": (
                    f'Digest realm="{_REALM}", '
                    f'nonce="{state["nonce"]}", '
                    f'qop="auth"'
                )
            }
        )

    return digest_auth


class HttpTransport(BaseTransport):
    def __init__(
        self,
        state: ProjectorState,
        model: ModelDef,
        host: str = "0.0.0.0",
        port: int = 8080,
        password: PasswordStore | None = None,
        power_sequencer: "PowerSequencer | None" = None,
    ) -> None:
        self._state = state
        self._model = model
        self._host = host
        self._port = port
        self._password = password
        self._power_sequencer = power_sequencer
        self._runner: web.AppRunner | None = None

    async def start(self) -> None:
        middlewares = [_make_digest_middleware(self._password)] if self._password else []
        app = web.Application(middlewares=middlewares)
        app.router.add_get("/cgi-bin/json_query", self._handle_json_query)
        app.router.add_get("/cgi-bin/directsend", self._handle_directsend)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self._host, self._port)
        await site.start()
        logger.info("HTTP transport listening on %s:%s", self._host, self._port)
        try:
            await asyncio.get_event_loop().create_future()
        finally:
            if self._runner is not None:
                await self._runner.cleanup()
                self._runner = None

    async def stop(self) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None

    # ------------------------------------------------------------------
    # /cgi-bin/json_query?jsoncallback=CMD?
    # ------------------------------------------------------------------

    async def _handle_json_query(self, request: web.Request) -> web.Response:
        cmd_str = request.rel_url.query.get("jsoncallback")
        if not cmd_str:
            raise web.HTTPBadRequest(reason="Missing jsoncallback parameter")
        response = handle_command(self._state, self._model, cmd_str, self._power_sequencer)
        self._state.log_command("http", cmd_str, response)
        reply, is_error = self._parse_json_query_response(response)
        return web.json_response(self._build_json_query_payload(cmd_str, reply, is_error))

    # ------------------------------------------------------------------
    # /cgi-bin/directsend?CMD=VALUE  or  /cgi-bin/directsend?KEY=ir_code
    # ------------------------------------------------------------------

    async def _handle_directsend(self, request: web.Request) -> web.Response:
        params = list(request.rel_url.query.items())
        if not params:
            # null command → connectivity/auth probe; surface as success with no state change
            return web.Response(status=200)
        cmd, value = params[0]
        cmd_str = f"{cmd} {value}"
        response = handle_command(self._state, self._model, cmd_str, self._power_sequencer)
        self._state.log_command("http", cmd_str, response)
        if response.startswith("ERR"):
            raise web.HTTPBadRequest(reason=f"Command failed: {cmd_str}")
        return web.Response(status=200)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_json_query_payload(cmd_str: str, reply: str, is_error: bool) -> dict:
        """Build Epson-compatible json_query payload with stable feature fields."""
        return {
            "projector": {
                "feature": {
                    "name": "esc/vp21",
                    "query": cmd_str,
                    "reply": reply,
                    "error": is_error,
                }
            }
        }

    @staticmethod
    def _parse_json_query_response(response: str) -> tuple[str, bool]:
        """Parse engine response into json_query reply value and error flag."""
        if response.startswith("ERR"):
            return "ERR", True
        if "=" in response:
            return response.split("=", 1)[1].rstrip("\r:"), False
        return "ERR", True
