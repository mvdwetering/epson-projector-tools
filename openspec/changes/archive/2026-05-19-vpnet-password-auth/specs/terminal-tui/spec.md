## MODIFIED Requirements

### Requirement: Startup screens and navigation
The terminal TUI SHALL provide two named screens for connection management.

**Screen 1 — Preset List** is shown on startup when at least one preset exists. It displays all saved presets as selectable rows, each showing name, protocol, and host. Key bindings: `Enter` or `c` connects to the selected preset; `n` opens Screen 2 blank (new preset); `e` opens Screen 2 pre-filled with the selected preset (edit); `d` deletes the selected preset after a confirmation prompt; `Esc`/`q` quits the application.

**Screen 2 — Connection Form** is shown on startup when no presets exist, or when navigated to from Screen 1. Fields: Name (text, optional — if blank the connection is not saved), Protocol (select: serial/vpnet/http), Host (text), Port (text, auto-filled by protocol), Password (text, hidden unless `vpnet` or `http` is selected; label reads "Password (ESC/VP.net / HTTP)"). Actions: `[Connect]` saves the preset if a name is given and then connects; `[Connect without saving]` connects without saving; `[Back]` returns to Screen 1.

#### Scenario: Preset list on startup
- **WHEN** the terminal is launched with no CLI arguments and at least one preset exists
- **THEN** Screen 1 (preset list) is shown

#### Scenario: Form on startup with no presets
- **WHEN** the terminal is launched with no CLI arguments and no presets are saved
- **THEN** Screen 2 (connection form, blank) is shown

#### Scenario: New preset flow
- **WHEN** the user fills in Screen 2 with a name, protocol, host, port, and optional password, then presses `[Connect]`
- **THEN** the preset is saved and the connection is established

#### Scenario: Edit preset flow
- **WHEN** the user selects a preset on Screen 1, presses `e`, modifies fields, and presses `[Connect]`
- **THEN** the preset is overwritten (same name, new values) and the connection is established

#### Scenario: Delete preset with confirmation
- **WHEN** the user selects a preset and presses `d`
- **THEN** a confirmation prompt is shown; on confirm the preset is deleted and the list refreshes

#### Scenario: Connect without saving
- **WHEN** the user fills in Screen 2 and presses `[Connect without saving]`
- **THEN** the connection is established and no preset is written

#### Scenario: Reconnect from within session
- **WHEN** the user presses `Ctrl+O` or `c` during an active session
- **THEN** the existing connection is closed and Screen 1 (or Screen 2 if no presets) is shown; on connect, a new connection is established

#### Scenario: Password field hidden for serial
- **WHEN** the user selects the `serial` protocol in the connection form
- **THEN** the password field and its label are hidden

#### Scenario: Password field visible for vpnet
- **WHEN** the user selects the `vpnet` protocol in the connection form
- **THEN** the password field and its label are shown

#### Scenario: Password field visible for http
- **WHEN** the user selects the `http` protocol in the connection form
- **THEN** the password field and its label are shown
