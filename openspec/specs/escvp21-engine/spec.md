## MODIFIED Requirements

### Requirement: Handle null command acknowledgment
The engine SHALL treat a plain carriage-return command with no command text as a null command and return `:`.

#### Scenario: Plain carriage-return null command
- **WHEN** input is a null ESC/VP21 command containing only `\r`
- **THEN** response is `:`

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

### Requirement: Handle source-list queries from model metadata
The engine SHALL support source-list query responses using model source metadata.

#### Scenario: SOURCELIST returns model sources
- **WHEN** `SOURCELIST?` is issued and supported by the active model
- **THEN** response is `SOURCELIST=<code1> <name1> <code2> <name2> ...\r:` built from non-cyclic model sources

#### Scenario: SOURCELISTA returns model sources
- **WHEN** `SOURCELISTA?` is issued and supported by the active model
- **THEN** response is `SOURCELISTA=<code1> <name1> <code2> <name2> ...\r:` built from the same non-cyclic model source list as `SOURCELIST`

### Requirement: Validate SOURCE against model source metadata
The engine SHALL validate `SOURCE` set operands against the active model source metadata.

#### Scenario: Known source code
- **WHEN** SET `SOURCE <code>` uses a code present in the non-cyclic model source list
- **THEN** response is `\r:` and state is updated

#### Scenario: Unknown source code
- **WHEN** SET `SOURCE <code>` uses a code not present in the non-cyclic model source list
- **THEN** response is `ERR\r:`

### Requirement: Validate KEY against model IR codes
The engine SHALL validate `KEY` command operands against the active model IR code list and SHALL apply shared key-dispatch behavior for mapped keys so behavior is consistent across HTTP, serial TCP, and ESC/VP.net transports.

#### Scenario: Known IR key code
- **WHEN** SET `KEY <code>` uses a code present in model `irCodes`
- **THEN** response is `\r:`

#### Scenario: Unknown IR key code
- **WHEN** SET `KEY <code>` uses a code not present in model `irCodes`
- **THEN** response is `ERR\r:`

#### Scenario: Source-selection key behavior is transport-independent
- **WHEN** a known source-selection `KEY <code>` is sent via HTTP, serial TCP, or ESC/VP.net
- **THEN** the engine applies the same source-selection side effect and returns identical command outcome across transports

#### Scenario: Volume increment key behavior is transport-independent
- **WHEN** mapped `KEY <inc-code>` is sent via HTTP, serial TCP, or ESC/VP.net and maps to `VOL INC`
- **THEN** the engine increments volume by one step within command limits and returns `\r:`

#### Scenario: Volume decrement key behavior is transport-independent
- **WHEN** mapped `KEY 57` is sent via HTTP, serial TCP, or ESC/VP.net and maps to `VOL DEC`
- **THEN** the engine decrements volume by one step within command limits and returns `\r:`
