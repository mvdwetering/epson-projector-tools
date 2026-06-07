from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

from projector.engine import handle_command
from projector.model import ModelDef
from projector.state import ProjectorState

logger = logging.getLogger(__name__)


class BaseTransport(ABC):
    @abstractmethod
    async def start(self) -> None:
        """Start the transport server. Runs indefinitely."""


async def read_until_cr(
    reader: asyncio.StreamReader,
    read_timeout: float | None = None,
) -> bytes:
    """Read bytes from reader until \\r is encountered (delimiter consumed, not returned)."""
    data = bytearray()
    while True:
        if read_timeout is None:
            byte = await reader.read(1)
        else:
            byte = await asyncio.wait_for(reader.read(1), timeout=read_timeout)
        if not byte:
            raise asyncio.IncompleteReadError(bytes(data), None)
        if byte == b"\r":
            break
        data += byte
    return bytes(data)


async def handle_escvp21_stream(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    state: ProjectorState,
    model: ModelDef,
    transport_name: str,
    read_timeout: float | None = None,
) -> None:
    """
    ESC/VP21 command loop shared by serial and ESC/VP.net transports.
    Reads \\r-terminated commands, calls the engine, writes responses.
    """
    peer = writer.get_extra_info("peername", ("?", 0))
    logger.info("%s: client connected from %s:%s", transport_name, peer[0], peer[1])
    try:
        while True:
            try:
                raw = await read_until_cr(reader, read_timeout=read_timeout)
            except asyncio.IncompleteReadError:
                break
            except asyncio.TimeoutError:
                logger.info("%s: idle timeout reached, closing client session", transport_name)
                state.log_command(
                    transport_name,
                    "connection closed by emulator (inactivity timeout)",
                    "IDLE_TIMEOUT",
                )
                break
            except ConnectionResetError:
                break

            cmd_str = raw.decode("utf-8", errors="replace")
            response = handle_command(state, model, cmd_str)
            writer.write(response.encode("utf-8"))
            await writer.drain()
            state.log_command(transport_name, cmd_str, response)
    finally:
        logger.info("%s: client disconnected %s:%s", transport_name, peer[0], peer[1])
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
