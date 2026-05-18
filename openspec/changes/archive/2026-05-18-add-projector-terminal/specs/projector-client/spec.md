## ADDED Requirements

### Requirement: Abstract client interface
The system SHALL provide an abstract base class `AbstractProjectorClient` with the following async interface: `connect()`, `disconnect()`, `send(cmd: str) -> tuple[str, float]` (returns ESC/VP21-formatted response and duration in milliseconds), and a `connected: bool` property.

#### Scenario: Send returns response and duration
- **WHEN** `send("SNO?")` is called on a connected client
- **THEN** it returns a tuple of `("SNO=<value>\r:", <ms>)` where `<ms>` is the elapsed time between sending and receiving the complete response

#### Scenario: Send on disconnected client raises
- **WHEN** `send()` is called on a client whose `connected` is `False`
- **THEN** it raises `ClientNotConnectedError`

---

### Requirement: Serial TCP client
The system SHALL provide a `SerialClient` that connects to a raw TCP endpoint, sends `CMD\r`-terminated commands, and reads the response until `:` is received.

#### Scenario: Connect and send
- **WHEN** `connect()` is called with a reachable host and port
- **THEN** `connected` becomes `True` and subsequent `send()` calls succeed

#### Scenario: Response termination
- **WHEN** a command is sent and the server responds with `SNO=LPKB3G001K\r:`
- **THEN** `send()` returns `"SNO=LPKB3G001K\r:"` with duration in ms

---

### Requirement: ESC/VP.net client
The system SHALL provide a `VpnetClient` that performs the HELLO/CONNECT binary handshake before entering the ESC/VP21 command pipe.

#### Scenario: Handshake on connect
- **WHEN** `connect()` is called
- **THEN** the HELLO packet is sent and a valid HELLO response is received, followed by the CONNECT packet and CONNECT response, before `connected` becomes `True`

#### Scenario: Handshake failure
- **WHEN** the server responds with a non-OK status during handshake
- **THEN** `connect()` raises `ConnectionError` and `connected` remains `False`

---

### Requirement: HTTP client
The system SHALL provide an `HttpClient` that sends ESC/VP21 GET commands to `/cgi-bin/json_query` and SET commands to `/cgi-bin/directsend`, using HTTP Digest authentication.

#### Scenario: GET command routing
- **WHEN** `send("PWR?")` is called
- **THEN** the client sends `GET /cgi-bin/json_query?jsoncallback=PWR?&_=<timestamp>` with `Referer` and Digest auth headers, and returns the ESC/VP21-formatted response

#### Scenario: SET command routing
- **WHEN** `send("PWR 01")` is called
- **THEN** the client sends `GET /cgi-bin/directsend?PWR=01&_=<timestamp>` with `Referer` and Digest auth headers, and returns `"\r:"` on HTTP 200

#### Scenario: JSON response parsing
- **WHEN** the server returns `{"projector": {"feature": {"reply": "04", "error": false}}}`
- **THEN** `send("PWR?")` returns `"PWR=04\r:"`

#### Scenario: JSON error response
- **WHEN** the server returns `{"projector": {"feature": {"reply": "ERR", "error": true}}}`
- **THEN** `send()` returns `"ERR\r:"`

#### Scenario: HTTP is always "connected"
- **WHEN** `connected` is queried on an `HttpClient`
- **THEN** it always returns `True` (HTTP is stateless; connection state is not tracked)

---

### Requirement: Auto-reconnect for stateful clients
Serial and ESC/VP.net clients SHALL automatically attempt to reconnect after a connection loss using exponential backoff: 1 s, 2 s, 4 s, 8 s, 16 s, 30 s (cap). The client SHALL notify registered state-change callbacks.

#### Scenario: Connection loss triggers reconnect
- **WHEN** the TCP connection is lost (EOF or OS error) during an active session
- **THEN** `connected` becomes `False`, the state callback is invoked with `("reconnecting", attempt=1, next_retry_s=1)`, and the client begins reconnect attempts

#### Scenario: Successful reconnect
- **WHEN** a reconnect attempt succeeds
- **THEN** `connected` becomes `True` and the state callback is invoked with `("connected", attempt=0, next_retry_s=0)`

#### Scenario: Commands during reconnect are rejected
- **WHEN** `send()` is called while `connected` is `False`
- **THEN** `ClientNotConnectedError` is raised immediately (commands are not queued)

#### Scenario: Backoff cap
- **WHEN** 6 or more consecutive reconnect attempts have failed
- **THEN** the retry interval is capped at 30 s and does not grow further

---

### Requirement: Connection state callback
Clients SHALL accept a `on_state_change` callback `(state: str, attempt: int, next_retry_s: int) -> None`. `state` is one of `"connected"`, `"disconnected"`, `"reconnecting"`.

#### Scenario: Callback on connect
- **WHEN** `connect()` succeeds
- **THEN** the callback is invoked with `("connected", 0, 0)`

#### Scenario: Callback on disconnect
- **WHEN** `disconnect()` is called explicitly
- **THEN** the callback is invoked with `("disconnected", 0, 0)`
