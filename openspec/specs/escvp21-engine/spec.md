## MODIFIED Requirements

### Requirement: Handle null command acknowledgment
The engine SHALL treat a plain carriage-return command with no command text as a null command and return `:`.

#### Scenario: Plain carriage-return null command
- **WHEN** input is a null ESC/VP21 command containing only `\r`
- **THEN** response is `:`

### Requirement: Handle SET command
The engine SHALL update projector state for a writable command and return `:`.

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
The engine SHALL validate `KEY` command operands against the active model IR code list.

#### Scenario: Known IR key code
- **WHEN** SET `KEY <code>` uses a code present in model `irCodes`
- **THEN** response is `\r:`

#### Scenario: Unknown IR key code
- **WHEN** SET `KEY <code>` uses a code not present in model `irCodes`
- **THEN** response is `ERR\r:`
