## MODIFIED Requirements

### Requirement: Connection info panel
The left column SHALL display a connection info panel. The panel heading label SHALL read `Connection` followed by the current connection status inline, e.g. `Connection  [Connected]`, `Connection  [Disconnected]`, or `Connection  [Reconnecting… 4s]`. The status portion SHALL use colour markup (green for connected, red for disconnected, yellow for reconnecting). The panel SHALL also show: preset name (if any), protocol, and host with port combined on a single line (e.g. `Host: 192.168.1.50:3629`).

#### Scenario: Status reflects connection state
- **WHEN** the client transitions to `"reconnecting"` with `next_retry_s=4`
- **THEN** the connection header label displays `Connection  [Reconnecting… 4s]` and updates each second

#### Scenario: Status on connect
- **WHEN** the client state becomes `"connected"`
- **THEN** the connection header label displays `Connection  [Connected]` in green

#### Scenario: Status on disconnect
- **WHEN** the client state becomes `"disconnected"`
- **THEN** the connection header label displays `Connection  [Disconnected]` in red

#### Scenario: Host and port on one line
- **WHEN** a connection is established to host `192.168.1.50` on port `3629`
- **THEN** the info panel shows a single label containing `Host: 192.168.1.50:3629`

---

### Requirement: Connect dialog
The terminal SHALL provide a two-screen connection flow instead of a single modal dialog.

**Screen 1 — Preset List** is shown on startup when at least one preset exists. It displays all saved presets as selectable rows, each showing name, protocol, and host. When opened while an active preset is set, the list SHALL pre-select that preset. Key bindings: `Enter` or `c` connects to the selected preset; `n` opens Screen 2 blank (new preset); `e` opens Screen 2 pre-filled with the selected preset (edit); `d` deletes the selected preset after a confirmation prompt; `Esc`/`q` quits the application.

**Screen 2 — Connection Form** is shown on startup when no presets exist, or when navigated to from Screen 1. Fields: Name (text, optional — if blank the connection is not saved), Protocol (select: serial/vpnet/http), Host (text), Port (text, auto-filled by protocol), Password (text, hidden unless `vpnet` or `http` is selected; label reads "Password (ESC/VP.net / HTTP)"). Actions: `[Connect & Save]` saves the preset if a name is given and then connects; `[Connect]` connects without saving; `[Back]` returns to Screen 1.

#### Scenario: Preset list on startup
- **WHEN** the terminal is launched with no CLI arguments and at least one preset exists
- **THEN** Screen 1 (preset list) is shown

#### Scenario: Form on startup with no presets
- **WHEN** the terminal is launched with no CLI arguments and no presets are saved
- **THEN** Screen 2 (connection form, blank) is shown

#### Scenario: Active preset pre-selected on reconnect
- **WHEN** the user is connected via a named preset and presses `c` to reopen the connect dialog
- **THEN** Screen 1 opens with that preset highlighted in the list

#### Scenario: No pre-selection when connected without a named preset
- **WHEN** the user is connected via an unnamed (not-saved) connection and presses `c`
- **THEN** Screen 1 opens with no preset pre-selected

#### Scenario: Pre-selection gracefully handles deleted preset
- **WHEN** the active preset name no longer exists in the list (e.g. deleted externally)
- **THEN** Screen 1 opens with no preset pre-selected and no error is raised

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
- **WHEN** the user fills Screen 2 without a name and presses `[Connect]`
- **THEN** the connection is established and no preset is written

#### Scenario: Runtime reconnect
- **WHEN** the user presses `c` while connected (from the main terminal screen)
- **THEN** the existing connection is closed and Screen 1 (or Screen 2 if no presets) is shown; on connect, a new connection is established

#### Scenario: Port auto-fill
- **WHEN** the user selects "ESC/VP.net" in the protocol dropdown on Screen 2
- **THEN** the port field is automatically set to `3629`

#### Scenario: Password field hidden for serial
- **WHEN** the user selects the `serial` protocol in the connection form
- **THEN** the password field and its label are hidden

#### Scenario: Password field visible for vpnet
- **WHEN** the user selects the `vpnet` protocol in the connection form
- **THEN** the password field and its label are shown

#### Scenario: Password field visible for http
- **WHEN** the user selects the `http` protocol in the connection form
- **THEN** the password field and its label are shown
