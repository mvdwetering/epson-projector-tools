## MODIFIED Requirements

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
