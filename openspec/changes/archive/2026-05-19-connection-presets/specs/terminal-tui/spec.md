## MODIFIED Requirements

### Requirement: Connect dialog
The terminal SHALL provide a two-screen connection flow instead of a single modal dialog.

**Screen 1 — Preset List** is shown on startup when at least one preset exists. It displays all saved presets as selectable rows, each showing name, protocol, and host. Key bindings: `Enter` or `c` connects to the selected preset; `n` opens Screen 2 blank (new preset); `e` opens Screen 2 pre-filled with the selected preset (edit); `d` deletes the selected preset after a confirmation prompt; `Esc`/`q` quits the application.

**Screen 2 — Connection Form** is shown on startup when no presets exist, or when navigated to from Screen 1. Fields: Name (text, optional — if blank the connection is not saved), Protocol (select: serial/vpnet/http), Host (text), Port (text, auto-filled by protocol), Password (text, hidden unless HTTP selected). Actions: `[Connect]` saves the preset if a name is given and then connects; `[Connect without saving]` connects without saving; `[Back]` returns to Screen 1.

#### Scenario: Preset list on startup
- **WHEN** the terminal is launched with no CLI arguments and at least one preset exists
- **THEN** Screen 1 (preset list) is shown

#### Scenario: Form on startup with no presets
- **WHEN** the terminal is launched with no CLI arguments and no presets are saved
- **THEN** Screen 2 (connection form, blank) is shown

#### Scenario: New preset flow
- **WHEN** the user presses `n` on Screen 1, fills the form with a name, and presses `[Connect]`
- **THEN** the preset is saved and the connection is established

#### Scenario: Edit preset flow
- **WHEN** the user presses `e` on Screen 1, modifies a field, and presses `[Connect]`
- **THEN** the preset is overwritten (same name, new values) and the connection is established

#### Scenario: Delete preset with confirmation
- **WHEN** the user presses `d` on Screen 1
- **THEN** a confirmation prompt is shown; on confirm the preset is deleted and the list refreshes

#### Scenario: Connect without saving
- **WHEN** the user fills Screen 2 without a name and presses `[Connect without saving]`
- **THEN** the connection is established and no preset is written

#### Scenario: Runtime reconnect
- **WHEN** the user presses `c` while connected (from the main terminal screen)
- **THEN** the existing connection is closed and Screen 1 (or Screen 2 if no presets) is shown; on connect, a new connection is established

#### Scenario: Port auto-fill
- **WHEN** the user selects "ESC/VP.net" in the protocol dropdown on Screen 2
- **THEN** the port field is automatically set to `3629`

---

### Requirement: CLI arguments
The `epson-terminal` entry point SHALL accept a single optional positional argument `preset_name`. If provided, the named preset is loaded from the presets file and the terminal connects immediately without showing any screen. If the named preset is not found, an error message is printed to stderr and the application exits with a non-zero code. If no argument is provided, the TUI launches normally (Screen 1 or Screen 2 per preset list state). All previous named flags (`--protocol`, `--host`, `--port`, `--password`, `--model`) are removed.

#### Scenario: Positional preset skips dialog
- **WHEN** `epson-terminal living-room` is run and a preset named "living-room" exists
- **THEN** the terminal connects to that preset immediately without showing any screen

#### Scenario: Unknown preset exits with error
- **WHEN** `epson-terminal unknown-preset` is run and no such preset exists
- **THEN** an error is printed to stderr and the process exits with a non-zero exit code

#### Scenario: No argument shows TUI
- **WHEN** `epson-terminal` is run with no arguments
- **THEN** the TUI launches and shows Screen 1 or Screen 2 depending on preset list state

---

### Requirement: Quick commands panel
The left column SHALL display a panel of clickable quick command buttons. The quick commands SHALL always be the hardcoded defaults: `SNO?`, `PWR?`, `PWR ON`, `PWR OFF`, `SOURCE?`. Model-driven population is removed.

#### Scenario: Default quick commands
- **WHEN** the terminal starts
- **THEN** the quick commands panel shows `SNO?`, `PWR?`, `PWR ON`, `PWR OFF`, `SOURCE?`

#### Scenario: Activating a quick command
- **WHEN** a quick command button is activated
- **THEN** its command text is inserted into the input area and sent immediately

## REMOVED Requirements

### Requirement: Model-driven quick commands
**Reason**: The model feature is removed from the terminal. There is currently only one model and it has not been used in practice. It can be reintroduced later when there is a clear need.
**Migration**: Quick commands always use the hardcoded defaults.

---

### Requirement: Model-driven input hints
**Reason**: The model feature is removed from the terminal.
**Migration**: No replacement. The hint line below the input area is removed.
