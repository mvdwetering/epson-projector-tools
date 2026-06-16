from __future__ import annotations

import asyncio
import logging

from projector.model import ModelDef
from projector.state import ProjectorState
from transports.base import BaseTransport, handle_escvp21_stream
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from projector.power import PowerSequencer

logger = logging.getLogger(__name__)


class SerialTransport(BaseTransport):
    def __init__(
        self,
        state: ProjectorState,
        model: ModelDef,
        host: str = "0.0.0.0",
        port: int = 12345,
        power_sequencer: "PowerSequencer | None" = None,
    ) -> None:
        self._state = state
        self._model = model
        self._host = host
        self._port = port
        self._power_sequencer = power_sequencer
        self._server: asyncio.AbstractServer | None = None
        self._client_tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client, self._host, self._port
        )
        logger.info("Serial transport listening on %s:%s", self._host, self._port)
        try:
            await self._server.serve_forever()
        finally:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def stop(self) -> None:
        for task in list(self._client_tasks):
            task.cancel()
        if self._client_tasks:
            await asyncio.gather(*self._client_tasks, return_exceptions=True)
            self._client_tasks.clear()
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        task = asyncio.current_task()
        if task:
            self._client_tasks.add(task)
        try:
            await handle_escvp21_stream(reader, writer, self._state, self._model, "serial", power_sequencer=self._power_sequencer)
        finally:
            if task:
                self._client_tasks.discard(task)
