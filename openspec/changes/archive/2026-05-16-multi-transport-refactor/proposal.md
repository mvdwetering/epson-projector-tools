## Why

The emulator currently supports only a single serial-over-TCP transport and is implemented as a single monolithic file, making it hard to extend. Adding ESC/VP.net (binary handshake TCP) and HTTP support — while sharing one emulated projector state — requires a clean multi-transport architecture with a proper separation of concerns.

## What Changes

- **BREAKING**: Refactor `server.py` into a multi-module package (`projector/`, `transports/`, `ui/`)
- Add ESC/VP.net transport (TCP port 3629): binary 16-byte handshake (CONNECT), then ESC/VP21 pipe
- Add HTTP transport stub (placeholder for future expansion)
- Extract shared ESC/VP21 command engine from transport-specific code
- Replace hardcoded EH-TW3200 model data with YAML-based model definitions
- Multi-model support: different commands, defaults, and ranges per model
- Replace synchronous `socketserver` with fully async (`asyncio`) architecture
- Add interactive Textual TUI: live projector state panel, command log, keyboard controls
- Add `AGENTS.md` to repository root
- All three transports share a single `ProjectorState` instance

## Capabilities

### New Capabilities

- `escvp21-engine`: Core ESC/VP21 command processing — parse, validate, execute commands against projector state; model-aware (supported commands, ranges, inc/dec); shared by all transports
- `projector-state`: Shared in-memory projector state with observer/event support so UI and transports can react to changes
- `model-definition`: YAML-based model files defining supported commands, defaults, value constraints, and inc/dec support; loader + validation
- `serial-transport`: Async TCP transport that accepts a raw connection and pipes bytes to the ESC/VP21 engine (current behavior, refactored)
- `vpnet-transport`: Async TCP transport implementing the ESC/VP.net binary handshake (CONNECT request/response), then pipes to the same ESC/VP21 engine
- `http-transport`: Async HTTP server stub — accepts connections, returns placeholder responses; to be expanded later
- `tui`: Textual-based interactive UI showing projector state, recent command log, and keyboard controls for manual state changes

### Modified Capabilities

## Impact

- `server.py` is fully replaced by the new package structure
- New dependency: `textual` (TUI), `pyyaml` (model files), `aiohttp` or `aiohttp`-lite for HTTP stub
- Existing serial-style clients (e.g. Home Assistant `socket://host:12345`) continue to work unchanged on the same port
- ESC/VP.net clients connect on port 3629
- HTTP clients connect on port 8080 (stub)
