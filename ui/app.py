from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Label, RichLog
from textual.containers import Horizontal, Vertical

from projector.model import ModelDef
from projector.state import ProjectorState

if TYPE_CHECKING:
    from transports.base import BaseTransport
    from transports.http import PasswordStore
    from projector.power import PowerSequencer


@dataclass(frozen=True)
class EmulatorRuntimeConfig:
    host: str
    serial_port: int
    vpnet_port: int
    http_port: int
    models_dir: Path


class ModelSelectScreen(ModalScreen[Path | None]):
    """Modal dialog for selecting a JSON model file."""

    DEFAULT_CSS = """
    ModelSelectScreen {
        align: center middle;
    }
    #model-dialog {
        width: 72;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #model-table {
        height: 12;
        margin-top: 1;
    }
    """

    def __init__(self, model_paths: Iterable[Path]) -> None:
        super().__init__()
        self._model_paths = list(model_paths)

    def _selected_model_path(self) -> Path | None:
        if not self._model_paths:
            return None
        table = self.query_one("#model-table", DataTable)
        coordinate = table.cursor_coordinate
        row_index = coordinate.row if hasattr(coordinate, "row") else int(coordinate[0])
        if row_index < 0 or row_index >= len(self._model_paths):
            return None
        return self._model_paths[row_index]

    def compose(self) -> ComposeResult:
        with Vertical(id="model-dialog"):
            yield Label("Select model (Enter to apply, Esc to cancel):")
            yield DataTable(id="model-table", show_header=False, show_cursor=True)

    def on_mount(self) -> None:
        table = self.query_one("#model-table", DataTable)
        table.add_column("Model", key="name", width=60)
        for model_path in self._model_paths:
            table.add_row(model_path.name, key=str(model_path))
        if self._model_paths:
            table.cursor_coordinate = Coordinate(0, 0)
            table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = str(event.row_key.value)
        if row_key:
            self.dismiss(Path(row_key))

    def on_key(self, event) -> None:
        if event.key == "enter":
            selected = self._selected_model_path()
            if selected is not None:
                self.dismiss(selected)
                event.stop()
            return
        if event.key == "escape":
            self.dismiss(None)
            event.stop()


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
        width: 48;
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
        Binding("m", "change_model", "Change Model", priority=True),
        Binding("a", "toggle_auth", "Toggle Auth"),
        Binding("w", "change_password", "Change Password"),
        Binding("q", "app.quit", "Quit", priority=True),
    ]

    def __init__(
        self,
        state: ProjectorState,
        model: ModelDef,
        transports: list["BaseTransport"] | None,
        runtime_config: EmulatorRuntimeConfig,
        password_store: "PasswordStore | None" = None,
        power_sequencer: "PowerSequencer | None" = None,
    ) -> None:
        super().__init__()
        self._state = state
        self._model = model
        self._transports = transports or []
        self._auto_create_transports = transports is None
        self._transport_tasks: list[asyncio.Task] = []
        self._runtime_config = runtime_config
        self._password_store = password_store
        self._power_sequencer = power_sequencer
        self._state_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        self._cmd_queue: asyncio.Queue[tuple[str, str, str]] = asyncio.Queue()
        self._recent_commands: list[str] = []
        self._background_tasks: list[asyncio.Task] = []

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
        self._set_title()
        self._build_state_table()
        self._build_config_table()
        self._register_observers()

        await self._start_transports()

        self._background_tasks = [
            asyncio.create_task(self._process_state_updates()),
            asyncio.create_task(self._process_command_updates()),
        ]

    async def on_unmount(self) -> None:
        if self._background_tasks:
            for task in self._background_tasks:
                task.cancel()
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks = []
        await self._stop_transports()

    def _set_title(self) -> None:
        display_name = self._model.file_name or self._model.name
        self.title = f"Epson Emulator — {display_name}"

    async def _start_transports(self) -> None:
        if self._auto_create_transports and not self._transports:
            self._transports = self._make_transports()
        self._transport_tasks = [
            asyncio.create_task(transport.start()) for transport in self._transports
        ]

    async def _stop_transports(self) -> None:
        if not self._transport_tasks:
            return
        for transport in self._transports:
            await transport.stop()
        for task in self._transport_tasks:
            task.cancel()
        await asyncio.gather(*self._transport_tasks, return_exceptions=True)
        self._transport_tasks = []

    def _make_transports(self) -> list[BaseTransport]:
        from transports.http import HttpTransport
        from transports.serial import SerialTransport
        from transports.vpnet import VpnetTransport

        return [
            SerialTransport(
                self._state,
                self._model,
                host=self._runtime_config.host,
                port=self._runtime_config.serial_port,
                power_sequencer=self._power_sequencer,
            ),
            VpnetTransport(
                self._state,
                self._model,
                host=self._runtime_config.host,
                port=self._runtime_config.vpnet_port,
                password_store=self._password_store,
                power_sequencer=self._power_sequencer,
            ),
            HttpTransport(
                self._state,
                self._model,
                host=self._runtime_config.host,
                port=self._runtime_config.http_port,
                password=self._password_store,
                power_sequencer=self._power_sequencer,
            ),
        ]

    def _build_state_table(self) -> None:
        table: DataTable = self.query_one("#state-table", DataTable)
        if table.columns:
            table.clear(columns=True)
        table.add_column("Command", key="command", width=11)
        table.add_column("Value", key="value", width=11)
        values = self._state.all_values()
        for cmd in self._ordered_commands(values):
            table.add_row(cmd, self._display_state_value(cmd, values[cmd]), key=cmd)

    def _display_state_value(self, cmd: str, value: str) -> str:
        cmd_def = self._model.commands.get(cmd)
        if cmd_def is None:
            return value
        if cmd_def.decimal_single_param and value.isdigit():
            try:
                return str(int(value, 10))
            except ValueError:
                return value
        return value

    @staticmethod
    def _extract_command_name(command_line: str) -> str | None:
        line = command_line.strip().upper()
        if not line:
            return None
        get_match = re.match(r"^([A-Z0-9]+)\?$", line)
        if get_match:
            return get_match.group(1)
        set_match = re.match(r"^([A-Z0-9]+) ", line)
        if set_match:
            return set_match.group(1)
        return None

    def _ordered_commands(self, values: dict[str, str]) -> list[str]:
        pinned_order = ["PWR", "SOURCE", "SNO", "LAMP", "KEY"]
        pinned = [cmd for cmd in pinned_order if cmd in values]
        recent = [cmd for cmd in self._recent_commands if cmd in values and cmd not in pinned]
        remainder = sorted(cmd for cmd in values if cmd not in pinned and cmd not in recent)
        return pinned + recent[:6] + remainder

    def _mark_command_recent(self, cmd: str) -> None:
        if cmd in {"PWR", "SOURCE", "SNO", "LAMP", "KEY"}:
            return
        if cmd in self._recent_commands:
            self._recent_commands.remove(cmd)
        self._recent_commands.insert(0, cmd)
        self._recent_commands = self._recent_commands[:6]

    def _build_config_table(self) -> None:
        table: DataTable = self.query_one("#config-table", DataTable)
        if table.columns:
            table.clear(columns=True)
        table.add_column("", key="line", width=42)
        auth_required = bool(self._password_store and self._password_store.enabled)
        vpnet_auth_icon = "🔒" if auth_required else "🔓"
        http_auth_icon = "🔒" if auth_required else "🔓"

        def cfg_line(name: str, port: int, icon: str | None = None) -> str:
            base = f"{name:<10} {port:>5}"
            suffix = " !" if (
                (name == "Serial TCP" and not self._model.serial_supported())
                or (name in {"ESC/VP.net", "HTTP"} and not self._model.network_supported())
            ) else ""
            return f"{base} {icon}{suffix}" if icon else f"{base}{suffix}"

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
            (
                f"{'ESC/VP.net':<10} {self._runtime_config.vpnet_port:>5} {vpnet_auth_icon}"
                f"{' !' if not self._model.network_supported() else ''}"
            ),
        )
        table.update_cell(
            "http",
            "line",
            (
                f"{'HTTP':<10} {self._runtime_config.http_port:>5} {http_auth_icon}"
                f"{' !' if not self._model.network_supported() else ''}"
            ),
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
        while True:
            await self._state_queue.get()
            self._build_state_table()

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
            cmd_name = self._extract_command_name(cmd)
            if cmd_name:
                self._mark_command_recent(cmd_name)
                self._build_state_table()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_toggle_power(self) -> None:
        if self._power_sequencer is not None:
            self._power_sequencer.cancel()
        current = self._state.get("PWR") or "01"
        # Cycle: 00/04 → 02 → 01 → 03 → 00/04
        _cycle: dict[str, str] = {
            "00": "02",
            "04": "02",
            "02": "01",
            "01": "03",
            "03": self._model.standby_state,
        }
        next_state = _cycle.get(current, "02")
        self._state.set("PWR", next_state)

    def action_toggle_auth(self) -> None:
        if self._password_store is None:
            return
        self._password_store.enabled = not self._password_store.enabled
        self._refresh_config_table_auth_icons()

    def action_change_model(self) -> None:
        models = sorted(self._runtime_config.models_dir.glob("*.json"))
        if not models:
            return

        def on_dismiss(selected: Path | None) -> None:
            if selected is None:
                return
            asyncio.create_task(self._switch_model(selected))

        self.push_screen(ModelSelectScreen(models), on_dismiss)

    def action_quit(self) -> None:
        self.exit()

    async def _switch_model(self, model_path: Path) -> None:
        from projector.model import load_model
        from projector.state import ProjectorState

        await self._stop_transports()
        if self._power_sequencer is not None:
            self._power_sequencer.cancel()

        self._model = load_model(model_path)
        self._state = ProjectorState(self._model)
        self._recent_commands = []
        self._register_observers()
        self._set_title()
        self._build_state_table()
        self._build_config_table()

        self._transports = self._make_transports() if self._auto_create_transports else []
        await self._start_transports()

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
