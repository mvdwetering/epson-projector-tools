## MODIFIED Requirements

### Requirement: ESC/VP21 pipe after handshake
After a successful CONNECT, the transport SHALL process incoming data identically to the serial transport: read `\r`-terminated commands, call the engine, send responses. The transport SHALL close the TCP connection if no inbound ESC/VP21 command activity is received for 600 seconds.

#### Scenario: GET command after handshake
- **WHEN** a connected ESC/VP.net client sends `PWR?\r`
- **THEN** response is `PWR=01\r:` (or current value)

#### Scenario: Client disconnects after handshake
- **WHEN** the TCP client closes the connection after handshake
- **THEN** the transport coroutine exits cleanly

#### Scenario: Idle session times out after handshake
- **WHEN** a connected ESC/VP.net client sends no command data for 600 seconds after a successful CONNECT
- **THEN** the transport closes the TCP connection and exits the session coroutine

#### Scenario: Activity before timeout keeps session open
- **WHEN** a connected ESC/VP.net client sends command data before 600 seconds elapse
- **THEN** the inactivity timer resets and the connection remains open
