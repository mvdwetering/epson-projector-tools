## Why

Passing the HTTP password as a plain CLI argument (`--http-password <value>`) exposes it in the process list (`ps aux`) and shell history, which is a security concern even for a development emulator. Replacing it with a hardcoded default password and a boolean enable-flag removes the sensitive value from the command line entirely.

## What Changes

- `--http-password` argument changes from a string value to a boolean flag: presence enables Digest authentication; absence disables it.
- The HTTP Digest password defaults to the hardcoded value `"httppassword"` when authentication is enabled.
- The password can be changed at runtime via a TUI keypress without restarting the emulator.
- `HttpTransport` holds the current password in a mutable reference so it can be updated live.

## Capabilities

### New Capabilities
<!-- None: all features are modifications to existing capabilities -->

### Modified Capabilities
- `http-digest-auth`: Password is no longer read from a CLI string argument. `--http-password` (no value) enables authentication with the default password `"httppassword"`. The password must be updatable at runtime.
- `tui`: Adds a key binding (e.g. `w`) that opens an inline input prompt allowing the operator to change the HTTP Digest password at runtime without restarting the emulator.

## Impact

- `main.py`: `--http-password` argparse argument changes from `type=str, default=None` to `action="store_true"`.
- `transports/http.py`: `HttpTransport` replaces the immutable `password: str | None` constructor argument with a mutable password store; digest middleware reads the current password on each request rather than capturing it at startup.
- `ui/app.py`: Receives a reference to the mutable password store; adds key binding and input widget for runtime password change.
