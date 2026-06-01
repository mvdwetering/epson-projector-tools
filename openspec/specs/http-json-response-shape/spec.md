## ADDED Requirements

### Requirement: json_query response includes complete Epson feature attributes
The HTTP transport SHALL return `GET /cgi-bin/json_query` responses with a complete Epson-style feature object for both success and error outcomes. The response JSON SHALL include `projector.feature.name`, `projector.feature.query`, `projector.feature.reply`, and `projector.feature.error` in every case.

#### Scenario: Successful query includes all attributes
- **WHEN** `GET /cgi-bin/json_query?jsoncallback=PWR?` is processed successfully
- **THEN** HTTP 200 response JSON includes `projector.feature.name="esc/vp21"`, `query="PWR?"`, `reply="<value>"`, and `error=false`

#### Scenario: Malformed query includes all attributes
- **WHEN** `GET /cgi-bin/json_query?jsoncallback=PWR` is processed as an ESC/VP21 error
- **THEN** response JSON includes `projector.feature.name="esc/vp21"`, `query="PWR"`, `reply="ERR"`, and `error=true`

#### Scenario: Error path never drops required attributes
- **WHEN** any `json_query` request results in an error response body
- **THEN** the response body still contains all required feature attributes (`name`, `query`, `reply`, `error`)
