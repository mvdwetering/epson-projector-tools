## Why

The HTTP emulator responses are currently inconsistent in shape, and some responses omit expected fields. This breaks compatibility with clients that parse Epson-style JSON responses with a fixed attribute set.

## What Changes

- Define and enforce a canonical JSON response schema for `json_query` replies in both success and error cases.
- Ensure every `json_query` response always includes `name`, `query`, `reply`, and `error` under `projector.feature`.
- Preserve existing response semantics (`reply` values and `error` boolean meaning) while making payload structure stable.
- Add automated tests that assert full attribute presence for both valid queries and malformed/error queries.

## Capabilities

### New Capabilities
- `http-json-response-shape`: Enforce a stable Epson-compatible JSON field set for HTTP `json_query` responses across success and error outcomes.

### Modified Capabilities
- `http-transport`: Tighten response-format requirements for `json_query` so all required fields are always present.

## Impact

- Affected code: HTTP transport response-building logic in [transports/http.py](transports/http.py).
- Affected behavior: HTTP JSON responses become structurally consistent across code paths.
- Affected tests: HTTP transport tests to validate complete response attributes for success and error cases.
- External impact: Improved compatibility for clients expecting a fixed Epson-like JSON object schema.
