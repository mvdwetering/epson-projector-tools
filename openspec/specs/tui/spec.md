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

### Requirement: Power key cycles through all power states instantly
The emulator TUI `p` keybinding SHALL advance `PWR` to the next state in the cycle — `00`/`04` → `02` → `01` → `03` → `00`/`04` — immediately, without waiting for warmup or cooldown delays. Any in-flight sequencer transition SHALL be cancelled before applying the instant state change.

#### Scenario: Advance from standby to warmup
- **WHEN** operator presses `p` and current `PWR` is `00` or `04`
- **THEN** `PWR` is set to `02` immediately

#### Scenario: Advance from warmup to normal
- **WHEN** operator presses `p` and current `PWR` is `02`
- **THEN** `PWR` is set to `01` immediately

#### Scenario: Advance from normal to cooldown
- **WHEN** operator presses `p` and current `PWR` is `01`
- **THEN** `PWR` is set to `03` immediately

#### Scenario: Advance from cooldown to standby
- **WHEN** operator presses `p` and current `PWR` is `03`
- **THEN** `PWR` is set to `00` or `04` (model's standby state) immediately

#### Scenario: In-flight sequencer task cancelled on key press
- **WHEN** operator presses `p` while a sequencer transition is running
- **THEN** the in-flight task is cancelled before the instant state change is applied

### Requirement: In-flight transition cancelled on model reload
The emulator TUI SHALL cancel any in-flight `PowerSequencer` transition before replacing state and model on a model switch.

#### Scenario: Transition cancelled before model reload
- **WHEN** the operator triggers a model switch while a warmup or cooldown is in progress
- **THEN** the sequencer is cancelled before state is replaced, preventing stale `PWR` writes after reload
