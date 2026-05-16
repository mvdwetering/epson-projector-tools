## Context

The emulator is currently a single `server.py` file using Python's synchronous `socketserver.TCPServer`. It emulates a serial-over-TCP connection to an Epson ESC/VP21 projector (specifically the EH-TW3200 model). Model data is hardcoded. The architecture needs to support three concurrent transports sharing one projector state, with an interactive TUI and extensibility for multiple projector models.

## Goals / Non-Goals

**Goals:**
- Three concurrent async transports: serial TCP, ESC/VP.net TCP, HTTP stub
- Single shared `ProjectorState` across all transports
- YAML-based model definitions to allow per-model command sets, defaults, and value ranges
- Interactive Textual TUI showing live state, command log, and keyboard controls
- Clean separation: transport layer ↔ ESC/VP21 engine ↔ projector state ↔ model definition
- ESC/VP21 engine has no I/O — fully testable in isolation

**Non-Goals:**
- Full HTTP control API (placeholder only — to be expanded later)
- ESC/VP.net UDP HELLO/discovery
- Password authentication in ESC/VP.net (always accept; no-password mode)
- Emulating power-state timing realistically (keep simple mock delay)
- Multi-client concurrency per transport (one active ESC/VP.net session at a time is realistic)

## Decisions

### 1. asyncio throughout

**Decision**: Use `asyncio` with `asyncio.start_server()` for all TCP transports.

**Rationale**: Textual is async-native (built on asyncio). Running all transports in one event loop eliminates cross-thread state synchronisation. `asyncio.start_server()` handles multiple concurrent connections naturally. The existing `socketserver` approach cannot co-exist cleanly with Textual.

**Alternative considered**: `threading` with `ThreadingMixIn` — rejected because it requires locks for shared state and doesn't compose with Textual.

### 2. YAML model definitions

**Decision**: One YAML file per model in `models/`, loaded at startup. Structure:
```yaml
name: EH-TW3200
commands:
  PWR:
    default: "01"
    readable: true
    writable: true
    set_values: ["ON", "OFF"]   # valid SET operands; null = accept anything
  BRIGHT:
    default: "11"
    readable: true
    writable: true
    inc_dec: true
    range: [0, 255]
```

**Rationale**: Epson publishes Excel files with model command data — YAML files can be generated from those. Keeps model data out of Python code. New models require no code changes.

**Alternative considered**: Python dataclass-per-model — rejected because adding models requires code changes and redeployment.

### 3. ESC/VP21 engine is pure function / no I/O

**Decision**: `engine.py` exposes `handle_command(state, model, command_str) -> str` — takes parsed input, returns response string. All I/O stays in transport layer.

**Rationale**: Fully testable without sockets. Each transport calls the engine identically after its own handshake/framing.

### 4. ESC/VP.net handshake hardcoded constants

**Decision**: Version `0x10`, IM-Type `0x21` (Type C/E), Projector-Command-Type `0x21` (ESC/VP21 Ver1.0) are hardcoded in the transport. No per-model variation.

**Rationale**: Only ESC/VP21 Ver1.0 is supported. IM-Type is discovery metadata and not functionally relevant for the emulator. Avoids polluting model YAML with protocol-level constants.

### 5. ProjectorState uses asyncio events for UI notification

**Decision**: `ProjectorState` maintains the state dict and emits asyncio `Event` or callback notifications when values change. The TUI subscribes to updates.

**Rationale**: Decouples transports from UI. Transports write state; TUI reads it reactively without polling.

### 6. Textual for TUI

**Decision**: Use `textual` library. Layout: left panel (projector state), right panel (command log, scrolling), bottom bar (keyboard shortcuts).

**Rationale**: Textual is async-native (same event loop), provides rich widget library, handles keyboard input cleanly. The TUI runs as the main asyncio app; transports are started as background tasks within it.

### 7. File/module layout

```
epson_emulator/
├── main.py                  # entry point: CLI args, start TUI + transports
├── models/
│   └── eh_tw3200.yaml
├── projector/
│   ├── model.py             # ModelDef dataclass + YAML loader
│   ├── state.py             # ProjectorState (shared mutable state + observers)
│   └── engine.py            # handle_command() — pure, no I/O
├── transports/
│   ├── base.py              # EscVp21Connection: async read loop, calls engine
│   ├── serial.py            # raw TCP pipe → base connection
│   ├── vpnet.py             # binary handshake → base connection
│   └── http.py              # aiohttp stub server
└── ui/
    └── app.py               # Textual App: widgets, keyboard bindings
```

## Risks / Trade-offs

- **Textual learning curve** → Mitigation: Textual has excellent docs; the layout is straightforward (two panels + status bar).
- **asyncio + blocking sleep in power emulation** → Mitigation: Replace `time.sleep(10)` with `await asyncio.sleep(10)`.
- **aiohttp adds a dependency just for a stub** → Decision: Use `aiohttp` since it will be needed when HTTP is expanded anyway.
- **YAML model validation** → Use Python `dataclasses` with a hand-written `from_dict()` class method; raises `ValueError` at load time with a clear error. No third-party validation library needed.

## Migration Plan

1. New package structure is created alongside old `server.py`
2. Old `server.py` is deleted once new entry point is functional
3. Serial transport preserves existing port default (12345) — Home Assistant integrations continue to work without reconfiguration
4. ESC/VP.net transport defaults to port 3629 (spec default)
5. HTTP transport defaults to port 8080

## Open Questions

- HTTP stub uses `aiohttp`. ✓
- Command log in the TUI is in-memory only; no file persistence. ✓
- Dependencies managed via `pyproject.toml`. ✓
