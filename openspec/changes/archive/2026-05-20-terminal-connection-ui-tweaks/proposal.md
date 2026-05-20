## Why

The connection info panel in the terminal TUI wastes vertical space by placing the connection status on its own line and the port on its own line. Consolidating these into fewer rows frees space for additional quick-command buttons. Additionally, reopening the Connect dialog loses the user's context because the current preset is never pre-selected, forcing extra navigation.

## What Changes

- The `status-label` ("Connected" / "Disconnected" / "Reconnecting…") is moved inline with the "Connection" header label, so the heading reads e.g. `Connection  [Connected]`.
- The port is shown on the same line as the host (e.g. `Host: 192.168.1.50:3629`), eliminating the separate `port-label` row.
- The connection section therefore drops from 6 rows to 4 rows, giving the quick-commands panel more vertical space.
- When the user opens the Connect screen while already connected (or previously connected), the `PresetListScreen` pre-selects the active preset so the user can edit or reconnect without manually locating it.
- The `[Connect]` button in the connection form is renamed to `[Connect & Save]` and the `[Connect without saving]` button is renamed to `[Connect]`, making the primary action shorter and the save-vs-no-save distinction clearer.

## Capabilities

### New Capabilities

<!-- none — all changes are within an existing TUI module -->

### Modified Capabilities

- `terminal-tui`: UI layout of the connection info panel and the Connect-screen preset pre-selection behaviour change.

## Impact

- `ui/terminal_app.py`: layout changes to `compose()`, `_attach_client()`, `_apply_state()`, `_tick_reconnect_countdown()`, `_push_connect_screen()` / `action_open_connect()`, and button labels in `ConnectionFormScreen`.
- No changes to transport, engine, model, state, or client layers.
- No new dependencies.
