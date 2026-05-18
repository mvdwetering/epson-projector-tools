## ADDED Requirements

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
