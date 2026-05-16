# Tasks: multi-transport-refactor

## 1. Project Setup

- [x] 1.1 Create `pyproject.toml` with project metadata and dependencies: `textual`, `aiohttp`, `pyyaml`
- [x] 1.2 Create package directory structure: `projector/`, `transports/`, `ui/`, `models/`
- [x] 1.3 Add `__init__.py` files to each new package

## 2. Model Definition

- [x] 2.1 Implement `projector/model.py`: `ModelDef` dataclass and `load_model(path)` function that parses a YAML file
- [x] 2.2 Create `models/eh_tw3200.yaml` with all commands from existing `server.py` (PWR, SOURCE, ASPECT, LUMINANCE, BRIGHT, CONTRAST, CMODE, MUTE, HREVERSE, VREVERSE, LAMP, SNO, etc.)

## 3. Projector State

- [x] 3.1 Implement `projector/state.py`: `ProjectorState` class with `get()`, `set()`, observer registration, and initialisation from a `ModelDef`

## 4. ESC/VP21 Engine

- [x] 4.1 Implement `projector/engine.py`: `handle_command(state, model, cmd_str) -> str` pure function covering GET, SET, INC/DEC, null command, and ERR responses

## 5. Transport Base

- [x] 5.1 Implement `transports/base.py`: `BaseTransport` abstract class with `start()` coroutine interface and a shared `handle_escvp21_stream(reader, writer, state, model)` helper used by serial and vpnet

## 6. Serial Transport

- [x] 6.1 Implement `transports/serial.py`: `SerialTransport` that listens on port 12345 (configurable) and uses the shared stream handler

## 7. ESC/VP.net Transport

- [x] 7.1 Implement `transports/vpnet.py`: `VpnetTransport` that listens on port 3629 (configurable), performs the HELLO → CONNECT binary handshake, then delegates to the shared ESC/VP21 stream handler

## 8. HTTP Transport

- [x] 8.1 Implement `transports/http.py`: `HttpTransport` stub using `aiohttp` that returns HTTP 200 with `"HTTP transport not yet implemented"` for all routes

## 9. TUI

- [x] 9.1 Implement `ui/app.py`: Textual `App` with a state panel (DataTable or similar), a command log (RichLog or ListView), and a power-toggle key binding (`p`)
- [x] 9.2 Wire observer callback from `ProjectorState` to the TUI state panel so it refreshes on any state change
- [x] 9.3 Wire command logging: each transport logs received commands to the TUI log widget with timestamp and transport name

## 10. Main Entry Point

- [x] 10.1 Implement `main.py`: parse `--model`, `--serial-port`, `--vpnet-port`, `--http-port` CLI args; load model; create `ProjectorState`; start all transports as asyncio background tasks inside Textual's `on_mount`; run the Textual app

## 11. Repo Housekeeping

- [x] 11.1 Create `agents.md` at repo root describing the project, architecture, key files, and how to extend it
- [x] 11.2 Verify old `server.py` is superseded (keep for reference or remove — confirm with user)
