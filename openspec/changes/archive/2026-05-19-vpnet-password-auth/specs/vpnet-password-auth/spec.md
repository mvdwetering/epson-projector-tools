## ADDED Requirements

### Requirement: Server enforces password on CONNECT
When a password is configured, `VpnetTransport` SHALL reject CONNECT requests that do not supply the correct password.

#### Scenario: CONNECT without password when password is configured
- **WHEN** the server has a password configured and the client sends a CONNECT packet with 0 headers
- **THEN** the server responds with CONNECT status `0x41` (Unauthorized) and closes the TCP connection

#### Scenario: CONNECT with wrong password
- **WHEN** the server has a password configured and the client sends a CONNECT packet with a Password header containing an incorrect value
- **THEN** the server responds with CONNECT status `0x43` (Forbidden) and closes the TCP connection

#### Scenario: CONNECT with correct password
- **WHEN** the server has a password configured and the client sends a CONNECT packet with a Password header containing the correct value
- **THEN** the server responds with CONNECT status `0x20` (OK) and enters ESC/VP21 pipe mode

#### Scenario: CONNECT when no password is configured
- **WHEN** the server has no password configured and the client sends a CONNECT packet with 0 headers
- **THEN** the server responds with CONNECT status `0x20` (OK) and enters ESC/VP21 pipe mode

#### Scenario: CONNECT with password header when no password is configured
- **WHEN** the server has no password configured and the client sends a CONNECT packet with a Password header
- **THEN** the server responds with CONNECT status `0x20` (OK) and enters ESC/VP21 pipe mode

---

### Requirement: Client sends password header when password is configured
`VpnetClient` SHALL include the Password header in the CONNECT packet when a password is provided.

#### Scenario: CONNECT with password
- **WHEN** `VpnetClient` is constructed with a non-empty `password` string and connects to a server
- **THEN** the CONNECT packet includes exactly one extra header with identifier `0x01` (Password), attribute `0x01` (Plain), and the password null-padded to 16 bytes

#### Scenario: CONNECT without password
- **WHEN** `VpnetClient` is constructed with an empty `password` string and connects to a server
- **THEN** the CONNECT packet has 0 extra headers

---

### Requirement: Client raises descriptive error on auth failure
`VpnetClient` SHALL raise a `ConnectionError` with a descriptive message when the server rejects the CONNECT with `0x41` or `0x43`.

#### Scenario: Server returns 0x41 (Unauthorized)
- **WHEN** the server responds to CONNECT with status `0x41`
- **THEN** `VpnetClient._handshake()` raises `ConnectionError` with a message indicating the projector requires a password

#### Scenario: Server returns 0x43 (Forbidden)
- **WHEN** the server responds to CONNECT with status `0x43`
- **THEN** `VpnetClient._handshake()` raises `ConnectionError` with a message indicating the password is incorrect

---

### Requirement: Emulator CLI flag for network password
`main.py` SHALL accept a `--password` boolean flag (replacing `--http-password`) that enables password authentication on both the ESC/VP.net and HTTP transports with the default password `"emulatorpassword"`.

#### Scenario: Flag not supplied
- **WHEN** `main.py` is run without `--password`
- **THEN** both ESC/VP.net and HTTP transports accept all requests without authentication

#### Scenario: Flag supplied
- **WHEN** `main.py` is run with `--password`
- **THEN** both the ESC/VP.net transport and the HTTP transport enforce the password `"emulatorpassword"` (changeable at runtime via TUI `w` keybinding)

#### Scenario: Legacy --http-password flag removed
- **WHEN** `main.py` is run with `--http-password`
- **THEN** argparse reports an unrecognised argument error

---

### Requirement: Shared password store between HTTP and ESC/VP.net
When `--password` is active, both transports SHALL use the same `PasswordStore` instance so that the TUI `w` keybinding changes both simultaneously.

#### Scenario: Flag supplied
- **WHEN** `main.py` is run with `--password`
- **THEN** one `PasswordStore` is created and passed to both `HttpTransport` and `VpnetTransport`; pressing `w` in the TUI updates the password for both

#### Scenario: Flag not supplied
- **WHEN** `main.py` is run without `--password`
- **THEN** no `PasswordStore` is created; both `HttpTransport` and `VpnetTransport` receive `None`
