## Context

The repo currently has a server-side architecture: `transports/` are protocol servers, `projector/engine.py` processes commands, and `projector/state.py` holds shared mutable state. The Textual TUI (`ui/app.py`) drives the emulator.

Adding the terminal tool requires a client-side mirror of the transport layer, a separate TUI, and a new entry point — but can reuse `projector/model.py` (command definitions) and the `aiohttp`/`textual` dependencies already present.

The repo is renamed `epson-projector-tools` to reflect dual purpose.

## Goals / Non-Goals

**Goals:**
- Async client layer with a uniform interface across serial TCP, ESC/VP.net, and HTTP protocols
- Textual TUI with two-column layout, multiline input, in-session history, auto-reconnect, and optional model integration
- Repo rename with two `pyproject.toml` entry points
- No new runtime dependencies

**Non-Goals:**
- Persistent command history across sessions
- Tab-completion in the text input (model hints are in-line, not autocomplete)
- Script/batch file loading from disk
- Emulator ↔ terminal integration beyond "run both in separate terminals"
- Any changes to existing emulator code

## Decisions

### D1 — `client/` package with abstract base class

A new `client/` package mirrors `transports/` on the client side. Each client implements:

```python
class AbstractProjectorClient(ABC):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send(self, cmd: str) -> tuple[str, float]: ...  # (response, ms)
    @property
    def connected(self) -> bool: ...
```

`send()` returns `(response_str, duration_ms)` where `response_str` is always formatted as ESC/VP21 (e.g. `SNO=LPKB3G001K\r:`, `\r:`, `ERR\r:`), regardless of protocol. The terminal UI never needs to know which protocol is active.

**Alternative considered:** Merge client logic into the TUI directly. Rejected — the clean abstraction makes unit testing feasible and protocol switching in the UI trivial.

### D2 — HTTP client routing

GET commands (`CMD?`) map to `GET /cgi-bin/json_query?jsoncallback=CMD?`. SET commands (`CMD VALUE`) map to `GET /cgi-bin/directsend?CMD=VALUE`. Both are GETs. A `_=<timestamp>` cache-buster query param and a `Referer: http://<host>/cgi-bin/webconf` header are included on every request (observed requirement from real devices).

The JSON response (`projector.feature.reply`, `projector.feature.error`) is translated into ESC/VP21 format before being returned by `send()`.

**Alternative considered:** Expose HTTP-native responses. Rejected — the unified interface (D1) requires ESC/VP21 format.

### D3 — Auto-reconnect for serial/vpnet clients

On connection loss (EOF, `ConnectionResetError`, OS error), the client enters a reconnecting loop with exponential backoff: 1 s, 2 s, 4 s, 8 s, 16 s, 30 s (cap). The loop runs as a background asyncio task. The TUI subscribes to a connection-state callback (`(state: Literal["connected","disconnected","reconnecting"], attempt: int, next_retry_s: int) -> None`).

During reconnecting, `send()` raises `ClientNotConnectedError` immediately (commands are not queued). HTTP has no persistent connection; "reconnect" means the next `send()` will attempt the HTTP request — the backoff logic is not needed.

**Alternative considered:** Queue commands during reconnect and replay on reconnection. Rejected — replaying stale commands against a projector that has changed state (e.g. just powered back on) is error-prone and confusing.

### D4 — Multiline input with `TextArea`

Textual's `TextArea` (available since Textual 0.38, required ≥ 0.80) is used for the command input area. `Ctrl+Enter` is bound to "send all lines sequentially". Each line is sent in order; the next line is sent only after the current response is received (`:` for serial/vpnet, HTTP response for HTTP). This ensures correct sequencing without any artificial delay.

In-session history is stored as a `list[str]` of previously submitted text blocks (not individual lines). `Up`/`Down` arrows cycle through the history list and populate the `TextArea`.

### D5 — Model integration tiers

| Model loaded? | Behaviour |
|---|---|
| No | Hardcoded quick commands: `SNO?`, `PWR?`, `PWR 01`, `PWR 02`, `SOURCE?` |
| Yes | Quick commands populated from model's `readable=True` commands; hardcoded set hidden |
| Yes | Input validation: unknown command names highlighted (yellow) before send; still sendable |
| Yes | Value hints: after typing a known command name + space, a status line shows `range`, `set_values`, or `set_map` keys |

Tab-completion is explicitly out of scope.

### D6 — Connection dialog and CLI args

CLI: `epson-terminal [--protocol serial|vpnet|http] [--host H] [--port P] [--password PW] [--model PATH]`

If all required args for the chosen protocol are present, the connection dialog is skipped and the terminal connects immediately on startup. If args are absent or `--protocol` is omitted, the connect dialog opens first.

`c` key opens the connect dialog at any time (closes existing connection cleanly first).

### D7 — Repo rename

`pyproject.toml`:
- `name = "epson-projector-tools"` (was `epson-emulator`)
- `[project.scripts]`: `epson-emulator = "main:main"` kept; `epson-terminal = "terminal:main"` added
- `[tool.setuptools.packages.find]` gains `"client*"` and keeps existing entries

## Risks / Trade-offs

- **TextArea key binding conflicts**: Textual may intercept `Ctrl+Enter` differently on some terminals. Mitigation: also bind `F5` as a secondary send shortcut.
- **HTTP Digest auth complexity**: The `aiohttp` session must replay the request after receiving a 401 (two-round-trip auth). `aiohttp` has built-in DigestAuth support; use that rather than the manual implementation in `transports/http.py`. Mitigation: test against the real device.
- **ESC/VP.net handshake on reconnect**: Each reconnect must redo the HELLO/CONNECT handshake. The `VpnetClient` handles this inside `connect()`, so reconnect is just `disconnect()` + `connect()`.
- **Real projector not always available**: The terminal cannot be integration-tested without hardware. Mitigation: point it at the local emulator for functional testing.

## Open Questions

- None blocking implementation.
