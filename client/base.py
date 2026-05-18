from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional


class ClientNotConnectedError(Exception):
    """Raised when send() is called on a client that is not connected."""


# State callback type: (state, attempt, next_retry_s) -> None
# state is one of "connected", "disconnected", "reconnecting"
StateCallback = Callable[[str, int, int], None]


class AbstractProjectorClient(ABC):
    """Abstract async client for ESC/VP21 projector communication."""

    def __init__(self, on_state_change: Optional[StateCallback] = None) -> None:
        self._on_state_change: Optional[StateCallback] = on_state_change

    def _notify(self, state: str, attempt: int = 0, next_retry_s: int = 0) -> None:
        if self._on_state_change:
            self._on_state_change(state, attempt, next_retry_s)

    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection to the projector."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection."""

    @abstractmethod
    async def send(self, cmd: str) -> tuple[str, float]:
        """
        Send a single ESC/VP21 command string and return (response, duration_ms).

        The response is always ESC/VP21 formatted regardless of underlying protocol:
          - GET success: "CMD=value\\r:"
          - SET / null:  "\\r:"
          - Error:       "ERR\\r:"

        Raises ClientNotConnectedError if not connected.
        """

    @property
    @abstractmethod
    def connected(self) -> bool:
        """True if the client currently has an active connection."""
