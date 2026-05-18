## MODIFIED Requirements

### Requirement: HTTP Digest authentication challenge
When the emulator is started with the `--http-password` flag, the HTTP transport SHALL challenge unauthenticated requests with HTTP Digest authentication. Requests to all HTTP endpoints without a valid `Authorization` header SHALL receive a `401 Unauthorized` response containing a `WWW-Authenticate` header with `realm="Web Control"`, a randomly generated nonce, and `qop="auth"`. No `algorithm` field SHALL be emitted (defaults to MD5 per RFC 2617).

The password used for authentication SHALL default to the hardcoded value `"httppassword"` when `--http-password` is provided. The password SHALL be mutable at runtime; when it is changed, all subsequent requests SHALL be verified against the new password without requiring a restart. `HA1` SHALL be recomputed on every request rather than cached at middleware creation time.

#### Scenario: Unauthenticated request when password is configured
- **WHEN** the emulator is started with `--http-password` (boolean flag, no value) and an HTTP request arrives with no `Authorization` header
- **THEN** the server returns HTTP 401 with header `WWW-Authenticate: Digest realm="Web Control", nonce="<random>", qop="auth"`

#### Scenario: Invalid credentials
- **WHEN** an HTTP request arrives with an `Authorization: Digest` header whose `response` hash does not match the expected MD5 digest
- **THEN** the server returns HTTP 401

#### Scenario: Valid credentials with default password
- **WHEN** an HTTP request arrives with a correctly computed `Authorization: Digest` header (username `EPSONWEB`, realm `Web Control`, password `httppassword`)
- **THEN** the server processes the request normally and returns the appropriate 2xx response

#### Scenario: No password flag — no auth required
- **WHEN** the emulator is started without `--http-password`
- **THEN** all HTTP endpoints accept requests without any `Authorization` header

#### Scenario: Authentication succeeds after runtime password change
- **WHEN** the runtime password has been changed from `"httppassword"` to a new value AND a client sends a correctly computed Digest response using the new password
- **THEN** the server accepts the request

#### Scenario: Authentication fails after runtime password change with old password
- **WHEN** the runtime password has been changed AND a client sends a Digest response computed with the old password
- **THEN** the server returns HTTP 401

## ADDED Requirements

### Requirement: HTTP Digest password mutable at runtime
The HTTP transport SHALL recompute `HA1 = MD5("EPSONWEB:Web Control:<password>")` on every incoming authenticated request using the current password value so that password changes take effect immediately without a server restart.

#### Scenario: Middleware reads current password per-request
- **WHEN** the password is changed at runtime and a new request arrives
- **THEN** the new `HA1` is used for verification of that request and all subsequent requests
