## ADDED Requirements

### Requirement: Parse ESC/VP21 command line
The engine SHALL parse a raw command string into a structured command with a name and optional value.
A line ending with `?` is a GET. A line with a space separating name and value is a SET. A blank line is a null command.

#### Scenario: Parse GET command
- **WHEN** input is `PWR?`
- **THEN** result is command name `PWR`, value `None`

#### Scenario: Parse SET command
- **WHEN** input is `SOURCE 30`
- **THEN** result is command name `SOURCE`, value `30`

#### Scenario: Parse null command
- **WHEN** input is an empty string
- **THEN** result is a null command

#### Scenario: Unrecognised format
- **WHEN** input does not match GET or SET format
- **THEN** engine SHALL return an ERR response

### Requirement: Handle GET command
The engine SHALL return the current value for a readable command in the format `CMD=value\r:`.

#### Scenario: Known readable command
- **WHEN** GET is issued for a command that exists in the model and has a current value
- **THEN** response is `CMD=value\r:`

#### Scenario: Unknown or unreadable command
- **WHEN** GET is issued for a command not in the model, or not readable
- **THEN** response is `ERR\r:`

### Requirement: Handle SET command
The engine SHALL update projector state for a writable command and return `:`.

#### Scenario: Valid SET
- **WHEN** SET is issued for a writable command with an accepted value
- **THEN** state is updated and response is `\r:`

#### Scenario: INC/DEC on numeric command
- **WHEN** SET value is `INC` or `DEC` for a command with `inc_dec: true`
- **THEN** state value is incremented or decremented by 1 within its range and response is `\r:`

#### Scenario: Unknown or unwritable command
- **WHEN** SET is issued for a command not in the model, or not writable
- **THEN** response is `ERR\r:`

### Requirement: Handle null command
The engine SHALL respond to a null command with `\r:`.

#### Scenario: Null command heartbeat
- **WHEN** a blank line is received
- **THEN** response is `\r:`

### Requirement: Engine has no I/O
The engine SHALL operate as a pure function: given state, model, and command string, it returns a response string without performing any network I/O.

#### Scenario: No side effects beyond state mutation
- **WHEN** engine processes any command
- **THEN** only the shared ProjectorState is mutated; no sockets, files, or threads are touched
