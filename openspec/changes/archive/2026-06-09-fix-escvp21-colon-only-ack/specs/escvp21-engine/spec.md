## ADDED Requirements

### Requirement: Handle null command acknowledgment
The engine SHALL treat a plain carriage-return command with no command text as a null command and return `:`.

#### Scenario: Plain carriage-return null command
- **WHEN** input is a null ESC/VP21 command containing only `\r`
- **THEN** response is `:`

## MODIFIED Requirements

### Requirement: Handle SET command
The engine SHALL update projector state for a writable command and return `:` on successful SET operations.

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
