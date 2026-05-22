## Why

Operators can see live projector state and command traffic, but they cannot verify runtime emulator configuration from the UI itself. During setup and troubleshooting this makes it harder to confirm which transport ports are active and whether password protection is enabled.

## What Changes

- Add a configuration panel in the emulator TUI that shows current transport settings.
- Display configured ports for serial TCP, ESC/VP.net, and HTTP transports.
- Display whether password authentication is required for protected transports.
- Keep configuration values consistent with emulator startup/runtime settings so operators can trust the UI as the source of truth.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `tui`: Extend requirements to display current emulator configuration, including transport ports and password-required status.

## Impact

- Affected specs: `openspec/specs/tui/spec.md` (delta required).
- Affected code: `main.py`, `ui/app.py`, and related UI data flow for startup configuration.
- No protocol wire-format changes expected; this is a UI visibility enhancement.
