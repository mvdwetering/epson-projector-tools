## ADDED Requirements

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

### Requirement: json_query endpoint
The HTTP transport SHALL implement `GET /cgi-bin/json_query`. The `jsoncallback` query parameter SHALL be treated as an ESC/VP21 GET command string (e.g. `PWR?`). The response SHALL be JSON in the format `{"projector": {"feature": {"name": "esc/vp21", "query": "<command>", "reply": "<value-or-ERR>", "error": <boolean>}}}`.

#### Scenario: Successful query
- **WHEN** `GET /cgi-bin/json_query?jsoncallback=PWR?` is received
- **THEN** the server returns HTTP 200 with `projector.feature.name="esc/vp21"`, `query="PWR?"`, `reply="<current-pwr-value>"`, and `error=false`

#### Scenario: ESC/VP21 command error
- **WHEN** `GET /cgi-bin/json_query?jsoncallback=PWR` is received (missing `?`)
- **THEN** the response JSON includes `projector.feature.name="esc/vp21"`, `query="PWR"`, `reply="ERR"`, and `error=true`

#### Scenario: Missing jsoncallback parameter
- **WHEN** no `jsoncallback` parameter is present
- **THEN** the server returns HTTP 400

### Requirement: directsend SET endpoint
The HTTP transport SHALL implement `GET /cgi-bin/directsend` for ESC/VP21 SET commands. The first query parameter SHALL be treated as `CMD=VALUE`, translated to `handle_command(state, model, "CMD VALUE")`. On success the server SHALL return HTTP 200.

#### Scenario: Successful SET
- **WHEN** `GET /cgi-bin/directsend?CMODE=15` is received
- **THEN** the engine processes `CMODE 15` and the server returns HTTP 200

#### Scenario: Failed SET
- **WHEN** the engine returns an error for the command
- **THEN** the server raises an exception resulting in HTTP 400 or 500

### Requirement: HTTP transport uses asyncio
The HTTP server SHALL be implemented using `aiohttp` and SHALL not block the asyncio event loop.

#### Scenario: Server starts with other transports
- **WHEN** the emulator starts
- **THEN** the HTTP server starts alongside serial and ESC/VP.net transports without blocking them
