## ADDED Requirements

### Requirement: Disconnect idle VP.net sessions
The emulator SHALL close an established ESC/VP.net TCP session when no inbound ESC/VP21 command activity is received for 600 seconds.

#### Scenario: Idle timeout disconnects session
- **WHEN** a client completes CONNECT successfully and then sends no command data for 600 seconds
- **THEN** the emulator closes that TCP session

### Requirement: Inbound activity resets idle timer
The emulator SHALL reset the VP.net inactivity timer whenever it receives inbound ESC/VP21 command data from the connected client.

#### Scenario: Periodic commands keep session alive
- **WHEN** a connected client sends valid ESC/VP21 command data at intervals shorter than 600 seconds
- **THEN** the emulator keeps the TCP session open
