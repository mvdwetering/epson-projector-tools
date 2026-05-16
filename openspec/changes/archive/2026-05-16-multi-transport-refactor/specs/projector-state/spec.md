## ADDED Requirements

### Requirement: Store projector values
ProjectorState SHALL maintain a key-value store of command names to their current string values, initialised from the active model's defaults.

#### Scenario: Get existing value
- **WHEN** `get(command)` is called for a known command
- **THEN** the current value is returned

#### Scenario: Get unknown value
- **WHEN** `get(command)` is called for an unknown command
- **THEN** `None` is returned

### Requirement: Update projector values
ProjectorState SHALL allow updating a command's value and SHALL notify registered observers.

#### Scenario: Set known value
- **WHEN** `set(command, value)` is called for a known command
- **THEN** the value is stored and all observers are notified

#### Scenario: Set unknown value
- **WHEN** `set(command, value)` is called for an unknown command
- **THEN** the value is rejected (returns False) and no observers are notified

### Requirement: Observer registration
ProjectorState SHALL allow observers (e.g. the TUI) to register a callback that is invoked on any state change.

#### Scenario: Observer notified on change
- **WHEN** a value is updated via `set()`
- **THEN** all registered observer callbacks are called with the command name and new value

### Requirement: Shared across transports
A single ProjectorState instance SHALL be shared by all active transports so all connections see and modify the same state.

#### Scenario: Change from one transport visible to another
- **WHEN** a SET command changes state via the serial transport
- **THEN** a subsequent GET via the ESC/VP.net transport returns the updated value
