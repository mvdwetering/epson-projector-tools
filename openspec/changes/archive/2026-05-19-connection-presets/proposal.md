## Why

Users frequently reconnect to the same projectors but must re-enter all connection parameters (protocol, host, port, password) every time — either on the command line or in the connect dialog. Named presets eliminate this repetition by letting users save and recall connections by name.

## What Changes

- **New**: Named connection presets stored in a platform-appropriate config file (`~/.config/epson_terminal/presets.yaml` on Linux/macOS, `%APPDATA%\Local\epson_terminal\presets.yaml` on Windows) via `platformdirs`.
- **New**: Preset list screen is the default entry point when launching the terminal — shows all saved presets with one-key connect, delete, and new-preset actions.
- **New**: Separate connection form screen (used for new presets and editing existing ones) with a "Save as preset" step before connecting.
- **New**: `terminal.py <preset_name>` positional CLI argument — connects directly to a named preset without showing any dialog.
- **BREAKING**: Remove `--protocol`, `--host`, `--port`, `--password` CLI arguments.
- **BREAKING**: Remove `--model` CLI argument and all model-loading logic from the terminal.

## Capabilities

### New Capabilities

- `connection-presets`: Persistent named presets — schema, file location, load/save/delete operations, and cross-platform path resolution.

### Modified Capabilities

- `terminal-tui`: Replace the single `ConnectDialog` modal with a two-screen flow: a preset list screen and a connection form screen. CLI entry point changes from named flags to a positional preset argument.

## Impact

- `terminal.py`: argparse changes (remove flags, add positional), remove model loading.
- `ui/terminal_app.py`: `ConnectDialog` replaced by two new screens; `TerminalApp` no longer receives `model` or `initial_params`.
- New module `client/presets.py` (or `projector/presets.py`): preset file I/O.
- New dependency: `platformdirs` (add to `pyproject.toml`).
- The quick-commands panel will always use the hard-coded default command list (model feature removed).
