# Epson Projector Emulator — Agent Guide

## Project overview

This repository emulates an Epson ESC/VP21 projector over three concurrent network transports:

| Transport | Protocol | Default port |
|-----------|----------|-------------|
| Serial TCP | Raw ESC/VP21 (`\r`-terminated) | 12345 |
| ESC/VP.net | Binary handshake → ESC/VP21 pipe | 3629 |
| HTTP | Stub (placeholder for future expansion) | 8080 |

All transports share a single `ProjectorState` instance. An interactive Textual TUI shows live state and the command log.

## Running

```bash
pip install -e .          # install dependencies from pyproject.toml
python main.py            # default model (EH-TW3200), default ports
python main.py --model eh_tw9400 --serial-port 12345
```

Press `p` in the TUI to toggle power, `q` to quit.

## Architecture

```
main.py
├── loads model YAML  →  projector/model.py  (ModelDef, CommandDef dataclasses)
├── creates state     →  projector/state.py  (ProjectorState, observer pattern)
├── starts TUI        →  ui/app.py           (Textual App)
│   └── on_mount starts transports as asyncio tasks:
│       ├── transports/serial.py   (SerialTransport)
│       ├── transports/vpnet.py    (VpnetTransport)
│       └── transports/http.py    (HttpTransport)
└── all transports call projector/engine.py  (handle_command — pure, no I/O)
```

### Key files

| File | Purpose |
|------|---------|
| `projector/model.py` | `ModelDef` / `CommandDef` dataclasses; `load_model(path)` YAML loader |
| `projector/state.py` | `ProjectorState`: shared mutable state + observer callbacks |
| `projector/engine.py` | `handle_command(state, model, cmd_str) -> str` — pure ESC/VP21 logic |
| `transports/base.py` | `BaseTransport` ABC + `handle_escvp21_stream()` shared pipe helper |
| `transports/serial.py` | Raw TCP → ESC/VP21 pipe |
| `transports/vpnet.py` | ESC/VP.net binary handshake → ESC/VP21 pipe |
| `transports/http.py` | aiohttp stub server |
| `ui/app.py` | Textual TUI: state table, command log, key bindings |
| `models/eh_tw3200.yaml` | EH-TW3200 model definition |

## Adding a new projector model

1. Create `models/<model_name>.yaml` — copy `eh_tw3200.yaml` as a template.
2. Edit commands: adjust `default` values, `readable`/`writable` flags, `range`, `set_values`, `set_map`.
3. Run with `python main.py --model <model_name>`.

No Python code changes are needed to add a model.

### YAML command fields

| Field | Type | Description |
|-------|------|-------------|
| `default` | string | Initial value |
| `readable` | bool | Supports GET (`CMD?`) |
| `writable` | bool | Supports SET (`CMD value`) |
| `inc_dec` | bool | Supports `INC`/`DEC` operands |
| `range` | [min, max] | Clamp range for INC/DEC |
| `set_values` | list | Accepted raw SET operands (validation) |
| `set_map` | dict | Maps accepted SET operand → stored value (e.g. `ON: "01"`) |
| `notify_only` | bool | SET acknowledged but not stored (e.g. `KEY`) |

## ESC/VP.net protocol notes

The binary handshake (port 3629):
1. Client → Server: 16-byte HELLO packet (`type=0x01`)
2. Server → Client: HELLO response (`status=0x20`)
3. Client → Server: 16-byte CONNECT packet (`type=0x03`)
4. Server → Client: CONNECT response (`status=0x20`)
5. Connection is now a raw ESC/VP21 pipe (identical to serial transport)

Header format: `"ESC/VP.net"` (10 bytes) + version `0x10` + type (1) + reserved `0x0000` (2) + status (1) + num_headers (1) = 16 bytes total.

## Extending the HTTP transport

The HTTP transport is intentionally minimal. To add real control:
1. Edit `transports/http.py`
2. Add `aiohttp` routes that call `handle_command(state, model, cmd)` or read `state.get(cmd)` directly
3. Return JSON responses

## Observer pattern

`ProjectorState` supports two observer types:
- **State observer** `(cmd: str, val: str) -> None` — called when any value changes
- **Command observer** `(transport: str, cmd: str, response: str) -> None` — called after each command

Register with `state.add_state_observer(fn)` / `state.add_command_observer(fn)`.

The TUI uses asyncio queues fed by these observers to update widgets without blocking transports.
