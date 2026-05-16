## ADDED Requirements

### Requirement: HTTP server placeholder
The HTTP transport SHALL start an HTTP server on port 8080 (default, configurable) that accepts connections but returns a stub response for all requests.

#### Scenario: GET any path
- **WHEN** an HTTP GET request is made to any path
- **THEN** the server returns HTTP 200 with body `HTTP transport not yet implemented`

### Requirement: HTTP server uses asyncio
The HTTP server SHALL be implemented using `aiohttp` to facilitate future expansion.

#### Scenario: Server starts with other transports
- **WHEN** the emulator starts
- **THEN** the HTTP server starts alongside serial and ESC/VP.net transports without blocking them
