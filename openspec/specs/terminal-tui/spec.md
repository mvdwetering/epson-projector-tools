## ADDED Requirements

### Requirement: Two-column layout
The terminal TUI SHALL use a two-column layout: left column contains the connection info panel, quick commands panel, and command input area; right column contains the scrolling command log.

#### Scenario: Layout renders
- **WHEN** the terminal is started
- **THEN** the left column is visible with connection info, quick commands, and input; the right column shows the command log

---

### Requirement: Connection info panel
The left column SHALL display a connection info panel showing: protocol (Serial TCP / ESC/VP.net / HTTP), host, port (or URL for HTTP), and current connection status (Connected / Disconnected / Reconnecting with countdown).

#### Scenario: Status reflects connection state
- **WHEN** the client transitions to `"reconnecting"` with `next_retry_s=4`
- **THEN** the status field displays "Reconnecting… 4s" and updates each second

#### Scenario: Status on connect
- **WHEN** the client state becomes `"connected"`
- **THEN** the status field displays "Connected"

---

### Requirement: Quick commands panel
The left column SHALL display a panel of clickable quick command buttons. The quick commands SHALL always be the hardcoded defaults: `SNO?`, `PWR?`, `PWR ON`, `PWR OFF`, `SOURCE?`.

#### Scenario: Default quick commands
- **WHEN** the terminal starts
- **THEN** the quick commands panel shows `SNO?`, `PWR?`, `PWR ON`, `PWR OFF`, `SOURCE?`

#### Scenario: Activating a quick command
- **WHEN** a quick command button is activated
- **THEN** its command text is inserted into the input area and sent immediately

---

### Requirement: Multiline command input
The left column SHALL contain a `TextArea` for command input. Multiple lines are treated as sequential commands. `Ctrl+Enter` (and `F5` as alternate) SHALL send all lines sequentially. Each line is sent only after the previous command's response is received.

#### Scenario: Single command send
- **WHEN** the user types `SNO?` and presses `Ctrl+Enter`
- **THEN** `SNO?` is sent, the response appears in the log, and the input is cleared

#### Scenario: Multiline sequential send
- **WHEN** the user types three lines (`PWR?`, `SOURCE?`, `MUTE?`) and presses `Ctrl+Enter`
- **THEN** `PWR?` is sent; after its response is received, `SOURCE?` is sent; after its response, `MUTE?` is sent; all three appear grouped in the log

#### Scenario: Batch continues on ERR
- **WHEN** a multiline batch contains a command that returns `ERR`
- **THEN** subsequent commands in the batch are still sent

---

### Requirement: In-session command history
The terminal SHALL maintain a list of previously submitted text blocks (entire TextArea contents at send time) for the current session. `Up`/`Down` arrow keys in the input area SHALL cycle through history entries and populate the TextArea.

#### Scenario: History navigation
- **WHEN** the user presses `Up` after having sent two previous commands
- **THEN** the TextArea is populated with the most recent previous input

#### Scenario: History not persisted
- **WHEN** the terminal is restarted
- **THEN** the history is empty

---

### Requirement: Command log with timestamps and durations
The right column SHALL display a scrolling log. Each entry shows: timestamp (HH:MM:SS.mmm), the command sent, the response received, and the duration in milliseconds. Multi-command batches SHALL be visually grouped.

#### Scenario: Single command log entry
- **WHEN** `SNO?` is sent and `SNO=LPKB3G001K\r:` is received after 42 ms
- **THEN** the log shows `14:21:03.412  SNO?  →  SNO=LPKB3G001K  [42 ms]`

#### Scenario: ERR response highlighted
- **WHEN** a command receives an `ERR` response
- **THEN** the log entry for that command is displayed in a distinct style (e.g. red)

#### Scenario: Batch group in log
- **WHEN** a batch of 3 commands is sent
- **THEN** the log shows a group header followed by the 3 individual entries, each with its own duration

---

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

### Requirement: Log filename label in command log panel
The command log panel SHALL display the full path of the current log file below the panel header. The label SHALL wrap when the panel is narrow so the full path is always visible and selectable. When no log file is open, the label SHALL be empty (hidden).

#### Scenario: Label shown when log is active
- **WHEN** a connection is established and a log file has been created
- **THEN** the command log panel shows the full log file path (e.g. `/home/user/.config/epson_terminal/logs/2026-05-19T14-32-00_vpnet_living-room.log`) below the "Command log" header

#### Scenario: Label hidden before connection
- **WHEN** the terminal is on the preset list or connection form screen
- **THEN** no log filename label is visible in the command log panel

#### Scenario: Label wraps on narrow window
- **WHEN** the terminal window is made narrow
- **THEN** the log path label wraps to multiple lines rather than being clipped

#### Scenario: Label updates on connection change
- **WHEN** the user switches to a different connection
- **THEN** the log filename label updates to reflect the new session's log file
