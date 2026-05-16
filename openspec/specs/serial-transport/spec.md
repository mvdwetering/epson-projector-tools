## ADDED Requirements

### Requirement: Accept TCP connections on serial port
The serial transport SHALL listen for TCP connections on port 12345 (default, configurable) using asyncio.

#### Scenario: Client connects
- **WHEN** a TCP client connects on port 12345
- **THEN** a new coroutine handles the connection

### Requirement: Process ESC/VP21 commands from serial stream
The serial transport SHALL read newline-terminated (`\r`) command strings from the socket, pass them to the ESC/VP21 engine, and write the response back.

#### Scenario: GET command via serial
- **WHEN** a client sends `PWR?\r`
- **THEN** the transport reads the line, calls the engine, and sends the response

#### Scenario: Multiple sequential commands
- **WHEN** a client sends multiple commands in sequence
- **THEN** each is processed in order and responses are returned

#### Scenario: Client disconnects
- **WHEN** the TCP client closes the connection
- **THEN** the transport coroutine exits cleanly without crashing the server

### Requirement: Support multiple concurrent serial clients
The serial transport SHALL handle multiple concurrent TCP connections, each processed independently.

#### Scenario: Two simultaneous serial clients
- **WHEN** two clients connect simultaneously
- **THEN** both receive correct independent responses
