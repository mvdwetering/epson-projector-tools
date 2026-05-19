## Context

The terminal currently uses a single `ConnectDialog` modal and a set of named CLI flags (`--protocol`, `--host`, `--port`, `--password`, `--model`). Users who work with a fixed set of projectors must re-enter connection details on every launch. There is no persistence layer for connection information. The model-loading feature exists in both `terminal.py` and `TerminalApp` but has no practical use with the current single-model codebase.

## Goals / Non-Goals

**Goals:**
- Persist named presets to a cross-platform config file.
- Replace the single connect dialog with a two-screen TUI flow: preset list → connection form.
- Allow connecting via `terminal.py <preset_name>` without any interactive dialog.
- Remove the model feature entirely from the terminal.
- Remove all individual connection CLI flags.

**Non-Goals:**
- Password encryption or OS keychain integration (plaintext YAML is acceptable for a local dev tool).
- Remote/shared preset storage.
- Re-introducing the model feature; it can be added separately when there is a concrete need.

## Decisions

### D1 — Preset storage: `platformdirs` + YAML

`platformdirs.user_config_dir("epson_terminal")` resolves to the correct per-user config directory on Linux (`~/.config/epson_terminal/`), macOS (`~/Library/Application Support/epson_terminal/`), and Windows (`%APPDATA%\Local\epson_terminal\`). Presets are stored as a plain YAML file (`presets.yaml`) — human-readable and easy to hand-edit.

Alternative considered: `~/.epson_terminal_presets.yaml` — simpler but clutters `$HOME` and doesn't follow platform conventions.

### D2 — Preset schema

```yaml
presets:
  - name: living-room
    protocol: vpnet
    host: 192.168.1.50
    port: 3629
    password: ""
  - name: office-http
    protocol: http
    host: 192.168.1.52
    port: 8080
    password: secret
```

A flat ordered list. Order is preserved; the user can hand-edit to reorder. Name is the unique key — saving with an existing name overwrites that entry.

### D3 — Two-screen TUI flow

**Screen 1 — Preset List** (default on launch when presets exist, or immediately shows Screen 2 when list is empty):
- Shows all presets as selectable rows with protocol and host summary.
- Keys: `Enter`/`c` = connect, `n` = new (goes to Screen 2 blank), `e` = edit selected (goes to Screen 2 pre-filled), `d` = delete selected (with confirmation), `Esc`/`q` = quit.

**Screen 2 — Connection Form** (also used for edit):
- Fields: Name, Protocol, Host, Port, Password.
- Buttons / keys: `[Connect]` = save preset (if name given) then connect; `[Connect without saving]` = connect without saving; `[Back]` = return to list.
- Port auto-updates when protocol changes (same behaviour as current dialog).
- Password field hidden unless HTTP selected.

This replaces `ConnectDialog` entirely.

### D4 — CLI positional argument

```
terminal.py [preset_name]
```

If `preset_name` is provided: load preset, skip all screens, connect immediately.
If `preset_name` is omitted: launch TUI; show Screen 1 (preset list) if presets exist, Screen 2 (blank form) otherwise.

All of `--protocol`, `--host`, `--port`, `--password`, `--model` are removed.

### D5 — Preset I/O module location

New file `client/presets.py` — lives alongside the other client modules. Exposes:
- `load_presets() -> list[dict]`
- `save_presets(presets: list[dict]) -> None`
- `find_preset(name: str) -> dict | None`

## Risks / Trade-offs

- **Plaintext passwords** → Acceptable for a local dev tool. Documented in README.
- **YAML hand-edit errors** → `load_presets()` will catch parse errors and return an empty list with a warning rather than crashing.
- **Name collision on save** → Overwrite in-place (preserving list order for that entry). This is the intended "edit" behaviour.
- **`platformdirs` new dependency** → Small, stable, widely used library. Risk is negligible.
