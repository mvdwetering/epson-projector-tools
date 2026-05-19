## Why

The ESC/VP.net transport currently accepts all connections without authentication. Real Epson projectors support an optional plaintext password in the CONNECT handshake. Without emulating this, controllers that supply a password (and clients using `VpnetClient` against a password-protected projector) cannot establish a session.

## What Changes

- Replace `--http-password` boolean CLI flag with a single `--password` flag that enables authentication on **all** network transports (ESC/VP.net and HTTP) simultaneously; existing `--http-password` flag is **REMOVED** (**BREAKING**)
- `VpnetTransport` parses the Password header from the CONNECT packet and enforces it when a password is configured; returns `0x41` (Unauthorized) or `0x43` (Forbidden) on failure
- `VpnetClient` accepts an optional `password` parameter and includes the Password header in CONNECT when set
- `VpnetTransport` and `HttpTransport` share the same `PasswordStore` instance so the emulator TUI `w` keybinding changes the password for both transports simultaneously
- Terminal TUI connection form shows the password field for `vpnet` protocol (currently hidden; only visible for `http`)

## Capabilities

### New Capabilities
- `vpnet-password-auth`: ESC/VP.net password authentication in the CONNECT handshake — server-side enforcement (`VpnetTransport`) and client-side transmission (`VpnetClient`); default password `"emulatorpassword"` when auth is enabled

### Modified Capabilities
- `terminal-tui`: Password input field is shown for both `vpnet` and `http` protocols; label updated accordingly

## Impact

- `main.py`: `--http-password` replaced by `--password` (**BREAKING**); `PasswordStore("emulatorpassword")` is created when `--password` is passed; shared instance passed to both `HttpTransport` and `VpnetTransport`
- `transports/vpnet.py`: `VpnetTransport.__init__` gains `password_store: PasswordStore | None = None`; `_handshake()` reads and validates Password header from CONNECT; `_skip_extra_headers` replaced by a header-parsing helper for CONNECT
- `client/vpnet.py`: `VpnetClient.__init__` gains `password: str = ""`; `_handshake()` includes Password header in CONNECT when password is non-empty; raises descriptive errors on `0x41`/`0x43`
- `terminal.py`: `_build_client()` passes `password` argument to `VpnetClient`
- `ui/terminal_app.py`: `_update_password_visibility()` updated to show password field for `vpnet`; label text updated
- No new dependencies
- **BREAKING**: `--http-password` flag removed; use `--password` instead
