## 1. Connection info panel — status inline with heading

- [x] 1.1 In `TerminalApp.compose()`, replace the static `Label("Connection", …)` and the `Label("Disconnected", id="status-label")` with a single `Label("Connection  [red]Disconnected[/red]", id="connection-header-label", markup=True)`
- [x] 1.2 In `_apply_state()`, update all references from `#status-label` to `#connection-header-label` and change the label text to `Connection  [green]Connected[/green]` / `Connection  [red]Disconnected[/red]` / `Connection  [yellow]Reconnecting… {n}s[/yellow]`
- [x] 1.3 In `_tick_reconnect_countdown()`, update the same label ID and text format
- [x] 1.4 Remove any CSS rule targeting `#status-label` and replace with `#connection-header-label` if needed

## 2. Connection info panel — host and port on one line

- [x] 2.1 In `TerminalApp.compose()`, remove the `Label("", id="port-label")` widget
- [x] 2.2 In `_attach_client()`, change the host label update to `f"Host:     {host}:{port}"` and remove the `query_one("#port-label")` line

## 3. Pre-select active preset in connect dialog

- [x] 3.1 Add `self._active_preset_name: str | None = None` to `TerminalApp.__init__()`
- [x] 3.2 In `_attach_client()`, set `self._active_preset_name` to the preset name from params (empty string or None when unnamed)
- [x] 3.3 Add an `initial_preset_name: str | None = None` parameter to `PresetListScreen.__init__()` and store it
- [x] 3.4 In `PresetListScreen._refresh_list()` (or `on_mount`), after populating the list, find the index of the item whose `_preset["name"]` matches `initial_preset_name` and call `lv.index = <idx>` to highlight it; do nothing if no match
- [x] 3.5 In `TerminalApp._push_connect_screen()`, pass `initial_preset_name=self._active_preset_name` when constructing `PresetListScreen`

## 4. Rename connection form buttons

- [x] 4.1 In `ConnectionFormScreen.compose()`, rename the `[Connect without saving]` button label to `[Connect]` (keep `id="btn-nosave"`)
- [x] 4.2 In `ConnectionFormScreen.compose()`, rename the `[Connect]` button label to `[Connect & Save]` (keep `id="btn-connect"`)
