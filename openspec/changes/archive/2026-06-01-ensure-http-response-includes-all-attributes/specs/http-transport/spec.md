## MODIFIED Requirements

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
