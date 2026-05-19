## ADDED Requirements

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
