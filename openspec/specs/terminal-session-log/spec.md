## ADDED Requirements

### Requirement: Per-session log file creation
When a connection is established, the terminal SHALL create a new log file in `~/.config/epson_terminal/logs/`. A new file SHALL be created on app startup (when a client is provided) and each time the user switches to a different connection. Reconnects to the same connection SHALL continue writing to the same file.

#### Scenario: New file on startup with preset
- **WHEN** the terminal is launched with a CLI preset argument
- **THEN** a new log file is created in `~/.config/epson_terminal/logs/` before the first log line is written

#### Scenario: New file on connection change
- **WHEN** the user switches to a different connection via the connect dialog
- **THEN** the previous log file is closed and a new log file is created for the new connection

#### Scenario: Reconnect continues same file
- **WHEN** the client disconnects and automatically reconnects to the same host
- **THEN** all log lines (including the disconnect and reconnect system messages) are appended to the existing log file

#### Scenario: Logs directory created automatically
- **WHEN** the logs directory does not exist and a connection is established
- **THEN** the directory is created before the file is opened

---

### Requirement: Log file naming
Log files SHALL be named using the pattern `<YYYY-MM-DD>T<HH-MM-SS>_<protocol>_<slug>.log` where:
- `<YYYY-MM-DD>T<HH-MM-SS>` is the ISO 8601 date and time at session start (colons replaced with hyphens for filesystem compatibility)
- `<protocol>` is one of `serial`, `vpnet`, or `http`
- `<slug>` is the preset name when available, or `<host>-<port>` for unsaved connections; characters unsafe on common filesystems SHALL be replaced with `-`

#### Scenario: Named preset filename
- **WHEN** the user connects using a preset named "living-room" via vpnet
- **THEN** the log file is named `2026-05-19T14-32-00_vpnet_living-room.log` (with the actual session timestamp)

#### Scenario: Unsaved connection filename
- **WHEN** the user connects to `192.168.1.50:3629` via vpnet without saving a preset
- **THEN** the log file is named `2026-05-19T14-32-00_vpnet_192.168.1.50-3629.log`

#### Scenario: HTTP protocol in filename
- **WHEN** the user connects via HTTP
- **THEN** the log file name contains `_http_` as the protocol segment

---

### Requirement: Log file contents
The log file SHALL contain every line written to the TUI command log widget, including command/response entries and system messages (connection attempts, errors, reconnect events). Each line SHALL use the same millisecond-precision timestamp format as the TUI display (`HH:MM:SS.mmm`). Lines SHALL be separated by newlines. The file SHALL be flushed after every line so that data is not lost on crash.

#### Scenario: Command entry in file
- **WHEN** `SNO?` is sent and `SNO=LPKB3G001K` is received after 42 ms
- **THEN** the log file contains a line matching `HH:MM:SS.mmm  SNO?  ->  SNO=LPKB3G001K  [42 ms]`

#### Scenario: System message in file
- **WHEN** the connection fails
- **THEN** the log file contains a line with the failure message prefixed by `>>` (e.g. `14:32:01.003  >> Connection failed: …`)

#### Scenario: File readable after crash
- **WHEN** the terminal process is killed mid-session
- **THEN** the log file contains all lines written before the kill (no buffered lines lost)

---

### Requirement: Log file closed on exit
The log file SHALL be closed cleanly when the terminal application exits or when a new connection session begins.

#### Scenario: Clean close on quit
- **WHEN** the user quits the terminal
- **THEN** the log file is closed before the process exits

#### Scenario: Close before new session
- **WHEN** the user switches connection
- **THEN** the previous log file is closed before the new file is opened

---

### Requirement: Silent failure on write error
If the log file cannot be created or written (e.g. read-only filesystem), the terminal SHALL continue operating normally. The failure SHALL be reported as a single system message in the TUI command log; subsequent log lines SHALL not attempt further file writes for that session.

#### Scenario: Read-only filesystem
- **WHEN** the logs directory is not writable
- **THEN** the TUI shows a system message indicating the log file could not be created, and the terminal continues accepting commands
