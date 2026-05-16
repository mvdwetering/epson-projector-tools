## ADDED Requirements

### Requirement: Listen on ESC/VP.net port
The ESC/VP.net transport SHALL listen for TCP connections on port 3629 (default, configurable) using asyncio.

#### Scenario: Client connects on port 3629
- **WHEN** a TCP client connects on port 3629
- **THEN** a new coroutine handles the ESC/VP.net handshake

### Requirement: Respond to HELLO packet
The transport SHALL respond to a 16-byte HELLO packet (type `0x01`) with a 16-byte HELLO response.

#### Scenario: HELLO exchange
- **WHEN** client sends a valid HELLO packet with header `ESC/VP.net`, version `0x10`, type `0x01`
- **THEN** transport responds with a HELLO response with type `0x01`, status `0x20` (OK), 0 headers

### Requirement: Complete CONNECT handshake
The transport SHALL respond to a CONNECT packet (type `0x03`) with a CONNECT response and then switch the connection to raw ESC/VP21 mode.

#### Scenario: Successful CONNECT (no password)
- **WHEN** client sends a CONNECT packet with type `0x03`, status `0x00`, 0 headers
- **THEN** transport responds with type `0x03`, status `0x20`, 0 headers and enters ESC/VP21 pipe mode

#### Scenario: Invalid packet header
- **WHEN** received data does not begin with `ESC/VP.net` (bytes 0–9)
- **THEN** transport closes the connection

### Requirement: ESC/VP21 pipe after handshake
After a successful CONNECT, the transport SHALL process incoming data identically to the serial transport: read `\r`-terminated commands, call the engine, send responses.

#### Scenario: GET command after handshake
- **WHEN** a connected ESC/VP.net client sends `PWR?\r`
- **THEN** response is `PWR=01\r:` (or current value)

#### Scenario: Client disconnects after handshake
- **WHEN** the TCP client closes the connection after handshake
- **THEN** the transport coroutine exits cleanly

### Requirement: Hardcoded protocol constants
The ESC/VP.net handshake constants SHALL be hardcoded: magic `"ESC/VP.net"`, version `0x10`, command-type `0x21` (ESC/VP21 Ver1.0). These SHALL NOT be model-configurable.

#### Scenario: Constants not in YAML
- **WHEN** any model file is loaded
- **THEN** the vpnet transport uses its own hardcoded constants regardless of model data
