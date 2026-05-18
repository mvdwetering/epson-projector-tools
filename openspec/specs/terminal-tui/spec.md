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
The left column SHALL display a panel of clickable/keyboard-activatable quick command buttons.

When no model is loaded, the hardcoded defaults SHALL be: `SNO?`, `PWR?`, `PWR 01`, `PWR 02`, `SOURCE?`.

When a model is loaded, the quick commands SHALL be populated from the model's commands where `readable=True`, replacing the hardcoded defaults.

#### Scenario: Default quick commands without model
- **WHEN** the terminal starts without `--model`
- **THEN** the quick commands panel shows `SNO?`, `PWR?`, `PWR 01`, `PWR 02`, `SOURCE?`

#### Scenario: Model-driven quick commands
- **WHEN** the terminal starts with `--model models/eh_tw3200.yaml`
- **THEN** the quick commands panel shows GET commands derived from the model's readable commands

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
The terminal SHALL provide a connect dialog (opened on startup if args are incomplete, or via `c` key at any time) with fields: Protocol (select), Host (text), Port (text, auto-filled by protocol), Password (text, shown only for HTTP), Model path (text, optional for all protocols).

#### Scenario: Dialog auto-fills port
- **WHEN** the user selects "ESC/VP.net" in the protocol dropdown
- **THEN** the port field is automatically set to `3629`

#### Scenario: Dialog on startup without args
- **WHEN** the terminal is launched without sufficient CLI args
- **THEN** the connect dialog is shown before any connection is attempted

#### Scenario: Runtime connection switch
- **WHEN** the user presses `c` while connected
- **THEN** the existing connection is closed and the connect dialog is shown; on submit, a new connection is established

---

### Requirement: CLI arguments
The `epson-terminal` entry point SHALL accept: `--protocol` (serial/vpnet/http), `--host`, `--port`, `--password` (HTTP only), `--model` (optional path to YAML). If all required args for the protocol are present, the connect dialog is skipped.

#### Scenario: Full CLI args skip dialog
- **WHEN** `epson-terminal --protocol vpnet --host 192.168.1.50 --port 3629` is run
- **THEN** the terminal connects immediately without showing the connect dialog

#### Scenario: Partial CLI args show dialog
- **WHEN** `epson-terminal --protocol http` is run without `--host`
- **THEN** the connect dialog opens with "http" pre-selected

---

### Requirement: Model-driven input hints
When a model is loaded, the terminal SHALL display inline hints in a status line below the input: range, accepted set values, or set_map keys for the command currently being typed.

#### Scenario: Range hint
- **WHEN** the user has typed `BRIGHT ` (command name + space) and the model defines `range: [0, 100]`
- **THEN** a status line shows `BRIGHT — range: 0–100`

#### Scenario: Set values hint
- **WHEN** the user has typed `CMODE ` and the model defines `set_values: ["00","01","02"]`
- **THEN** a status line shows `CMODE — values: 00, 01, 02`

#### Scenario: Unknown command warning
- **WHEN** the user types a command name not present in the loaded model
- **THEN** the command text is highlighted in a warning style (e.g. yellow); it is still sendable
