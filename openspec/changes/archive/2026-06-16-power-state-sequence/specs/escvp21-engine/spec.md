## MODIFIED Requirements

### Requirement: Handle SET command
The engine SHALL update projector state for a writable command and return `:`. For `PWR ON` and `PWR OFF`, the engine SHALL delegate to the `PowerSequencer` when one is provided, rejecting commands that are not valid in the current power state.

#### Scenario: Valid SET
- **WHEN** SET is issued for a writable command with an accepted value
- **THEN** state is updated and response is `:`

#### Scenario: INC/DEC on decimal single-parameter command
- **WHEN** SET value is `INC` or `DEC` for a command marked INC/DEC-capable and that command is a single-parameter decimal adjustment command
- **THEN** state value is incremented or decremented by 1 within its range and response is `:`

#### Scenario: INC/DEC rejected for non-decimal or complex command
- **WHEN** SET value is `INC` or `DEC` for a command that is not a single-parameter decimal adjustment command (for example mixed/multi-parameter commands)
- **THEN** response is `ERR\r:`

#### Scenario: Unknown or unwritable command
- **WHEN** SET is issued for a command not in the model, or not writable
- **THEN** response is `ERR\r:`

#### Scenario: PWR ON accepted when in standby
- **WHEN** `PWR ON` is issued and a `PowerSequencer` is active and current `PWR` is `00` or `04`
- **THEN** response is `\r:` and the sequencer begins the warmup transition

#### Scenario: PWR OFF accepted when lamp is on
- **WHEN** `PWR OFF` is issued and a `PowerSequencer` is active and current `PWR` is `01`
- **THEN** response is `\r:` and the sequencer begins the cooldown transition

#### Scenario: PWR ON rejected during transition
- **WHEN** `PWR ON` is issued and a `PowerSequencer` is active and current `PWR` is `02` or `03`
- **THEN** response is `ERR\r:`

#### Scenario: PWR OFF rejected during transition
- **WHEN** `PWR OFF` is issued and a `PowerSequencer` is active and current `PWR` is `02` or `03`
- **THEN** response is `ERR\r:`

#### Scenario: PWR command without sequencer retains synchronous behaviour
- **WHEN** `PWR ON` or `PWR OFF` is issued and no `PowerSequencer` is provided to the engine
- **THEN** state is updated immediately and response is `\r:`
