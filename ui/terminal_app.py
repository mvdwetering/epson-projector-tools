from __future__ import annotations

import asyncio
import re
from datetime import datetime
from io import TextIOWrapper
from typing import IO, Optional

from platformdirs import user_config_dir
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    TextArea,
)
from textual.reactive import reactive

from client.base import AbstractProjectorClient, ClientNotConnectedError
from client.serial import SerialClient
from client.vpnet import VpnetClient
from client.http import HttpClient
from client.presets import load_presets, save_preset, delete_preset

_DEFAULT_PORTS: dict[str, int] = {"serial": 12345, "vpnet": 3629, "http": 80}
_DEFAULT_QUICK_CMDS = ["SNO?", "PWR?", "PWR ON", "PWR OFF", "SOURCE?"]

_PROTOCOL_LABELS = [
    ("Serial TCP", "serial"),
    ("ESC/VP.net", "vpnet"),
    ("HTTP", "http"),
]


# ---------------------------------------------------------------------------
# Confirm dialog
# ---------------------------------------------------------------------------

class ConfirmDialog(ModalScreen[bool]):
    """Simple yes/no confirmation modal."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }
    #confirm-panel {
        width: 50;
        height: auto;
        border: solid $warning;
        background: $surface;
        padding: 1 2;
    }
    #confirm-buttons {
        margin-top: 1;
        height: auto;
        align: right middle;
    }
    #confirm-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-panel"):
            yield Label(self._message, markup=True)
            with Horizontal(id="confirm-buttons"):
                yield Button("Cancel", variant="default", id="btn-no")
                yield Button("Delete", variant="error", id="btn-yes")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-yes")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)
            event.stop()
        elif event.key == "y":
            self.dismiss(True)
            event.stop()


# ---------------------------------------------------------------------------
# Preset list screen
# ---------------------------------------------------------------------------

class PresetListScreen(Screen["dict | None"]):
    """Main entry screen showing saved presets."""

    DEFAULT_CSS = """
    PresetListScreen {
        align: center middle;
    }
    #preset-panel {
        width: 72;
        height: auto;
        max-height: 80vh;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #preset-list {
        height: auto;
        max-height: 20;
        margin-bottom: 1;
    }
    #empty-label {
        color: $text-muted;
        margin: 1 0;
    }
    #preset-hint {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("n", "new_preset", "New", show=True),
        Binding("e", "edit_preset", "Edit", show=True),
        Binding("d", "delete_preset", "Delete", show=True),
        Binding("ctrl+q", "app.quit", "Quit", show=True),
        Binding("q", "app.quit", "Quit", show=False),
    ]

    def __init__(self, initial_preset_name: Optional[str] = None) -> None:
        super().__init__()
        self._initial_preset_name = initial_preset_name

    def compose(self) -> ComposeResult:
        with Vertical(id="preset-panel"):
            yield Label("[bold]Saved Presets[/bold]", markup=True)
            yield Label(
                "No presets saved yet. Press [bold]n[/bold] to add one.",
                id="empty-label",
                markup=True,
            )
            yield ListView(id="preset-list")
            yield Label(
                "[dim]Enter: connect  n: new  e: edit  d: delete  q: quit[/dim]",
                id="preset-hint",
                markup=True,
            )

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        presets = load_presets()
        lv = self.query_one("#preset-list", ListView)
        empty_label = self.query_one("#empty-label", Label)
        lv.remove_children()
        if presets:
            empty_label.display = False
            lv.display = True
            for p in presets:
                name = p.get("name", "?")
                proto = p.get("protocol", "?")
                host = p.get("host", "?")
                port = p.get("port", "?")
                item = ListItem(
                    Label(f"[bold]{name}[/bold]  {proto}  {host}:{port}", markup=True)
                )
                item._preset = p  # type: ignore[attr-defined]
                lv.append(item)
            if self._initial_preset_name:
                for idx, child in enumerate(lv._nodes):
                    if getattr(child, "_preset", {}).get("name") == self._initial_preset_name:
                        lv.index = idx
                        break
        else:
            empty_label.display = True
            lv.display = False

    def _selected_preset(self) -> Optional[dict]:
        lv = self.query_one("#preset-list", ListView)
        child = lv.highlighted_child
        if child is not None:
            return getattr(child, "_preset", None)
        return None

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        preset = getattr(event.item, "_preset", None)
        if preset:
            self.dismiss(preset)

    async def action_new_preset(self) -> None:
        async def _on_result(params: "dict | None") -> None:
            if params is not None:
                self.dismiss(params)

        await self.app.push_screen(ConnectionFormScreen(), _on_result)

    async def action_edit_preset(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return

        async def _on_result(params: "dict | None") -> None:
            if params is not None:
                self.dismiss(params)

        await self.app.push_screen(ConnectionFormScreen(prefill=preset), _on_result)

    async def action_delete_preset(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return
        name = preset.get("name", "?")

        async def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                delete_preset(name)
                self._refresh_list()

        await self.app.push_screen(
            ConfirmDialog(f"Delete preset [bold]{name}[/bold]?"), _on_confirm
        )


# ---------------------------------------------------------------------------
# Connection form screen
# ---------------------------------------------------------------------------

class ConnectionFormScreen(Screen["dict | None"]):
    """Form screen for creating or editing a connection preset."""

    DEFAULT_CSS = """
    ConnectionFormScreen {
        align: center middle;
    }
    #form-panel {
        width: 72;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #form-panel Label {
        margin-top: 1;
    }
    #form-buttons {
        margin-top: 1;
        height: auto;
        align: right middle;
    }
    #form-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, prefill: Optional[dict] = None) -> None:
        super().__init__()
        self._prefill = prefill or {}
        self._last_proto = str(self._prefill.get("protocol", "vpnet"))

    def compose(self) -> ComposeResult:
        pre = self._prefill
        proto = pre.get("protocol", "vpnet")
        with Vertical(id="form-panel"):
            yield Label("Name (leave blank to connect without saving):")
            yield Input(
                value=pre.get("name", ""),
                placeholder="e.g. living-room",
                id="name-input",
            )
            yield Label("Protocol:")
            yield Select(
                [(label, val) for label, val in _PROTOCOL_LABELS],
                value=proto,
                id="proto-select",
            )
            yield Label("Host:")
            yield Input(
                value=pre.get("host", ""),
                placeholder="192.168.1.50",
                id="host-input",
            )
            yield Label("Port:")
            yield Input(
                value=str(pre.get("port", _DEFAULT_PORTS[proto])),
                placeholder="port",
                id="port-input",
            )
            yield Label("Password (ESC/VP.net / HTTP):", id="password-label")
            yield Input(
                value=pre.get("password", ""),
                placeholder="leave blank if not required",
                password=True,
                id="password-input",
            )
            with Horizontal(id="form-buttons"):
                yield Button("Back", variant="default", id="btn-back")
                yield Button("Connect", variant="default", id="btn-nosave")
                yield Button("Connect & Save", variant="primary", id="btn-connect")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()
        self._update_password_visibility()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "proto-select":
            proto = str(event.value)
            port_input = self.query_one("#port-input", Input)
            port_value = port_input.value.strip()
            old_default = _DEFAULT_PORTS.get(self._last_proto, 80)
            # Only auto-apply protocol defaults if the user has not set a custom port.
            if not port_value or (port_value.isdigit() and int(port_value) == old_default):
                port_input.value = str(_DEFAULT_PORTS.get(proto, 80))
            self._last_proto = proto
            self._update_password_visibility()

    def _update_password_visibility(self) -> None:
        proto = str(self.query_one("#proto-select", Select).value)
        visible = proto in ("vpnet", "http")
        self.query_one("#password-label", Label).display = visible
        self.query_one("#password-input", Input).display = visible

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.dismiss(None)
        elif event.button.id == "btn-nosave":
            self._submit(save=False)
        elif event.button.id == "btn-connect":
            self._submit(save=True)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.stop()

    def _submit(self, save: bool) -> None:
        proto = str(self.query_one("#proto-select", Select).value)
        name = self.query_one("#name-input", Input).value.strip()
        host = self.query_one("#host-input", Input).value.strip()
        port_str = self.query_one("#port-input", Input).value.strip()
        password = self.query_one("#password-input", Input).value
        try:
            port = int(port_str)
        except ValueError:
            port = _DEFAULT_PORTS.get(proto, 80)
        self.dismiss({
            "name": name,
            "protocol": proto,
            "host": host,
            "port": port,
            "password": password,
            "save": save and bool(name),
        })


# ---------------------------------------------------------------------------
# Main terminal app
# ---------------------------------------------------------------------------

class TerminalApp(App[None]):
    """Interactive Epson projector terminal TUI."""

    CSS = """
    Screen { layout: vertical; }

    #panels { height: 1fr; }

    #left-col {
        width: 36;
        min-width: 28;
    }

    #info-panel {
        height: auto;
        border: solid $primary;
        padding: 0 1;
    }
    #info-panel Label { height: 1; }

    #quick-panel {
        height: auto;
        border: solid $accent;
        padding: 0 1;
    }
    #quick-panel Label { height: 1; }
    #quick-buttons { height: auto; layout: grid; grid-size: 2; grid-gutter: 0; }
    #quick-buttons Button { width: 1fr; }

    #input-panel {
        height: 1fr;
        border: solid $secondary;
        padding: 0 1;
    }
    #input-panel Label { height: 1; }
    TextArea { height: 1fr; }

    #log-panel {
        width: 1fr;
        border: solid $secondary;
        padding: 0 1;
    }
    #log-file-label {
        width: 1fr;
        height: auto;
        color: $text-muted;
    }
    #cmd-log { height: 1fr; }
    """

    BINDINGS = [
        Binding("ctrl+s", "send_commands", "Send", show=True, priority=True),
        Binding("ctrl+o", "open_connect", "Connect", show=True, priority=True),
        Binding("c", "open_connect", "Connect", show=False),
        Binding("ctrl+q", "quit", "Quit", show=True, priority=True),
        Binding("q", "quit", "Quit", show=False),
    ]

    status_text: reactive[str] = reactive("Disconnected")
    status_style: reactive[str] = reactive("red")

    def __init__(
        self,
        client: Optional[AbstractProjectorClient] = None,
        initial_params: Optional[dict] = None,
    ) -> None:
        super().__init__()
        self._client = client
        self._initial_params = initial_params or {}
        self._history: list[str] = []
        self._history_idx: int = -1
        self._reconnect_countdown_timer: Optional[object] = None
        self._reconnect_next_s: int = 0
        self._reconnect_attempt: int = 0
        self._cmd_queue: asyncio.Queue = asyncio.Queue()
        self._sending = False
        self._log_file: Optional[IO[str]] = None
        self._active_preset_name: Optional[str] = None

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="panels"):
            with Vertical(id="left-col"):
                with Vertical(id="info-panel"):
                    yield Label("Connection  [red]Disconnected[/red]", id="connection-header-label", markup=True)
                    yield Label("", id="preset-name-label")
                    yield Label("", id="proto-label")
                    yield Label("", id="host-label")
                with Vertical(id="quick-panel"):
                    yield Label("Quick commands")
                    with Horizontal(id="quick-buttons"):
                        pass  # populated in on_mount
                with Vertical(id="input-panel"):
                    yield Label("[Ctrl+S] send  [↑/↓] history")
                    yield TextArea(id="cmd-input")
            with Vertical(id="log-panel"):
                yield Label("Command log  [select text to copy]")
                yield Label("", id="log-file-label")
                yield TextArea("", read_only=True, id="cmd-log")
        yield Footer()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def on_mount(self) -> None:
        self._populate_quick_commands()
        if self._client is not None:
            self._attach_client(self._client, self._initial_params)
            asyncio.create_task(self._connect_client())
        else:
            await self._push_connect_screen()

    async def _push_connect_screen(self) -> None:
        async def _on_result(params: "dict | None") -> None:
            if params is None:
                return
            await self._apply_new_connection(params)

        presets = load_presets()
        if presets:
            await self.push_screen(PresetListScreen(initial_preset_name=self._active_preset_name), _on_result)
        else:
            await self.push_screen(ConnectionFormScreen(), _on_result)

    async def on_unmount(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
        if self._log_file is not None:
            try:
                self._log_file.close()
            except Exception:
                pass
            self._log_file = None

    async def _connect_client(self) -> None:
        assert self._client is not None
        try:
            await self._client.connect()
        except Exception as exc:
            self._log_system(f"Connection failed: {exc}")

    # ------------------------------------------------------------------
    # Client attachment
    # ------------------------------------------------------------------

    def _attach_client(
        self, client: AbstractProjectorClient, params: Optional[dict]
    ) -> None:
        """Store client, wire state callback, update info panel labels."""
        # Close any previous session log before starting a new one
        if self._log_file is not None:
            try:
                self._log_file.close()
            except Exception:
                pass
            self._log_file = None

        self._client = client
        self._client._on_state_change = self._on_state_change

        if params:
            name = params.get("name", "")
            self._active_preset_name = name if name else None
            self.query_one("#preset-name-label", Label).update(
                f"Preset:   [bold]{name}[/bold]" if name else ""
            )
            self.query_one("#proto-label", Label).update(
                f"Protocol: [bold]{params.get('protocol','?')}[/bold]"
            )
            self.query_one("#host-label", Label).update(
                f"Host:     {params.get('host','?')}:{params.get('port','?')}"
            )
            protocol = params.get("protocol", "serial")
            name = params.get("name", "").strip()
            slug = name if name else f"{params.get('host','unknown')}-{params.get('port','0')}"
            log_file = _open_session_log(self, protocol, slug)
            self._log_file = log_file
            log_label = self.query_one("#log-file-label", Label)
            if log_file is not None:
                log_label.update(f"[dim]{log_file.name}[/dim]")
            else:
                log_label.update("")

    def _on_state_change(self, state: str, attempt: int, next_retry_s: int) -> None:
        """Called from the client — may be an asyncio task or a background thread."""
        try:
            asyncio.get_running_loop()
            # Already on the event loop (e.g. HTTP connect or serial asyncio task).
            self.call_later(self._apply_state, state, attempt, next_retry_s)
        except RuntimeError:
            # Called from a background OS thread.
            self.call_from_thread(self._apply_state, state, attempt, next_retry_s)

    def _apply_state(self, state: str, attempt: int, next_retry_s: int) -> None:
        header_label = self.query_one("#connection-header-label", Label)
        if self._reconnect_countdown_timer is not None:
            self._reconnect_countdown_timer.stop()
            self._reconnect_countdown_timer = None

        if state == "connected":
            header_label.update("Connection  [green]Connected[/green]")
            self._log_system("Connected")
        elif state == "disconnected":
            header_label.update("Connection  [red]Disconnected[/red]")
            self._log_system("Disconnected")
        elif state == "reconnecting":
            self._reconnect_next_s = next_retry_s
            self._reconnect_attempt = attempt
            header_label.update(
                f"Connection  [yellow]Reconnecting\u2026 {next_retry_s}s[/yellow]"
            )
            self._reconnect_countdown_timer = self.set_interval(
                1.0, self._tick_reconnect_countdown
            )

    def _tick_reconnect_countdown(self) -> None:
        if self._reconnect_next_s > 1:
            self._reconnect_next_s -= 1
            self.query_one("#connection-header-label", Label).update(
                f"Connection  [yellow]Reconnecting\u2026 {self._reconnect_next_s}s[/yellow]"
            )
        else:
            if self._reconnect_countdown_timer:
                self._reconnect_countdown_timer.stop()
                self._reconnect_countdown_timer = None

    # ------------------------------------------------------------------
    # Quick commands
    # ------------------------------------------------------------------

    def _populate_quick_commands(self) -> None:
        container = self.query_one("#quick-buttons")
        container.remove_children()
        for cmd in _DEFAULT_QUICK_CMDS:
            btn = Button(cmd, id=f"qcmd-{cmd.replace(' ', '_').replace('?', 'Q')}")
            btn.tooltip = cmd
            container.mount(btn)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("qcmd-"):
            # Extract command from button label
            cmd = str(event.button.label)
            await self._do_send([cmd])

    # ------------------------------------------------------------------
    # Send action
    # ------------------------------------------------------------------

    async def action_send_commands(self) -> None:
        textarea = self.query_one("#cmd-input", TextArea)
        text = textarea.text.strip()
        if not text:
            return
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return
        # Save to history
        self._history.insert(0, text)
        self._history_idx = -1
        # Clear input
        textarea.clear()
        await self._do_send(lines)

    async def _do_send(self, lines: list[str]) -> None:
        if self._client is None:
            self._log_system("No active connection.")
            return
        is_batch = len(lines) > 1
        if is_batch:
            self._append_to_log(f"{_timestamp()}  -- batch ({len(lines)} cmds) --")
        for cmd in lines:
            ts = _timestamp()
            try:
                response, duration_ms = await self._client.send(cmd)
            except ClientNotConnectedError:
                self._append_to_log(f"{ts}  {cmd}  ->  (not connected)")
                continue
            except Exception as exc:
                self._append_to_log(f"{ts}  {cmd}  ->  Error: {exc}")
                continue
            self._write_log_entry(ts, cmd, response, duration_ms, indent=is_batch)

    def _write_log_entry(
        self,
        ts: str,
        cmd: str,
        response: str,
        duration_ms: float,
        indent: bool = False,
    ) -> None:
        display_resp = response.replace("\r:", "").strip()
        err_marker = "[ERR]  " if display_resp == "ERR" else ""
        display_resp = display_resp or "OK"
        prefix = "  " if indent else ""
        self._append_to_log(
            f"{prefix}{ts}  {cmd}  ->  {err_marker}{display_resp}  [{duration_ms:.0f} ms]"
        )

    def _log_system(self, msg: str) -> None:
        self._append_to_log(f"{_timestamp()}  >> {msg}")

    def _append_to_log(self, line: str) -> None:
        log = self.query_one("#cmd-log", TextArea)
        log.read_only = False
        text_to_add = ("\n" if log.text else "") + line
        log.insert(text_to_add, location=log.document.end, maintain_selection_offset=True)
        log.read_only = True
        log.scroll_end(animate=False)
        if self._log_file is not None:
            try:
                self._log_file.write(line + "\n")
                self._log_file.flush()
            except Exception:
                self._log_file = None

    # ------------------------------------------------------------------
    # History navigation
    # ------------------------------------------------------------------

    async def on_key(self, event) -> None:
        focused = self.focused
        textarea = self.query_one("#cmd-input", TextArea)
        if focused is not textarea:
            return
        if event.key == "up":
            if self._history and self._history_idx < len(self._history) - 1:
                self._history_idx += 1
                textarea.clear()
                textarea.insert(self._history[self._history_idx])
            event.stop()
        elif event.key == "down":
            if self._history_idx > 0:
                self._history_idx -= 1
                textarea.clear()
                textarea.insert(self._history[self._history_idx])
            elif self._history_idx == 0:
                self._history_idx = -1
                textarea.clear()
            event.stop()

    # ------------------------------------------------------------------
    # Connect screens
    # ------------------------------------------------------------------

    async def action_open_connect(self) -> None:
        await self._push_connect_screen()

    async def _apply_new_connection(self, params: dict) -> None:
        # Save preset if requested
        if params.get("save") and params.get("name"):
            save_preset({
                "name": params["name"],
                "protocol": params["protocol"],
                "host": params["host"],
                "port": params["port"],
                "password": params.get("password", ""),
            })

        # Close existing connection
        if self._client is not None:
            try:
                self._client._on_state_change = None  # suppress stale callbacks
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None
            self._apply_state("disconnected", 0, 0)

        protocol = params["protocol"]
        host = params["host"]
        port = params["port"]
        password = params.get("password", "")

        if not host:
            self._log_system("No host specified — not connecting.")
            return

        if protocol == "serial":
            client: AbstractProjectorClient = SerialClient(host, port)
        elif protocol == "vpnet":
            client = VpnetClient(host, port, password=password)
        else:
            client = HttpClient(host, port, password)

        self._initial_params = params
        self._attach_client(client, params)
        self._log_system(f"Connecting to {host}:{port} via {protocol}…")
        asyncio.create_task(self._connect_client())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    now = datetime.now()
    return now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


def _slug(text: str) -> str:
    """Sanitise text for use in a filename."""
    return re.sub(r"[^\w.\-]", "-", text).strip("-") or "session"


def _open_session_log(app: "TerminalApp", protocol: str, name_or_slug: str) -> Optional[IO[str]]:
    """Create a new per-session log file; return the open handle or None on error."""
    logs_dir = Path(user_config_dir("epson_terminal")) / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        app._append_to_log(f"{_timestamp()}  >> Warning: could not create logs directory: {exc}")
        return None
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{date_str}_{_slug(protocol)}_{_slug(name_or_slug)}.log"
    path = logs_dir / filename
    try:
        return path.open("a", encoding="utf-8")
    except Exception as exc:
        app._append_to_log(f"{_timestamp()}  >> Warning: could not open log file {path}: {exc}")
        return None
