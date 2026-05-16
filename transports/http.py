from __future__ import annotations

import asyncio
import logging

from aiohttp import web

from projector.model import ModelDef
from projector.state import ProjectorState
from transports.base import BaseTransport

logger = logging.getLogger(__name__)


class HttpTransport(BaseTransport):
    def __init__(
        self,
        state: ProjectorState,
        model: ModelDef,
        host: str = "0.0.0.0",
        port: int = 8080,
    ) -> None:
        self._state = state
        self._model = model
        self._host = host
        self._port = port

    async def start(self) -> None:
        app = web.Application()
        app.router.add_route("*", "/{path_info:.*}", self._handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self._host, self._port)
        await site.start()
        logger.info("HTTP transport listening on %s:%s", self._host, self._port)
        # Keep running until cancelled
        await asyncio.get_event_loop().create_future()

    async def _handle(self, request: web.Request) -> web.Response:
        return web.Response(text="HTTP transport not yet implemented\n")
