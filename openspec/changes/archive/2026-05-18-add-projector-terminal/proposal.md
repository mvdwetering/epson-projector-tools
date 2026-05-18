## Why

The repo currently only contains an Epson projector emulator. Adding a client-side terminal tool completes the toolkit: developers and integrators can now use the same repo to both emulate and interactively control real projectors. Renaming the repo to `epson-projector-tools` reflects this expanded scope.

## What Changes

- **BREAKING** Rename package from `epson-emulator` to `epson-projector-tools`; add a second entry point `epson-terminal`
- Add `client/` package with protocol-agnostic async client abstraction and three concrete implementations: serial TCP, ESC/VP.net, HTTP
- Add `terminal.py` top-level entry point and `ui/terminal_app.py` Textual TUI
- HTTP client hides protocol differences — all three transports expose the same ESC/VP21 command interface to the terminal UI
- Model YAML is optional; when supplied it enables quick-command shortcuts and input validation/hints
- In-session command history (up/down arrow navigation), not persisted
- Hardcoded default quick commands (`SNO?`, `PWR?`, `PWR 01`, `PWR 02`, `SOURCE?`) shown when no model is loaded; model-driven quick commands replace them when a model is supplied
- Auto-reconnect with exponential backoff (1 s → 2 s → … → 30 s cap) for serial/vpnet; HTTP retries on next send
- Connection parameters configurable via CLI args; switchable at runtime via an in-UI connect dialog (`c` key)

## Capabilities

### New Capabilities

- `projector-client`: Abstract async client interface plus serial, ESC/VP.net, and HTTP implementations; handles connect/disconnect/auto-reconnect and response timing
- `terminal-tui`: Textual TUI for the terminal tool — two-column layout (connection info + quick commands + multiline input on the left; timestamped/timed command log on the right), connect dialog, model-optional autocomplete hints

### Modified Capabilities

- `model-definition`: No requirement changes — model loading is reused as-is by the terminal for optional command validation and quick-command generation

## Impact

- `pyproject.toml`: package rename, new `epson-terminal` script entry point, no new dependencies (Textual + aiohttp already present)
- New `client/` package (no dependencies on `transports/` or `projector/state.py`)
- New `terminal.py` entry point
- New `ui/terminal_app.py`
- Existing emulator code untouched
