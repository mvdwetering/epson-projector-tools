from __future__ import annotations

from typing import Callable

from projector.model import ModelDef

# Observer type: called with (command_name, new_value) on state change
StateObserver = Callable[[str, str], None]
# Observer type: called with (transport_name, command_str, response_str) on each command
CommandObserver = Callable[[str, str, str], None]


class ProjectorState:
    def __init__(self, model: ModelDef) -> None:
        self._values: dict[str, str] = {
            name: defn.default for name, defn in model.commands.items()
        }
        valid_sources = model.non_cyclic_sources()
        if "SOURCE" in self._values and valid_sources:
            current = self._values.get("SOURCE", "")
            if current not in {src.code for src in valid_sources}:
                self._values["SOURCE"] = valid_sources[0].code
        self._state_observers: list[StateObserver] = []
        self._command_observers: list[CommandObserver] = []

    # ------------------------------------------------------------------
    # State access
    # ------------------------------------------------------------------

    def get(self, command: str) -> str | None:
        return self._values.get(command)

    def set(self, command: str, value: str) -> bool:
        """Store a new value. Returns False if the command is unknown."""
        if command not in self._values:
            return False
        self._values[command] = value
        for obs in self._state_observers:
            obs(command, value)
        return True

    def all_values(self) -> dict[str, str]:
        """Return a shallow copy of the current state."""
        return dict(self._values)

    # ------------------------------------------------------------------
    # Observer registration
    # ------------------------------------------------------------------

    def add_state_observer(self, obs: StateObserver) -> None:
        self._state_observers.append(obs)

    def add_command_observer(self, obs: CommandObserver) -> None:
        self._command_observers.append(obs)

    # ------------------------------------------------------------------
    # Command logging (called by transports after each command)
    # ------------------------------------------------------------------

    def log_command(self, transport: str, command: str, response: str) -> None:
        for obs in self._command_observers:
            obs(transport, command, response)
