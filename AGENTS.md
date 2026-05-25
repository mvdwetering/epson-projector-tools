# Epson Projector Tools — Agent Guide

## Project overview

This repository contains two command-line applications:

1. `epson-emulator`: an Epson ESC/VP21 projector emulator with multi-transport servers and a Textual TUI.
2. `epson-terminal`: an interactive client TUI that connects to real projectors or the emulator over serial TCP, ESC/VP.net, or HTTP.

Both tools share protocol conventions and are packaged from `pyproject.toml` entry points.

## Running

Use the project venv.

```bash
pip install -e .

# Emulator
epson-emulator
epson-emulator --help
epson-emulator --password

# Terminal client
epson-terminal
epson-terminal --help
epson-terminal <preset-name>
```

You can also run module entry files directly (`python main.py`, `python terminal.py`) while developing.

## Emulator architecture

```
main.py
├── loads model YAML                  -> projector/model.py
├── creates shared state             -> projector/state.py
├── creates transports               -> transports/serial.py
│                                    -> transports/vpnet.py
│                                    -> transports/http.py
└── runs emulator Textual UI         -> ui/app.py

All command handling goes through    -> projector/engine.py (handle_command)
```

All emulator transports operate on one shared `ProjectorState` instance.

### Emulator defaults and CLI

- Default model: `eh_tw3200` (resolved to `models/eh_tw3200.yaml` when no suffix is given)
- Default bind host: `0.0.0.0`
- Default ports:
	- Serial TCP: `12345`
	- ESC/VP.net: `3629`
	- HTTP: `8080`
- `--password` enables auth on ESC/VP.net and HTTP with initial password `emulatorpassword`
- `--loglevel` controls Python logging

### Emulator TUI (`ui/app.py`)

- Shows connection config panel (ports + auth lock status), state table, and transport command log.
- Key bindings:
	- `p`: toggle power (`PWR ON` / `PWR OFF`)
	- `w`: change auth password at runtime (only when password mode is enabled)
	- `q`: quit
- Command log uses millisecond timestamps and transport labels.

## Terminal client architecture

```
terminal.py
├── optional preset bootstrap         -> client/presets.py
├── client factory                    -> client/serial.py | client/vpnet.py | client/http.py
└── interactive Textual terminal      -> ui/terminal_app.py
```

### Terminal client behavior

- Preset-first UX:
	- If presets exist, opens a preset list screen.
	- If no presets exist, opens a connection form.
	- Passing `epson-terminal <preset-name>` connects immediately using that preset.
- Connection form supports protocol selection, host/port/password, and optional save.
- Saved presets are stored in:
	- `~/.config/epson_terminal/presets.yaml` (via `platformdirs.user_config_dir`)
- Per-session logs are stored in:
	- `~/.config/epson_terminal/logs/*.log`
- Terminal key bindings:
	- `Ctrl+S`: send commands
	- `Ctrl+O` or `c`: open connect/presets flow
	- `Ctrl+Q` or `q`: quit
	- `Up/Down`: navigate command history in input box

### Client transport behavior (`client/*`)

- `SerialClient` and `VpnetClient` are persistent socket clients with auto-reconnect backoff.
- `HttpClient` is request/response based but still has explicit `connect()`/`disconnect()` to validate reachability/auth and manage session middleware.
- All clients normalize responses into ESC/VP21 format:
	- GET success: `CMD=value\r:`
	- SET/null success: `\r:`
	- Error: `ERR\r:`

## Protocol notes

### Serial transport

- Raw TCP ESC/VP21 stream (`\r`-terminated commands, responses ending `:`).
- Implemented by `transports/serial.py` using shared stream loop in `transports/base.py`.

### ESC/VP.net transport

- TCP session mode is CONNECT-first (type `0x03`).
- HELLO (`0x01`) is treated as UDP discovery only and is rejected on TCP with status `0x45`.
- Optional password is carried in extra header id `0x01`.
- Status handling includes:
	- `0x20` success
	- `0x41` unauthorized (password required)
	- `0x43` forbidden (wrong password)
- After successful CONNECT, transport becomes a raw ESC/VP21 pipe.

Header format remains:
`"ESC/VP.net"` (10 bytes) + version (1) + type (1) + reserved (2) + status (1) + num_headers (1).

### HTTP transport

- Implemented in `transports/http.py` using `aiohttp`.
- Supports Epson-style CGI endpoints:
	- `GET /cgi-bin/json_query?jsoncallback=CMD?`
	- `GET /cgi-bin/directsend?CMD=VALUE`
	- `GET /cgi-bin/directsend?KEY=<ir_code>`
- Optional HTTP Digest auth middleware:
	- realm: `Web Control`
	- username expected by clients: `EPSONWEB`
	- qop: `auth`
- Includes IR key dispatch/mapping for selected Epson key codes.

### Wireshark dissector (new behavior)

- Location: `dissectors/escvpnet.lua`
- Auto-registers on both TCP and UDP port `3629`.
- Also available through Wireshark `Decode As -> escvpnet`.
- Uses packet-local (stateless) detection:
	- If payload starts with `ESC/VP.net` magic, it decodes ESC/VP.net header + extension headers.
	- If payload does not start with magic, it decodes payload as `ESC/VP21 data`.
- Adds expert info for malformed/protocol-violation cases (for example short headers, unexpected version, non-zero reserved field, and extension-header length mismatches).

## Core modules

| File | Purpose |
|------|---------|
| `projector/model.py` | YAML-backed `ModelDef` / `CommandDef` definitions and loader |
| `projector/state.py` | Shared mutable state + observer registration + command logging hooks |
| `projector/engine.py` | Pure command handler (`handle_command`) for ESC/VP21 parsing/validation |
| `transports/base.py` | Base transport contract and shared ESC/VP21 stream loop |
| `ui/app.py` | Emulator TUI |
| `ui/terminal_app.py` | Terminal client TUI |
| `client/presets.py` | Preset persistence helpers |
| `dissectors/escvpnet.lua` | Wireshark dissector for ESC/VP.net |

## Model definitions

To add a new projector model:

1. Add `models/<model_name>.yaml` (copy `models/eh_tw3200.yaml` as template).
2. Define command behavior (`default`, read/write flags, ranges, mapping).
3. Run emulator with `--model <model_name>`.

No Python code changes are required for model-only additions.

Supported YAML command fields include:

- `default`: initial stored value
- `readable`: whether `CMD?` is accepted
- `writable`: whether `CMD <value>` is accepted
- `inc_dec`: whether `INC`/`DEC` operands are accepted
- `range`: min/max bounds for increment/decrement operations
- `set_values`: whitelist of accepted set operands
- `set_map`: input-to-stored value mapping (for aliases like `ON -> 01`)
- `notify_only`: acknowledge command but do not mutate stored state

## Observer pattern

`ProjectorState` exposes two observer channels:

- State observer: `(cmd: str, val: str) -> None`
- Command observer: `(transport: str, cmd: str, response: str) -> None`

The emulator UI consumes both through asyncio queues so network handlers stay non-blocking.
