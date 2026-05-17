## MODIFIED Requirements

### Requirement: HTTP server placeholder
The HTTP transport SHALL start an HTTP server on port 8080 (default, configurable) that accepts connections. It SHALL route requests to `/cgi-bin/json_query` and `/cgi-bin/directsend`. All other paths SHALL return HTTP 404. When a password is configured, all routes SHALL be protected by Digest authentication middleware.

#### Scenario: GET any unknown path
- **WHEN** an HTTP GET request is made to any path other than the two CGI endpoints
- **THEN** the server returns HTTP 404

#### Scenario: Server starts with other transports
- **WHEN** the emulator starts
- **THEN** the HTTP server starts alongside serial and ESC/VP.net transports without blocking them

#### Scenario: Server starts with password — middleware active
- **WHEN** the emulator is started with `--http-password`
- **THEN** the HTTP server applies Digest auth middleware to all routes

#### Scenario: Server starts without password — no middleware
- **WHEN** the emulator is started without `--http-password`
- **THEN** the HTTP server starts with no authentication middleware (current behaviour)
