## ADDED Requirements

### Requirement: Display current projector state
The TUI SHALL display a panel showing current values for all projector commands (power, source, brightness, etc.) updated in real time when state changes.

#### Scenario: State panel shows defaults at startup
- **WHEN** the emulator starts
- **THEN** the TUI shows the default values from the loaded model

#### Scenario: State panel updates on command
- **WHEN** a SET command changes a projector value
- **THEN** the TUI state panel updates to show the new value within one UI refresh cycle

### Requirement: Display recent command log
The TUI SHALL display a scrollable log of the most recent ESC/VP21 commands received (across all transports) with timestamps and the transport they arrived on.

#### Scenario: Command logged on receipt
- **WHEN** any transport receives a command
- **THEN** the command, transport name, and timestamp appear in the log

### Requirement: Interactive power control
The TUI SHALL provide a keyboard shortcut or button to toggle projector power (PWR ON / PWR OFF) directly from the UI.

#### Scenario: Power toggle from TUI
- **WHEN** user presses the designated key (e.g. `p`)
- **THEN** PWR state toggles between `01` (on) and `00` (standby) and the state panel updates

### Requirement: Built on Textual
The TUI SHALL be implemented using the Textual framework and run as the main asyncio application. Transport servers SHALL run as background tasks within the same event loop.

#### Scenario: TUI and transports share event loop
- **WHEN** the emulator starts
- **THEN** Textual is the main application; serial, ESC/VP.net, and HTTP servers are asyncio background tasks started in `on_mount`

### Requirement: Runtime HTTP password change
The TUI SHALL provide a key binding (`w`) that opens a modal input dialog allowing the operator to change the HTTP Digest password without restarting the emulator. The modal SHALL be pre-filled with the current password. Submitting the modal (Enter) SHALL update the shared password store immediately. Cancelling (Escape) SHALL leave the password unchanged. The key binding SHALL only be advertised in the footer when authentication is enabled (i.e. when the emulator was started with `--http-password`).

#### Scenario: Password change modal opens
- **WHEN** the operator presses `w` with auth enabled
- **THEN** a modal dialog appears with a text input pre-filled with the current password

#### Scenario: Password updated on submit
- **WHEN** the operator clears the input, types a new password, and presses Enter
- **THEN** the modal is dismissed and the new password is active for all subsequent HTTP requests

#### Scenario: Password unchanged on cancel
- **WHEN** the operator presses Escape in the modal
- **THEN** the modal is dismissed and the password remains unchanged

#### Scenario: Key binding not shown when auth disabled
- **WHEN** the emulator is started without `--http-password`
- **THEN** the `w` key binding does not appear in the TUI footer and pressing `w` has no effect
