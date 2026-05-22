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
The TUI SHALL display a scrollable log of the most recent ESC/VP21 commands received (across all transports) with timestamps formatted as `HH:MM:SS.mmm` and the transport they arrived on.

#### Scenario: Command logged on receipt
- **WHEN** any transport receives a command
- **THEN** the command, transport name, and millisecond-precision timestamp appear in the log

#### Scenario: Closely spaced commands remain distinguishable
- **WHEN** multiple commands are received within the same second
- **THEN** their log entries preserve millisecond precision so operators can distinguish the event order within that second

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

### Requirement: Display runtime transport configuration
The TUI SHALL display a dedicated configuration panel that shows the emulator's current transport configuration for the active process.

#### Scenario: Configuration panel visible at startup
- **WHEN** the emulator TUI is launched
- **THEN** a configuration panel is visible without requiring user interaction

#### Scenario: Configuration panel appears before state panel
- **WHEN** the emulator TUI is launched
- **THEN** the configuration panel is rendered above the state panel in the left column

### Requirement: Display configured transport ports
The configuration panel SHALL show the configured listening port for each transport: Serial TCP, ESC/VP.net, and HTTP.

#### Scenario: Panel shows startup ports
- **WHEN** the emulator is started with explicit port arguments
- **THEN** the panel displays those exact serial, ESC/VP.net, and HTTP port values

#### Scenario: Panel shows default ports
- **WHEN** the emulator is started without overriding transport ports
- **THEN** the panel displays the default serial, ESC/VP.net, and HTTP port values used by the process

### Requirement: Display password-required status
The configuration panel SHALL show whether password authentication is required for transports that support password protection, without revealing password values.

#### Scenario: HTTP auth required
- **WHEN** the emulator is started with HTTP password authentication configured
- **THEN** the panel shows HTTP authentication as required

#### Scenario: HTTP auth not required
- **WHEN** the emulator is started without HTTP password authentication configured
- **THEN** the panel shows HTTP authentication as not required

#### Scenario: Password value never shown
- **WHEN** authentication is configured for any transport
- **THEN** the configuration panel does not display plaintext or masked password content
