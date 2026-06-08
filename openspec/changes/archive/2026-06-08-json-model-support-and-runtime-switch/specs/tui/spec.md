## MODIFIED Requirements

### Requirement: Display current projector state
The TUI SHALL display a panel showing current values for projector commands, ordered for operator visibility as pinned commands first, then recent activity, then alphabetical remainder.

Pinned commands are `PWR`, `SOURCE`, `SNO`, `LAMP`, and `KEY` (when present in the model).
Recent activity section SHALL contain up to 6 commands.

#### Scenario: Pinned commands appear first
- **WHEN** the emulator starts with a model that includes pinned commands
- **THEN** pinned commands are rendered at the top of the state table in fixed order

#### Scenario: Recent commands float above alphabetical remainder
- **WHEN** non-pinned commands are queried or set
- **THEN** up to 6 most recent active commands appear below pinned commands and above alphabetical remainder without duplicates

### Requirement: Display runtime transport configuration
The TUI SHALL display runtime transport rows in the configuration panel with inline support indicators and no extra warning rows.

#### Scenario: Unsupported transport indicated inline
- **WHEN** active model metadata marks a transport capability as unsupported
- **THEN** the corresponding transport row includes an inline unsupported indicator on the same line

#### Scenario: Unknown capability treated as supported
- **WHEN** model connectivity capability is unknown (`null`)
- **THEN** no unsupported indicator is shown for that transport

#### Scenario: Config panel remains compact
- **WHEN** unsupported indicators are shown
- **THEN** no additional configuration-panel rows are added for warnings

### Requirement: Runtime model switching
The emulator TUI SHALL provide runtime model selection and apply model changes using a safe restart sequence.

#### Scenario: Switch model from UI
- **WHEN** an operator selects a different JSON model in the TUI
- **THEN** the app stops transports, reloads model and state, rebuilds state/config views, restarts transports, and updates the title using filename or model name

#### Scenario: Behavior after switch
- **WHEN** model switch completes
- **THEN** command handling and displayed state reflect the newly selected model defaults and metadata