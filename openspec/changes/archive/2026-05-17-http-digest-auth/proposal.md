## Why

Newer Epson projectors protect their HTTP control interface with HTTP Digest authentication. Without emulating this, clients that use `DigestAuthMiddleware` (e.g. aiohttp-based controllers) cannot interact with the emulator. Adding optional Digest auth makes the emulator a faithful stand-in for real hardware.

## What Changes

- Add `--http-password` CLI argument to `main.py`; when omitted, HTTP transport remains unauthenticated (no behaviour change for existing users)
- Add a Digest authentication middleware to `HttpTransport` that is only activated when a password is supplied
- All HTTP endpoints (`/cgi-bin/json_query`, `/cgi-bin/directsend`) are protected by the middleware when active

## Capabilities

### New Capabilities
- `http-digest-auth`: HTTP Digest authentication middleware for the HTTP transport; challenges unauthenticated requests with `WWW-Authenticate: Digest realm="Web Control"` and verifies responses using MD5

### Modified Capabilities
- `http-transport`: New optional `password` constructor parameter; behaviour unchanged when password is absent

## Impact

- `main.py`: new `--http-password` argument passed to `HttpTransport`
- `transports/http.py`: new middleware function; `HttpTransport.__init__` gains `password: str | None = None`
- No new dependencies (uses `hashlib` and `secrets` from stdlib)
- No breaking changes; existing callers without a password see identical behaviour
