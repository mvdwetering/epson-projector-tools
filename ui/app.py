from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Label, RichLog
from textual.containers import Horizontal, Vertical

from projector.engine import handle_command
from projector.model import ModelDef
from projector.state import ProjectorState

if TYPE_CHECKING:
    from transports.base import BaseTransport
    from transports.http import PasswordStore


@dataclass(frozen=True)
class EmulatorRuntimeConfig:
    serial_port: int
    vpnet_port: int
    http_port: int


class ChangePasswordScreen(ModalScreen["str | None"]):
    """Modal dialog for changing the HTTP Digest password at runtime."""

    DEFAULT_CSS = """
    ChangePasswordScreen {
        align: center middle;
    }
    #pw-dialog {
        width: 68;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #pw-dialog Label {
        margin-bottom: 1;
    }
    """

    def __init__(self, current_password: str) -> None:
        super().__init__()
        self._current_password = current_password

    def compose(self) -> ComposeResult:
        with Vertical(id="pw-dialog"):
            yield Label("Change HTTP Digest password (Enter to confirm, Esc to cancel):")
            yield Input(value=self._current_password, id="pw-input")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value or None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.stop()


class EmulatorApp(App[None]):
    """Interactive Epson projector emulator TUI."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #panels {
        height: 1fr;
    }
    #left-panel {
        width: 40;
        height: 1fr;
    }
    #state-table {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }
    #config-table {
        height: auto;
        border: solid $accent;
        padding: 0 1;
        margin-bottom: 1;
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
        Binding("a", "toggle_auth", "Toggle Auth"),
        Binding("w", "change_password", "Change Password"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        state: ProjectorState,
        model: ModelDef,
        transports: list["BaseTransport"],
        runtime_config: EmulatorRuntimeConfig,
        password_store: "PasswordStore | None" = None,
    ) -> None:
        super().__init__()
        self._state = state
        self._model = model
        self._transports = transports
        self._runtime_config = runtime_config
        self._password_store = password_store
        self._state_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        self._cmd_queue: asyncio.Queue[tuple[str, str, str]] = asyncio.Queue()

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="panels"):
            with Vertical(id="left-panel"):
                yield DataTable(id="config-table", show_cursor=False, show_header=False)
                yield DataTable(id="state-table", show_cursor=False)
            yield RichLog(id="cmd-log", markup=True, max_lines=500)
        yield Footer()

    # ------------------------------------------------------------------
    # Mount: populate table, start transports and queue processors
    # ------------------------------------------------------------------

    async def on_mount(self) -> None:
        self.title = f"Epson Emulator — {self._model.name}"
        self._build_state_table()
        self._build_config_table()
        self._register_observers()

        for transport in self._transports:
            asyncio.create_task(transport.start())

        asyncio.create_task(self._process_state_updates())
        asyncio.create_task(self._process_command_updates())

    def _build_state_table(self) -> None:
        table: DataTable = self.query_one("#state-table", DataTable)
        table.add_column("Command", key="command", width=11)
        table.add_column("Value", key="value", width=11)
        for cmd, value in self._state.all_values().items():
            table.add_row(cmd, value, key=cmd)

    def _build_config_table(self) -> None:
        table: DataTable = self.query_one("#config-table", DataTable)
        table.add_column("", key="line", width=32)
        auth_required = bool(self._password_store and self._password_store.enabled)
        vpnet_auth_icon = "🔒" if auth_required else "🔓"
        http_auth_icon = "🔒" if auth_required else "🔓"

        def cfg_line(name: str, port: int, icon: str | None = None) -> str:
            base = f"{name:<10} {port:>5}"
            return f"{base} {icon}" if icon else base

        table.add_row(
            cfg_line("Serial TCP", self._runtime_config.serial_port),
            key="serial",
        )
        table.add_row(
            cfg_line("ESC/VP.net", self._runtime_config.vpnet_port, vpnet_auth_icon),
            key="vpnet",
        )
        table.add_row(
            cfg_line("HTTP", self._runtime_config.http_port, http_auth_icon),
            key="http",
        )

    def _refresh_config_table_auth_icons(self) -> None:
        table: DataTable = self.query_one("#config-table", DataTable)
        auth_required = bool(self._password_store and self._password_store.enabled)
        vpnet_auth_icon = "🔒" if auth_required else "🔓"
        http_auth_icon = "🔒" if auth_required else "🔓"
        table.update_cell(
            "vpnet",
            "line",
            f"{'ESC/VP.net':<10} {self._runtime_config.vpnet_port:>5} {vpnet_auth_icon}",
        )
        table.update_cell(
            "http",
            "line",
            f"{'HTTP':<10} {self._runtime_config.http_port:>5} {http_auth_icon}",
        )

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
            now = datetime.now()
            ts = now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"
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

    def action_toggle_auth(self) -> None:
        if self._password_store is None:
            return
        self._password_store.enabled = not self._password_store.enabled
        self._refresh_config_table_auth_icons()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in {"change_password", "toggle_auth"} and self._password_store is None:
            return None
        return True

    def action_change_password(self) -> None:
        if self._password_store is None:
            return
        store = self._password_store

        def on_dismiss(new_password: str | None) -> None:
            if new_password:
                store.password = new_password

        self.push_screen(ChangePasswordScreen(store.password), on_dismiss)
