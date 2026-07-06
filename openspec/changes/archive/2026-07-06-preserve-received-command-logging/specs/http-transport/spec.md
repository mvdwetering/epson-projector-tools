## MODIFIED Requirements

### Requirement: directsend KEY endpoint
The HTTP transport SHALL implement IR KEY commands via `GET /cgi-bin/directsend?KEY=<ir_code>`. IR codes with known VP21 equivalents SHALL be translated to state changes. Navigation and menu keys SHALL be passed to the engine as `KEY <code>` (notify_only). Unknown IR codes that cannot be handled SHALL raise an exception. Command logging for KEY requests SHALL always record the received command (`KEY <ir_code>`), even when execution is delegated to an internal mapped VP21 command.

Source-selection key mappings SHALL remain unchanged from existing behavior.
The transport SHALL preserve received-command logging for KEY requests while shared engine semantics apply mapped effects, including `VOL INC`/`VOL DEC` behavior.

#### Scenario: Power toggle
- **WHEN** `GET /cgi-bin/directsend?KEY=3B` is received
- **THEN** if PWR is `01` it becomes `00`; if `00` it becomes `01`; server returns HTTP 200

#### Scenario: Power OFF
- **WHEN** `GET /cgi-bin/directsend?KEY=6C` is received
- **THEN** PWR is set to `00`; server returns HTTP 200

#### Scenario: Mute toggle
- **WHEN** `GET /cgi-bin/directsend?KEY=3E` is received
- **THEN** MUTE flips between `ON` and `OFF`; server returns HTTP 200

#### Scenario: Source select via IR key
- **WHEN** `GET /cgi-bin/directsend?KEY=4D` (HDMI1) is received
- **THEN** SOURCE is set to `30`; server returns HTTP 200

#### Scenario: Volume increment via IR key
- **WHEN** `GET /cgi-bin/directsend?KEY=<inc-code>` is received and maps to `VOL INC`
- **THEN** volume increases by one step (within command limits) and server returns HTTP 200

#### Scenario: Volume decrement via IR key
- **WHEN** `GET /cgi-bin/directsend?KEY=57` is received and maps to `VOL DEC`
- **THEN** volume decreases by one step (within command limits) and server returns HTTP 200

#### Scenario: Navigation key
- **WHEN** `GET /cgi-bin/directsend?KEY=3C` (Menu) is received
- **THEN** the engine processes it as notify_only and the server returns HTTP 200

#### Scenario: Mapped KEY logs received command
- **WHEN** `GET /cgi-bin/directsend?KEY=40` is received and mapped internally to `SOURCE A0`
- **THEN** the command log records `KEY 40` as the command and still applies SOURCE `A0`

#### Scenario: Unhandled IR code
- **WHEN** an IR code with no known mapping and no model KEY command match is received
- **THEN** the server raises an exception resulting in HTTP 400 or 500
