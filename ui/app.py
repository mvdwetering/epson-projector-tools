from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Header, RichLog
from textual.containers import Horizontal

from projector.engine import handle_command
from projector.model import ModelDef
from projector.state import ProjectorState

if TYPE_CHECKING:
    from transports.base import BaseTransport


class EmulatorApp(App[None]):
    """Interactive Epson projector emulator TUI."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #panels {
        height: 1fr;
    }
    #state-panel {
        width: 40;
        border: solid $primary;
        padding: 0 1;
    }
    #log-panel {
        width: 1fr;
        border: solid $secondary;
        padding: 0 1;
    }
    DataTable {
        height: 1fr;
    }
    RichLog {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("p", "toggle_power", "Toggle Power"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        state: ProjectorState,
        model: ModelDef,
        transports: list["BaseTransport"],
    ) -> None:
        super().__init__()
        self._state = state
        self._model = model
        self._transports = transports
        self._state_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        self._cmd_queue: asyncio.Queue[tuple[str, str, str]] = asyncio.Queue()

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="panels"):
            yield DataTable(id="state-table", show_cursor=False)
            yield RichLog(id="cmd-log", markup=True, max_lines=500)
        yield Footer()

    # ------------------------------------------------------------------
    # Mount: populate table, start transports and queue processors
    # ------------------------------------------------------------------

    async def on_mount(self) -> None:
        self.title = f"Epson Emulator — {self._model.name}"
        self._build_state_table()
        self._register_observers()

        for transport in self._transports:
            asyncio.create_task(transport.start())

        asyncio.create_task(self._process_state_updates())
        asyncio.create_task(self._process_command_updates())

    def _build_state_table(self) -> None:
        table: DataTable = self.query_one("#state-table", DataTable)
        table.add_column("Command", key="command", width=14)
        table.add_column("Value", key="value", width=20)
        for cmd, value in self._state.all_values().items():
            table.add_row(cmd, value, key=cmd)

    def _register_observers(self) -> None:
        self._state.add_state_observer(
            lambda cmd, val: self._state_queue.put_nowait((cmd, val))
        )
        self._state.add_command_observer(
            lambda transport, cmd, response: self._cmd_queue.put_nowait(
                (transport, cmd, response)
            )
        )

    # ------------------------------------------------------------------
    # Background queue processors
    # ------------------------------------------------------------------

    async def _process_state_updates(self) -> None:
        table: DataTable = self.query_one("#state-table", DataTable)
        while True:
            cmd, val = await self._state_queue.get()
            table.update_cell(cmd, "value", val)

    async def _process_command_updates(self) -> None:
        log: RichLog = self.query_one("#cmd-log", RichLog)
        while True:
            transport, cmd, response = await self._cmd_queue.get()
            ts = datetime.now().strftime("%H:%M:%S")
            display_cmd = cmd if cmd else "(null)"
            ok = "✓" if response != "ERR\r:" else "[red]✗[/red]"
            log.write(
                f"[dim]{ts}[/dim] [bold cyan]{transport:6}[/bold cyan] "
                f"{display_cmd!r:20} {ok}"
            )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_toggle_power(self) -> None:
        current = self._state.get("PWR")
        new_cmd = "PWR ON" if current != "01" else "PWR OFF"
        handle_command(self._state, self._model, new_cmd)
