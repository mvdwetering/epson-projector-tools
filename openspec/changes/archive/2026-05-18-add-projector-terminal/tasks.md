## 1. Repo Rename

- [x] 1.1 Update `pyproject.toml`: rename package to `epson-projector-tools`, add `epson-terminal = "terminal:main"` script entry, add `"client*"` to `packages.find`
- [x] 1.2 Re-install the package in editable mode (`pip install -e .`) to pick up the new entry point

## 2. Client Package — Base

- [x] 2.1 Create `client/__init__.py`
- [x] 2.2 Create `client/base.py`: define `ClientNotConnectedError`, `AbstractProjectorClient` ABC with `connect()`, `disconnect()`, `send(cmd) -> tuple[str, float]`, `connected` property, and `on_state_change` callback support

## 3. Client Package — Serial TCP

- [x] 3.1 Create `client/serial.py`: `SerialClient` implementing `AbstractProjectorClient`; connect to TCP, send `CMD\r`, read until `:`, measure duration, raise `ClientNotConnectedError` when not connected
- [x] 3.2 Implement auto-reconnect background task with exponential backoff (1→2→4→8→16→30 s cap) and state-change callback invocations

## 4. Client Package — ESC/VP.net

- [x] 4.1 Create `client/vpnet.py`: `VpnetClient` implementing `AbstractProjectorClient`; reuse HELLO/CONNECT handshake constants from `transports/vpnet.py`, then delegate to the serial pipe logic
- [x] 4.2 Ensure reconnect calls `disconnect()` + `connect()` (redo handshake each time)

## 5. Client Package — HTTP

- [x] 5.1 Create `client/http.py`: `HttpClient` implementing `AbstractProjectorClient`; use `aiohttp.DigestAuth` for authentication
- [x] 5.2 Implement GET routing: commands ending in `?` → `json_query?jsoncallback=CMD?&_=<ts>` with `Referer` header
- [x] 5.3 Implement SET routing: `CMD VALUE` → `directsend?CMD=VALUE&_=<ts>` with `Referer` header
- [x] 5.4 Parse JSON response (`projector.feature.reply`, `projector.feature.error`) and return ESC/VP21-formatted string
- [x] 5.5 `HttpClient.connected` always returns `True`

## 6. Terminal Entry Point

- [x] 6.1 Create `terminal.py` with `main()` function; parse CLI args (`--protocol`, `--host`, `--port`, `--password`, `--model`); instantiate the correct client; launch `TerminalApp`

## 7. Terminal TUI — Skeleton

- [x] 7.1 Create `ui/terminal_app.py` with `TerminalApp(App)` skeleton; two-column `Horizontal` layout
- [x] 7.2 Add left column: `ConnectionInfoPanel` (static labels for protocol/host/port/status), `QuickCommandsPanel` (button row), `TextArea` for input, hint status line
- [x] 7.3 Add right column: `RichLog` for command log

## 8. Terminal TUI — Connection Info & Status

- [x] 8.1 Wire `on_state_change` callback from client to update the status label in `ConnectionInfoPanel` (Connected / Disconnected / Reconnecting…Xs with countdown)
- [x] 8.2 Implement per-second countdown tick during reconnecting state using `set_interval`

## 9. Terminal TUI — Quick Commands

- [x] 9.1 Populate `QuickCommandsPanel` with hardcoded defaults (`SNO?`, `PWR?`, `PWR 01`, `PWR 02`, `SOURCE?`) when no model is loaded
- [x] 9.2 When a model is loaded, populate buttons from model commands where `readable=True`
- [x] 9.3 Bind button press to insert-and-send the command

## 10. Terminal TUI — Command Input & Send

- [x] 10.1 Bind `Ctrl+Enter` and `F5` to the send action
- [x] 10.2 Implement send action: split `TextArea` content by newline, send lines sequentially (each waits for response before sending next), batch-group log entries
- [x] 10.3 Clear `TextArea` and append submitted block to in-session history after send
- [x] 10.4 Bind `Up`/`Down` arrows to cycle through history and repopulate `TextArea`

## 11. Terminal TUI — Command Log

- [x] 11.1 Implement log entry formatting: `HH:MM:SS.mmm  CMD  →  RESPONSE  [Xms]`
- [x] 11.2 Apply distinct style (red) for `ERR` responses
- [x] 11.3 Emit a batch group header before multi-command batches

## 12. Terminal TUI — Connect Dialog

- [x] 12.1 Implement `ConnectDialog(ModalScreen)` with Protocol select, Host input, Port input (auto-filled by protocol: serial=12345, vpnet=3629, http=80), Password input (visible only for HTTP), Model path input
- [x] 12.2 On dialog submit, close existing client connection, instantiate new client, reconnect, update connection info panel
- [x] 12.3 Bind `c` key to open `ConnectDialog`
- [x] 12.4 On startup: if CLI args are sufficient for the selected protocol, skip dialog; otherwise show it

## 13. Terminal TUI — Model Hints

- [x] 13.1 On each keystroke in the TextArea, parse the current line's command name
- [x] 13.2 If a model is loaded and the command name is recognized (followed by a space), show `range`, `set_values`, or `set_map` keys in the hint status line
- [x] 13.3 If a model is loaded and the command name is unrecognized, highlight the input text in warning style (yellow)
