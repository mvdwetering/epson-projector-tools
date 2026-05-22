## ADDED Requirements

### Requirement: Display runtime transport configuration
The TUI SHALL display a dedicated configuration panel that shows the emulator's current transport configuration for the active process.

#### Scenario: Configuration panel visible at startup
- **WHEN** the emulator TUI is launched
- **THEN** a configuration panel is visible without requiring user interaction

### Requirement: Display configured transport ports
The configuration panel SHALL show the configured listening port for each transport: Serial TCP, ESC/VP.net, and HTTP.

#### Scenario: Panel shows startup ports
- **WHEN** the emulator is started with explicit port arguments
- **THEN** the panel displays those exact serial, ESC/VP.net, and HTTP port values

#### Scenario: Panel shows default ports
- **WHEN** the emulator is started without overriding transport ports
- **THEN** the panel displays the default serial, ESC/VP.net, and HTTP port values used by the process

### Requirement: Display password-required status
The configuration panel SHALL show whether password authentication is required for transports that support password protection, without revealing password values.

#### Scenario: HTTP auth required
- **WHEN** the emulator is started with HTTP password authentication configured
- **THEN** the panel shows HTTP authentication as required

#### Scenario: HTTP auth not required
- **WHEN** the emulator is started without HTTP password authentication configured
- **THEN** the panel shows HTTP authentication as not required

#### Scenario: Password value never shown
- **WHEN** authentication is configured for any transport
- **THEN** the configuration panel does not display plaintext or masked password content
