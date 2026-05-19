## 1. Dependencies & Preset Module

- [x] 1.1 Add `platformdirs` to `pyproject.toml` dependencies
- [x] 1.2 Create `client/presets.py` with `load_presets()`, `save_preset()`, `delete_preset()`, `find_preset()` and YAML file I/O using `platformdirs`

## 2. Remove Model Feature from Terminal

- [x] 2.1 Remove `--model` CLI argument and model-loading logic from `terminal.py`
- [x] 2.2 Remove `model` parameter from `TerminalApp.__init__` and all usages in `ui/terminal_app.py`
- [x] 2.3 Simplify `_populate_quick_commands()` to always use `_DEFAULT_QUICK_CMDS` (remove model-driven branch)
- [x] 2.4 Remove model input hint logic (hint label, `_update_hint()` or equivalent) from `TerminalApp`

## 3. Remove Old Connect Dialog & CLI Flags

- [x] 3.1 Remove `ConnectDialog` class from `ui/terminal_app.py`
- [x] 3.2 Remove `--protocol`, `--host`, `--port`, `--password` CLI arguments from `terminal.py`
- [x] 3.3 Remove `_build_client()` and `_args_sufficient()` helpers from `terminal.py`
- [x] 3.4 Remove `initial_params` parameter from `TerminalApp.__init__` and the info-panel pre-fill logic

## 4. Preset List Screen

- [x] 4.1 Implement `PresetListScreen` (Textual `Screen`) showing preset rows with name, protocol, host summary
- [x] 4.2 Add `Enter`/`c` binding on `PresetListScreen` to connect to selected preset
- [x] 4.3 Add `n` binding to push `ConnectionFormScreen` (blank)
- [x] 4.4 Add `e` binding to push `ConnectionFormScreen` pre-filled with selected preset
- [x] 4.5 Add `d` binding with confirmation prompt; on confirm call `delete_preset()` and refresh list
- [x] 4.6 Handle empty-list state: show a prompt directing the user to press `n`

## 5. Connection Form Screen

- [x] 5.1 Implement `ConnectionFormScreen` (Textual `Screen`) with Name, Protocol, Host, Port, Password fields
- [x] 5.2 Auto-fill Port when Protocol select changes (serial=12345, vpnet=3629, http=80)
- [x] 5.3 Show/hide Password field based on protocol selection (visible only for HTTP)
- [x] 5.4 Implement `[Connect]` action: save preset via `save_preset()` if name non-empty, then dismiss with connection params
- [x] 5.5 Implement `[Connect without saving]` action: dismiss with connection params, no save
- [x] 5.6 Implement `[Back]` action: return to `PresetListScreen`
- [x] 5.7 Pre-fill all fields when screen is opened in edit mode

## 6. Wire Screens into TerminalApp

- [x] 6.1 On startup (no preset arg): push `PresetListScreen` if presets exist, else push `ConnectionFormScreen`
- [x] 6.2 On `c` key (runtime reconnect): close current connection, push `PresetListScreen` (or `ConnectionFormScreen` if empty)
- [x] 6.3 On screen dismiss with connection params: build client, call `_attach_client()`, start connect task
- [x] 6.4 Update connection info panel labels from preset/form params after connect

## 7. CLI Positional Argument

- [x] 7.1 Replace all named connection flags with a single optional positional `preset_name` argument in `terminal.py`
- [x] 7.2 If `preset_name` provided: load preset via `find_preset()`, exit with error if not found, else connect directly skipping TUI screens
- [x] 7.3 If no argument: launch TUI normally (step 6.1 flow)
