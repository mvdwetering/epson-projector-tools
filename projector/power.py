from __future__ import annotations

import asyncio

from projector.model import ModelDef
from projector.state import ProjectorState

_TRANSITIONING = {"02", "03"}
_STANDBY = {"00", "04"}


class PowerSequencer:
    """Manages timed power-state transitions for the emulator.

    Protocol-level PWR ON / PWR OFF commands go through request_on() /
    request_off(), which schedule async transitions through the correct
    intermediate states.  The TUI keybinding writes state directly and
    calls cancel() first to abort any in-flight transition.
    """

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def is_transitioning(self) -> bool:
        return (self._task is not None and not self._task.done())

    def request_on(self, state: ProjectorState, model: ModelDef) -> bool:
        """Start power-on transition: standby → warmup → normal.

        Returns True if the transition was started, False if rejected.
        """
        current = state.get("PWR")
        if current not in _STANDBY:
            return False
        state.set("PWR", "02")
        self._task = asyncio.get_event_loop().create_task(
            self._finish_on(state, model.warmup_seconds)
        )
        return True

    def request_off(self, state: ProjectorState, model: ModelDef) -> bool:
        """Start power-off transition: normal → cooldown → standby.

        Returns True if the transition was started, False if rejected.
        """
        current = state.get("PWR")
        if current != "01":
            return False
        state.set("PWR", "03")
        self._task = asyncio.get_event_loop().create_task(
            self._finish_off(state, model.cooldown_seconds, model.standby_state)
        )
        return True

    def cancel(self) -> None:
        """Cancel any in-flight transition task. Safe to call when idle."""
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = None

    # ------------------------------------------------------------------
    # Internal coroutines
    # ------------------------------------------------------------------

    async def _finish_on(self, state: ProjectorState, delay: float) -> None:
        await asyncio.sleep(delay)
        state.set("PWR", "01")

    async def _finish_off(self, state: ProjectorState, delay: float, standby: str) -> None:
        await asyncio.sleep(delay)
        state.set("PWR", standby)
