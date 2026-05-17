## ADDED Requirements

### Requirement: HTTP Digest authentication challenge
When the emulator is started with a password, the HTTP transport SHALL challenge unauthenticated requests with HTTP Digest authentication. Requests to all HTTP endpoints without a valid `Authorization` header SHALL receive a `401 Unauthorized` response containing a `WWW-Authenticate` header with `realm="Web Control"`, a randomly generated nonce, and `qop="auth"`. No `algorithm` field SHALL be emitted (defaults to MD5 per RFC 2617).

#### Scenario: Unauthenticated request when password is configured
- **WHEN** the emulator is started with `--http-password` and an HTTP request arrives with no `Authorization` header
- **THEN** the server returns HTTP 401 with header `WWW-Authenticate: Digest realm="Web Control", nonce="<random>", qop="auth"`

#### Scenario: Invalid credentials
- **WHEN** an HTTP request arrives with an `Authorization: Digest` header whose `response` hash does not match the expected MD5 digest
- **THEN** the server returns HTTP 401

#### Scenario: Valid credentials
- **WHEN** an HTTP request arrives with a correctly computed `Authorization: Digest` header (username `EPSONWEB`, realm `Web Control`, correct password)
- **THEN** the server processes the request normally and returns the appropriate 2xx response

#### Scenario: No password configured — no auth required
- **WHEN** the emulator is started without `--http-password`
- **THEN** all HTTP endpoints accept requests without any `Authorization` header

### Requirement: Digest authentication parameters
The Digest authentication SHALL use the following fixed parameters matching the real Epson projector protocol:
- **Realm**: `"Web Control"`
- **Username**: `"EPSONWEB"` (expected from client; only this username is accepted)
- **Algorithm**: MD5 (RFC 2617 default; field omitted from `WWW-Authenticate`)
- **qop**: `"auth"`

HA1 SHALL be computed as `MD5("EPSONWEB:Web Control:<password>")` once at startup. Per-request verification SHALL compute `HA2 = MD5("<method>:<request-uri>")` and `response = MD5("<HA1>:<nonce>:<nc>:<cnonce>:auth:<HA2>")`.

#### Scenario: Correct HA1/HA2/response computation
- **WHEN** a client sends `Authorization: Digest username="EPSONWEB", realm="Web Control", nonce="<n>", nc=<nc>, cnonce="<c>", qop=auth, response="<r>"`
- **THEN** the server accepts the request if and only if `MD5(MD5("EPSONWEB:Web Control:<password>"):<n>:<nc>:<c>:auth:MD5("GET:<uri>"))` equals `<r>`

### Requirement: Nonce lifecycle
A fresh random nonce SHALL be generated for each `401` challenge. The nonce SHALL be stored in the middleware for verification of the subsequent authenticated request. Nonce-count (`nc`) validation SHALL NOT be performed — any `nc` value from the client is accepted.

#### Scenario: Nonce is random per challenge
- **WHEN** two separate unauthenticated requests trigger two separate 401 responses
- **THEN** each 401 response contains a different `nonce` value

#### Scenario: Client reuses nonce across multiple requests
- **WHEN** an authenticated client sends successive requests with the same nonce and incrementing `nc`
- **THEN** each request is accepted without re-challenging
